---
name: lx-extract
description: Extract one or more units into records (step F1, extractor).
argument-hint: <pkg> <unit or range, e.g. ot/ch13 or ot/ch13-ch20>
disable-model-invocation: true
---
Play `agents/extractor.md` for `$ARGUMENTS`, following the F1 section of PIPELINE.md. For each unit, read only that unit, the ruler, the roster, `sources.md`, and the glossary if it exists, and write one record. For more than one unit, use one subagent per unit, each given only its own reads. Log the step, and list the records' `Needs a human` items at the end.
