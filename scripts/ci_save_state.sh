#!/usr/bin/env bash
# Commit and push what the us-rewards job has recorded so far.
#
#     bash scripts/ci_save_state.sh "<commit message>"
#
# The job runs for five hours and used to commit once, at its end. On
# 11 November 2026 the machine it ran on was lost after two hours and
# everything it had recorded went with it. This is called during a run as
# well as at its end, so that at most an hour can be lost.
#
# It works in a second checkout of the branch. The programs that are still
# recording write in the first one and are never touched: no file of theirs
# is moved, stashed or rewritten. Only files the job itself has written are
# copied across, so a file somebody else has changed on the branch meanwhile
# (the scoring scripts write settlements.csv beside these) is left as it is.
#
# It never fails the job: if a push does not go through, the next call
# carries the same files again.
set -uo pipefail

msg="${1:?a commit message is needed}"
branch="${GITHUB_REF_NAME:-$(git rev-parse --abbrev-ref HEAD)}"
snap="${SNAP_DIR:-$(cd .. && pwd)/kht-save}"
dirs=(state/us-rewards state/us-quoter state/us-lasttick)

# one save at a time: an hourly save still running must not meet the one at the end of the run
exec 9>"$snap.lock"
flock -w 600 9 || { echo "save: another save is still running"; exit 0; }

# what this job has written since it checked the branch out
mapfile -t changed < <(git status --porcelain --untracked-files=all -- "${dirs[@]}" 2>/dev/null | awk '{print $NF}')
if [ "${#changed[@]}" -eq 0 ]; then
  echo "save: nothing recorded yet"
  exit 0
fi

if [ ! -e "$snap/.git" ]; then
  git worktree add -q --detach "$snap" HEAD || { echo "save: could not make a second checkout"; exit 0; }
fi

for attempt in 1 2 3 4; do
  # the branch as it is now, then the recorded files laid over it
  if ! git -C "$snap" fetch -q origin "$branch"; then
    echo "save: could not reach the repository (attempt $attempt)"; sleep $((attempt * 5)); continue
  fi
  git -C "$snap" checkout -q --detach FETCH_HEAD
  git -C "$snap" reset -q --hard FETCH_HEAD
  for f in "${changed[@]}"; do
    [ -f "$f" ] || continue
    mkdir -p "$snap/$(dirname "$f")"
    cp -p "$f" "$snap/$f.partial" 2>/dev/null && mv -f "$snap/$f.partial" "$snap/$f"
  done
  for d in "${dirs[@]}"; do                       # one at a time: git adds nothing at all if any one path is missing
    if [ -e "$snap/$d" ]; then git -C "$snap" add -- "$d"; fi
  done
  if git -C "$snap" diff --cached --quiet; then
    echo "save: nothing new since the last save"
    exit 0
  fi
  git -C "$snap" -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" commit -q -m "$msg"
  if git -C "$snap" push -q origin "HEAD:refs/heads/$branch"; then
    echo "save: pushed ${#changed[@]} files"
    exit 0
  fi
  echo "save: the branch moved while saving (attempt $attempt)"
  sleep $((attempt * 5))
done
echo "save: gave up for now; the next save carries the same files"
exit 0
