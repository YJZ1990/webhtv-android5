#!/usr/bin/env python3
"""Normalise and repair unified diff files so `git apply` accepts them.

The nextlib patch series committed upstream is generated on a machine that
wrote CRLF line endings and, for at least one hunk, header line counts that do
not match the body. `git apply` rejects those as "corrupt patch", and GNU patch
rejects them as "malformed patch".

This script rewrites each patch as:

  * LF line endings only
  * exactly one trailing newline
  * every ``@@`` header recomputed from the lines actually present

It refuses to guess: if a hunk body contains a line that is not a valid diff
line (``+``, ``-``, space, empty or ``\\``), the patch is reported and copied
through unchanged so the caller fails loudly instead of applying something
half-correct.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")


def _is_boundary(line: str) -> bool:
    """True when a line starts a new hunk or a new file section."""
    return (
        line.startswith("@@")
        or line.startswith("diff ")
        or line.startswith("--- ")
        or line.startswith("+++ ")
        or line.startswith("index ")
    )


def split_lines(text: str) -> list[str]:
    lines = text.split("\n")
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def repair(text: str) -> tuple[str, int, list[str]]:
    lines = split_lines(text.replace("\r\n", "\n").replace("\r", "\n"))
    out: list[str] = []
    repaired = 0
    problems: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        match = HUNK_RE.match(line)
        if not match:
            out.append(line)
            i += 1
            continue

        old_start, old_len_s, new_start, new_len_s, tail = match.groups()
        old_len = int(old_len_s) if old_len_s is not None else 1
        new_len = int(new_len_s) if new_len_s is not None else 1

        body: list[str] = []
        old_count = 0
        new_count = 0
        j = i + 1
        while j < len(lines) and not _is_boundary(lines[j]):
            entry = lines[j]
            if entry.startswith("+") and not entry.startswith("+++"):
                new_count += 1
            elif entry.startswith("-") and not entry.startswith("---"):
                old_count += 1
            elif entry.startswith(" ") or entry == "":
                old_count += 1
                new_count += 1
            elif entry.startswith("\\"):
                pass
            else:
                problems.append(f"unexpected diff line {j + 1}: {entry[:60]!r}")
                break
            body.append(entry)
            j += 1

        if (old_count, new_count) != (old_len, new_len):
            repaired += 1
            out.append(f"@@ -{old_start},{old_count} +{new_start},{new_count} @@{tail}")
        else:
            out.append(line)
        out.extend(body)
        i = j

    return "\n".join(out) + "\n", repaired, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="directory containing *.patch")
    parser.add_argument("destination", help="directory to write repaired patches")
    args = parser.parse_args()

    src = Path(args.source)
    dst = Path(args.destination)
    dst.mkdir(parents=True, exist_ok=True)

    patches = sorted(src.glob("*.patch"))
    if not patches:
        print(f"no patches found in {src}", file=sys.stderr)
        return 1

    failures = 0
    for patch in patches:
        text = patch.read_bytes().decode("utf-8", "replace")
        fixed, repaired, problems = repair(text)
        target = dst / patch.name
        target.write_text(fixed, encoding="utf-8", newline="\n")
        note = f"{repaired} hunk header(s) recomputed" if repaired else "headers already consistent"
        print(f"{patch.name}: {note}")
        for problem in problems:
            print(f"  WARNING {problem}", file=sys.stderr)
            failures += 1

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
