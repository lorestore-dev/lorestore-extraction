---
mode: agent
description: Index a package and close the run (step F4).
---
Run `python tools/lx.py index ${input:args:<pkg>}`, check that every file has the right layer, and log the step. Then stop and ask me to approve the package and whether to bump its version.
