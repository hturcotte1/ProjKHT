"""The gate that decides whether a scheduled run should trade."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from kht.trading import schedule

NOW = datetime(2026, 11, 10, 12, 7, 30, tzinfo=timezone.utc)
SRC = Path(__file__).resolve().parents[1] / "src"


def _stamp(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "last_cycle_started"
    p.write_text(text)
    return p


def test_no_record_means_due(tmp_path):
    due, why = schedule.check(tmp_path / "missing", 170, NOW)
    assert due and "no record" in why


def test_recent_cycle_is_not_due_and_says_when(tmp_path):
    p = _stamp(tmp_path, "2026-11-10T10:47:05Z\n")
    due, why = schedule.check(p, 170, NOW)
    assert not due
    assert "80 minutes ago" in why
    assert "13:37 UTC" in why          # 10:47 + 170 minutes


def test_due_exactly_at_the_interval(tmp_path):
    p = _stamp(tmp_path, (NOW - timedelta(minutes=170)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert schedule.check(p, 170, NOW)[0]
    p = _stamp(tmp_path, (NOW - timedelta(minutes=169, seconds=59)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert not schedule.check(p, 170, NOW)[0]


def test_a_three_hour_pace_survives_a_few_minutes_of_jitter(tmp_path):
    # Slots are 15 minutes apart. A cycle that started 8 minutes late must not
    # push the next one a whole slot beyond three hours.
    started = datetime(2026, 11, 10, 9, 15, 0, tzinfo=timezone.utc)   # the 09:07 slot, late
    p = _stamp(tmp_path, started.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert not schedule.check(p, 170, datetime(2026, 11, 10, 11, 52, 20, tzinfo=timezone.utc))[0]
    assert schedule.check(p, 170, datetime(2026, 11, 10, 12, 7, 20, tzinfo=timezone.utc))[0]


def test_unusable_records_fail_towards_trading(tmp_path):
    for text in ["", "   \n", "yesterday", "1794297350", "2026-13-45T99:00:00Z"]:
        assert schedule.check(_stamp(tmp_path, text), 170, NOW)[0], text
    d = tmp_path / "a_directory"
    d.mkdir()
    assert schedule.check(d, 170, NOW)[0]
    b = tmp_path / "binary"
    b.write_bytes(b"\xff\xfe\x00\x81")
    assert schedule.check(b, 170, NOW)[0]


def test_a_record_in_the_future_is_ignored(tmp_path):
    p = _stamp(tmp_path, (NOW + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    due, why = schedule.check(p, 170, NOW)
    assert due and "future" in why


def test_times_without_a_zone_are_read_as_utc(tmp_path):
    p = _stamp(tmp_path, "2026-11-10T12:00:00")
    assert not schedule.check(p, 170, NOW)[0]
    p = _stamp(tmp_path, "2026-11-10T05:00:00-07:00")      # the same instant, written with an offset
    assert not schedule.check(p, 170, NOW)[0]


def test_mark_writes_what_read_understands(tmp_path):
    p = tmp_path / "state" / "last_cycle_started"          # parent does not exist yet
    schedule.mark(p, NOW)
    assert p.read_text() == "2026-11-10T12:07:30Z\n"
    assert schedule.read_stamp(p) == NOW


def test_main_marks_only_when_due(tmp_path, capsys):
    p = tmp_path / "last_cycle_started"

    assert schedule.main([str(p), "--min-minutes", "170", "--mark"]) == 0
    written = schedule.read_stamp(p)
    assert written is not None
    assert abs((datetime.now(timezone.utc) - written).total_seconds()) < 60
    assert capsys.readouterr().out.startswith("due")

    # Ten minutes after a cycle started, a scheduled run is not due and must
    # leave the record alone.
    earlier = (datetime.now(timezone.utc) - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ\n")
    p.write_text(earlier)
    assert schedule.main([str(p), "--min-minutes", "170", "--mark"]) == schedule.NOT_DUE
    assert p.read_text() == earlier
    assert capsys.readouterr().out.startswith("not due")

    # A manual run asks for no minimum, so it is always due and moves the record.
    p.write_text("2020-01-01T00:00:00Z\n")
    assert schedule.main([str(p), "--mark"]) == 0
    assert p.read_text() != "2020-01-01T00:00:00Z\n"


def test_without_mark_nothing_is_written(tmp_path):
    p = tmp_path / "last_cycle_started"
    assert schedule.main([str(p), "--min-minutes", "170"]) == 0
    assert not p.exists()


def test_runs_as_a_module_before_anything_is_installed(tmp_path):
    """The workflow calls it with the runner's own Python and only PYTHONPATH set."""
    p = tmp_path / "last_cycle_started"
    env = {"PYTHONPATH": str(SRC), "PATH": os.environ.get("PATH", "")}
    cmd = [sys.executable, "-S", "-m", "kht.trading.schedule", str(p), "--min-minutes", "170", "--mark"]

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("due")

    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert r.returncode == schedule.NOT_DUE, r.stderr
    assert r.stdout.startswith("not due")

    r = subprocess.run(cmd[:-3] + ["--min-minutes", "soon"], env=env, capture_output=True, text=True)
    assert r.returncode not in (0, schedule.NOT_DUE)        # a bad call is an error, not an answer
