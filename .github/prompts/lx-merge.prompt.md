---
mode: agent
description: Merge every record into the package's files (step F2b).
---
Run `python tools/lx.py merge ${input:args:<pkg>} --dry`. For each conflict, find its cause in the records and propose a fix: re-extract the unit, or ask me. When the dry run is clean, run the merge, read the changed files for anything the tool can't judge, and log the step.
