---
mode: agent
description: Extract one or more units into records (step F1, extractor).
---
Play `agents/extractor.md` for `${input:args:<pkg> <unit or range, e.g. ot/ch13 or ot/ch13-ch20>}`, following the F1 section of [PIPELINE.md](../../PIPELINE.md). For each unit, read only that unit, the ruler, the roster, `sources.md`, and the glossary if it exists, and write one record. For more than one unit, do them one at a time, and read nothing of one unit while extracting another. Log the step, and list the records' `Needs a human` items at the end.
