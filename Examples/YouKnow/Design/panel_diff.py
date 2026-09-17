#!/usr/bin/env python3
"""Judge a fresh panel render against the committed files by pixels.

PNG bytes depend on the encoder, so a render on another machine can rewrite
every file in GUI2D/ and GUI/Output/ without changing a pixel. The Panels
workflow therefore compares pixels: a file whose pixels equal the committed
ones is restored from git, so it never churns, and only real changes are
reported, and, on a manual run, committed.

    python3 Design/panel_diff.py                       # list changes, exit 1 if any
    python3 Design/panel_diff.py --restore-unchanged   # drop byte-only churn first
    python3 Design/panel_diff.py --exit-zero           # report through the exit status
                                                       # only via GITHUB_OUTPUT

Non-image files under the same directories (the Lua panel definitions) count
as changed whenever git says they are.
"""

import io
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

PROJECT = Path(__file__).resolve().parent.parent
WATCHED = ("GUI2D", "GUI/Output")


def git(*arguments, binary=False):
    result = subprocess.run(["git", *arguments], cwd=PROJECT, check=True,
                            capture_output=True)
    return result.stdout if binary else result.stdout.decode()


def same_pixels(path):
    """True when the working file and HEAD's decode to the same RGBA pixels."""
    committed = git("show", f"HEAD:./{path}", binary=True)
    with Image.open(io.BytesIO(committed)) as before, Image.open(PROJECT / path) as after:
        return (before.size == after.size
                and before.convert("RGBA").tobytes() == after.convert("RGBA").tobytes())


def main(argv):
    restore = "--restore-unchanged" in argv
    exit_zero = "--exit-zero" in argv
    modified = git("ls-files", "--modified", "--", *WATCHED).split()
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *WATCHED).split()
    changed = list(untracked)
    for path in modified:
        if path.endswith(".png") and same_pixels(path):
            if restore:
                git("checkout", "--", path)
            continue
        changed.append(path)
    for path in changed:
        print(f"changed: {path}")
    print(f"{len(changed)} panel file(s) differ from the committed render"
          if changed else "the committed panels equal a fresh render, pixel for pixel")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"changed={len(changed)}\n")
    return 0 if exit_zero or not changed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
