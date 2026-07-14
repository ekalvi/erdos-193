#!/usr/bin/env python3
"""
Stamp the research-log timeline from git history.

Each EVENTS entry in progress.html gets a timestamp = author date of the
earliest commit whose diff introduced that event's title string (git log -S).
Writes/replaces the `const STAMPS = {...}` block between the STAMPS markers.
Rerun after appending events:  python3 viz/build_stamps.py && git add -A ...
In-progress items (kind 'live') are left unstamped by the renderer.
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

HTML = Path(__file__).parent / "progress.html"
src = HTML.read_text()

titles = re.findall(
    r"\[\s*'(?:ok|dead|sci|build|live)'\s*,\s*'[^']*'\s*,\s*'((?:[^'\\]|\\.)*)'",
    src,
)
# events backfilled when the page was created carry the page-creation commit
# time, not the event's real time — leave those unstamped (day header suffices)
page_birth = subprocess.run(
    ["git", "log", "--reverse", "--format=%aI", "--", "viz/progress.html"],
    capture_output=True, text=True, cwd=HTML.parent.parent,
).stdout.strip().splitlines()[0]
stamps = {}
for t in titles:
    plain = t.replace("\\'", "'")
    # a distinctive, rename-resistant probe: the longest word run in the title
    probe = plain
    out = subprocess.run(
        ["git", "log", "--reverse", "--format=%aI", "-S", probe, "--", "viz/progress.html"],
        capture_output=True, text=True, cwd=HTML.parent.parent,
    ).stdout.strip().splitlines()
    if out and out[0] == page_birth:
        continue
    if out:
        dt = datetime.fromisoformat(out[0])
        off = dt.utcoffset().total_seconds() / 3600
        tz = {-4.0: "EDT", -5.0: "EST"}.get(off, f"UTC{off:+.0f}")
        stamps[plain] = dt.strftime("%b %-d · %H:%M ") + tz
    else:
        print(f"  (no commit found for: {plain[:50]!r} — leaving unstamped)")

block = "const STAMPS = " + json.dumps(stamps, ensure_ascii=False, indent=0) + ";"
new = re.sub(
    r"// STAMPS-BEGIN.*?// STAMPS-END",
    "// STAMPS-BEGIN\n" + block + "\n// STAMPS-END",
    src,
    flags=re.S,
)
assert new != src or block in src, "STAMPS markers not found in progress.html"
HTML.write_text(new)
print(f"stamped {len(stamps)}/{len(titles)} events")
