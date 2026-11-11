"""The script that pushes what the recording job has written so far (scripts/ci_save_state.sh)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ci_save_state.sh"
pytestmark = pytest.mark.skipif(shutil.which("git") is None or shutil.which("flock") is None, reason="needs git and flock")


def git(cwd, *args):
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, text=True).stdout


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def repos(tmp_path):
    """A branch on a stand-in server, the job's shallow checkout of it, and somebody else's clone."""
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", str(origin))
    seed = tmp_path / "seed"
    git(tmp_path, "clone", "-q", str(origin), str(seed))
    git(seed, "checkout", "-q", "-b", "work")
    write(seed / "state/us-rewards/log.csv", "run,started\nr0,1\n")
    write(seed / "state/us-rewards/settlements.csv", "slug,settle\na,1.0\n")
    write(seed / "docs/notes.md", "notes\n")
    git(seed, "add", "-A")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "work")
    runner, other = tmp_path / "runner", tmp_path / "other"
    git(tmp_path, "clone", "-q", "--depth", "1", "--branch", "work", f"file://{origin}", str(runner))
    git(tmp_path, "clone", "-q", "--branch", "work", str(origin), str(other))
    return origin, runner, other, tmp_path


def save(runner, tmp_path, message):
    env = {**os.environ, "GITHUB_REF_NAME": "work", "SNAP_DIR": str(tmp_path / "kht-save")}
    r = subprocess.run(["bash", str(SCRIPT), message], cwd=runner, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr                               # it must never fail the job
    return r.stdout.strip().splitlines()[-1]


def on_branch(origin, tmp_path, name="check"):
    dest = tmp_path / name
    if dest.exists():
        shutil.rmtree(dest)
    git(tmp_path, "clone", "-q", "--branch", "work", str(origin), str(dest))
    return dest


def test_saves_what_the_job_wrote_and_nothing_else(repos):
    origin, runner, other, tmp_path = repos
    assert save(runner, tmp_path, "save 0") == "save: nothing recorded yet"
    # the job records
    write(runner / "state/us-rewards/runs/r1/games.csv.gz", "games v1\n")
    write(runner / "state/us-quoter/cycles.csv", "cycle 1\n")
    write(runner / "state/us-lasttick/runs/x/books.csv.gz", "books v1\n")
    write(runner / "state/us-ladder/runs/x/books.csv.gz", "ladder books v1\n")
    write(runner / "notes-of-the-job.txt", "not state\n")
    # meanwhile somebody else pushes a newer settlements file and a document
    write(other / "state/us-rewards/settlements.csv", "slug,settle\na,1.0\nb,0.0\n")
    write(other / "docs/notes.md", "notes\nmore\n")
    git(other, "commit", "-q", "-am", "scores")
    git(other, "push", "-q", "origin", "work")
    assert save(runner, tmp_path, "save 1") == "save: pushed 4 files"
    seen = on_branch(origin, tmp_path)
    assert (seen / "state/us-rewards/runs/r1/games.csv.gz").read_text() == "games v1\n"
    assert (seen / "state/us-lasttick/runs/x/books.csv.gz").read_text() == "books v1\n"
    assert (seen / "state/us-ladder/runs/x/books.csv.gz").read_text() == "ladder books v1\n"
    assert (seen / "state/us-rewards/settlements.csv").read_text().endswith("b,0.0\n")       # the other person's newer file is not put back
    assert (seen / "docs/notes.md").read_text() == "notes\nmore\n" and not (seen / "notes-of-the-job.txt").exists()
    # the job goes on; the files grow; the log gets its line at the end of the run
    write(runner / "state/us-rewards/runs/r1/games.csv.gz", "games v2\n")
    with (runner / "state/us-rewards/log.csv").open("a") as fh:
        fh.write("r1,2\n")
    assert save(runner, tmp_path, "save 2") == "save: pushed 5 files"
    assert save(runner, tmp_path, "save 3") == "save: nothing new since the last save"
    seen = on_branch(origin, tmp_path)
    assert (seen / "state/us-rewards/runs/r1/games.csv.gz").read_text() == "games v2\n"
    assert (seen / "state/us-rewards/log.csv").read_text() == "run,started\nr0,1\nr1,2\n"
    assert git(seen, "log", "--format=%s").split() == ["save", "2", "save", "1", "scores", "start"]
    # the checkout the programs write in was never touched
    assert git(runner, "log", "--format=%s").strip() == "start"
    assert "state/us-quoter/" in git(runner, "status", "--porcelain")


def test_a_save_survives_the_server_being_out_of_reach(repos):
    origin, runner, other, tmp_path = repos
    write(runner / "state/us-quoter/cycles.csv", "cycle 1\n")
    hidden = origin.with_name("hidden.git")
    origin.rename(hidden)                                             # the repository cannot be reached
    env = {**os.environ, "GITHUB_REF_NAME": "work", "SNAP_DIR": str(tmp_path / "kht-save")}
    script = SCRIPT.read_text().replace("sleep $((attempt * 5))", "sleep 0")
    quick = tmp_path / "quick.sh"
    quick.write_text(script)
    r = subprocess.run(["bash", str(quick), "save"], cwd=runner, env=env, capture_output=True, text=True)
    assert r.returncode == 0 and "gave up for now" in r.stdout
    hidden.rename(origin)
    assert save(runner, tmp_path, "save later") == "save: pushed 1 files"
    assert (on_branch(origin, tmp_path) / "state/us-quoter/cycles.csv").read_text() == "cycle 1\n"
