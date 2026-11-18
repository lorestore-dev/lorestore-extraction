# LoreStore extraction workspace

A VS Code workspace for building [LoreStore](https://github.com/lorestore-dev/lorestore)
packages from source texts. It runs the spec's `extraction` workflow (§13.6) with an AI
assistant playing each agent from its reference file, and a small tool for the steps
that are mechanical.

It comes with one package in progress: *Oliver Twist*, chapters 1–12 of 53. The
package lives in its own repository,
[`oliver-twist`](https://github.com/lorestore-dev/oliver-twist), mounted here at
`worlds/oliver-twist/base/`.

## Getting started

```sh
git clone --recurse-submodules https://github.com/lorestore-dev/lorestore-extraction.git
cd lorestore-extraction
pip install -r lorestore/tools/requirements.txt
python tools/lx.py setup
```

Then open `lorestore-extraction.code-workspace` in VS Code, and run
`python tools/lx.py status oliver-twist/base` (or the **lx: status** task) to see where
the package is.

## The pipeline

[PIPELINE.md](PIPELINE.md) is the runbook: each step, what it reads and writes, and
where it stops for a human. In outline:

| Step | Who | Does |
| --- | --- | --- |
| Before F0 | you, with `lx new` and `lx split` | Create the package, register its sources, split the texts into units |
| F0 | assistant as worldbuilder | Write the ruler; you approve it |
| F0b | assistant as character-designer | Seed the roster from your cast list; you approve it |
| F1 | assistant as extractor | One extraction record per unit, in parallel if the assistant can |
| F2a | assistant as merger | Merge new names into the roster; you settle every question the records raise |
| F2b | `lx merge` | Merge every record into the package's files, and list conflicts |
| F4 | `lx index` | Index the package; you approve it and bump its version |

Each step is a command in the assistant's chat: `/lx-ruler`, `/lx-seed`, `/lx-extract`,
`/lx-roster`, `/lx-merge`, `/lx-index`. They're skills in Claude Code
(`.claude/skills/`) and prompt files in GitHub Copilot (`.github/prompts/`). Both
assistants also read the workspace's instructions, in `CLAUDE.md` and
`.github/copilot-instructions.md`.

Every step is logged in the package's `extraction/<pkg>/log.md`, with the decisions
made at each gate and anything the spec didn't settle.

## What's here

| Path | What it is |
| --- | --- |
| `lorestore/` | The spec, as a submodule pinned at `v0.4` |
| `agents/`, `workflows/` | Copied from the spec by `lx setup`; not committed |
| `worlds/<pkg>/` | The packages being built |
| `extraction/<pkg>/` | Each package's texts, extraction records, and log |
| `tools/lx.py` | `setup`, `new`, `split`, `status`, `merge`, `index` |
| `PIPELINE.md` | The runbook |

## Starting a package of your own

```sh
python tools/lx.py new my-fandom/base --name "My Fandom"
python tools/lx.py split my-fandom/base BK1 book1.txt --pattern "^Chapter \d+"
```

Register the sources in `worlds/my-fandom/base/sources.md`, then run `/lx-ruler
my-fandom/base`. To give the package its own repository later, move `worlds/my-fandom/base`
out and add it back as a submodule.

## License

The workspace (the tool, the runbook, and the instructions) is licensed under the
Apache License 2.0, like the spec: see [LICENSE](LICENSE). Each package and its
extraction files carry their own license. For *Oliver Twist*, the novel's text in
`extraction/oliver-twist/base/texts/` is in the public domain (from Project Gutenberg
ebook 730, with its header and license removed), and the records, the log, and the
package are licensed CC BY 4.0.
