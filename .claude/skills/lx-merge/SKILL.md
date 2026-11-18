---
name: lx-merge
description: Merge every record into the package's files (step F2b).
argument-hint: <pkg>
disable-model-invocation: true
---
Run `python tools/lx.py merge $ARGUMENTS --dry`. For each conflict, find its cause in the records and propose a fix: re-extract the unit, or ask me. When the dry run is clean, run the merge, read the changed files for anything the tool can't judge, and log the step.
