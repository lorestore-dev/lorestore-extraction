"""lx: the mechanical parts of the LoreStore extraction workflow (§13.6).

The agents' work (F0 ruler, F0b seed roster, F1 records, the F2a roster gate) is done
by an assistant playing each agent from agents/<name>.md. This tool does the rest:

  python tools/lx.py setup                       copy agents/ and workflows/ from the spec
  python tools/lx.py new <pkg> --name "<Title>"  scaffold a base package and its extraction
  python tools/lx.py split <pkg> <work> <file> --pattern <regex>
                                                 split a source text into units
  python tools/lx.py status <pkg>                what's extracted, what's waiting, what fails
  python tools/lx.py merge <pkg> [--dry]         F2b: merge every record into the bible
  python tools/lx.py index <pkg>                 F4: write index.md

<pkg> is a package path such as oliver-twist/base: the package lives at
worlds/<pkg>/ and its extraction at extraction/<pkg>/ (§2.1, §2.6).
"""
import argparse, collections, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "lorestore"


# ---------------------------------------------------------------- files and tables

def read(p):
    return p.read_text(encoding="utf-8")


def write(p, lines):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\r\n")


def table(text, heading):
    """Rows of the first Markdown table under `## <heading>`, as dicts."""
    m = re.search(r"^#{2,3} " + re.escape(heading) + r"\s*$(.*?)(?=^#{1,3} |\Z)", text, re.M | re.S)
    if not m:
        return []
    lines = [l for l in m.group(1).splitlines() if l.startswith("|")]
    if len(lines) < 2:
        return []
    split = lambda l: [c.strip() for c in re.split(r"(?<!\\)\|", l.strip()[1:-1])]
    hdr = split(lines[0])
    return [dict(zip(hdr, split(l))) for l in lines[2:]]


def fmt(hdr, rows):
    w = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(hdr)]
    line = lambda r: "| " + " | ".join(c.ljust(w[i]) for i, c in enumerate(r)) + " |"
    return [line(hdr), "| " + " | ".join("-" * x for x in w) + " |"] + [line(r) for r in rows]


def front_matter(text):
    m = re.match(r"---\s*\n(.*?)\n---", text, re.S)
    return dict(re.findall(r"^(\S+):\s*(.*?)\s*$", m.group(1), re.M)) if m else {}


class Package:
    def __init__(self, pkg):
        self.id = pkg
        self.bible = ROOT / "worlds" / pkg
        self.work = ROOT / "extraction" / pkg
        if not self.bible.is_dir():
            sys.exit(f"no package at worlds/{pkg}/")

    def records(self):
        return sorted((self.work / "extractions").glob("*/*.md"))

    def units(self):
        return sorted((self.work / "texts").glob("*/*.md"))

    def roster(self):
        p = self.bible / "characters/_roster.md"
        return {r["Slug"]: r for r in table(read(p), "Characters")} if p.exists() else {}

    def sources(self):
        p = self.bible / "sources.md"
        return {r["ID"] for r in table(read(p), "Sources")} if p.exists() else set()

    def ruler(self):
        """Segment -> (order, children), from the ruler's ## Order table."""
        p = self.bible / "canon-timeline.md"
        if not p.exists():
            return {}
        out = {}
        for i, r in enumerate(table(read(p), "Order")):
            n = r.get("Children", "")
            out[r["Segment"]] = (i, int(n) if n.isdigit() else None)
        return out


def point_key(ruler, p):
    """Sort key for a ruler point SEG[:n[:m]], or None if it isn't on the ruler."""
    parts = p.split(":")
    if parts[0] not in ruler or len(parts) > 3 or not all(x.isdigit() for x in parts[1:]):
        return None
    order, children = ruler[parts[0]]
    nums = [int(x) for x in parts[1:]] + [0] * (3 - len(parts))
    if children is not None and nums[0] > children:
        return None
    return (order, *nums)


# ---------------------------------------------------------------- setup

def cmd_setup(a):
    if not (SPEC / "spec").is_dir():
        subprocess.run(["git", "-c", "protocol.file.allow=always", "submodule", "update",
                        "--init", "--recursive"], cwd=ROOT, check=True)
    for d in ("agents", "workflows"):
        if (ROOT / d).exists():
            shutil.rmtree(ROOT / d)
        shutil.copytree(SPEC / d, ROOT / d)
    tag = subprocess.run(["git", "describe", "--tags", "--always"], cwd=SPEC,
                         capture_output=True, text=True).stdout.strip()
    print(f"agents/ and workflows/ copied from lorestore {tag}")


# ---------------------------------------------------------------- new

def cmd_new(a):
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)+", a.pkg):
        sys.exit("package path must be <fandom>/<package>, lower-case with hyphens")
    bible, work = ROOT / "worlds" / a.pkg, ROOT / "extraction" / a.pkg
    if bible.exists() or work.exists():
        sys.exit(f"{a.pkg} already exists")
    ver = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], cwd=SPEC,
                         capture_output=True, text=True).stdout.strip().lstrip("v") or "0.4"
    pid = a.pkg.split("/")[0] if a.pkg.endswith("/base") else a.pkg
    write(bible / "package.yaml", [
        f'spec_version: "{ver}"', f"id: {pid}", "kind: base", f'name: "{a.name}"',
        "version: 0.1.0", "status: open-for-extraction", "relies-on: []",
        f"license: {a.license}"])
    write(bible / "sources.md", [
        "# Sources", "", "## Sources",
        "| ID | Tier | Title | Author / origin | Notes |",
        "| -- | ---- | ----- | --------------- | ----- |",
        "", "## Bibliography"])
    (work / "texts").mkdir(parents=True)
    (work / "extractions").mkdir()
    write(work / "log.md", [
        f"# Extraction log: {a.pkg}", "",
        "The `extraction` workflow (§13.6). Each step lists what it read, what it wrote,",
        "the decisions made at its gate, and anything the spec or the agent file didn't",
        "settle.", "", "## Before F0 (human)", "",
        "- Wrote `package.yaml` and `sources.md`. <!-- register the sources, with tiers -->",
        "", "## Findings", ""])
    print(f"created worlds/{a.pkg}/ and extraction/{a.pkg}/")
    print("next: register the sources in sources.md, then split the texts into units")


# ---------------------------------------------------------------- split

def cmd_split(a):
    pk = Package(a.pkg)
    text = pathlib.Path(a.file).read_text(encoding="utf-8-sig")
    if a.start:
        text = text[text.index(a.start):]
    if a.end:
        text = text[:text.index(a.end)]
    ms = list(re.finditer(a.pattern, text, re.M))
    if not ms:
        sys.exit("the pattern matched nothing")
    out = pk.work / "texts" / a.work.lower()
    out.mkdir(parents=True, exist_ok=True)
    for i, m in enumerate(ms):
        body = text[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(text)].strip()
        head = " ".join(m.group(0).split())
        write(out / f"ch{i + 1:02d}.md", [f"# {head}", "", body])
    print(f"wrote {len(ms)} units to extraction/{a.pkg}/texts/{a.work.lower()}/")


# ---------------------------------------------------------------- merge (F2b)

def gather(pk):
    """Every record's facts, quotations, and new names, with aliases mapped to slugs."""
    roster = pk.roster()
    alias = {a: s for s, r in roster.items()
             for a in (x.strip() for x in r.get("Aliases", "").split(";"))
             if re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a)}
    slug = lambda s: alias.get(s, s)
    facts, quotes, names = collections.defaultdict(list), [], []
    for f in pk.records():
        t = read(f)
        src = front_matter(t).get("source", "")
        rec = f"{f.parent.name}/{f.name}"
        for r in table(t, "Facts"):
            tgt = r.get("Target", "")
            m = re.fullmatch(r"characters/(.+)\.md", tgt)
            if m:
                tgt = f"characters/{slug(m.group(1))}.md"
            ent, attr = r.get("Entity", ""), r.get("Attribute", "")
            if tgt == "relationships.md":
                ent = "+".join(sorted(slug(x) for x in ent.split("+")))
            if tgt == "knowledge.md" and attr.startswith("state:"):
                attr = "state:" + slug(attr[6:])
            facts[tgt].append(dict(ent=ent, attr=attr, val=r.get("Value", ""), asof=r.get("As of", ""),
                                   src=r.get("Source", ""), cit=r.get("Citation", ""),
                                   tf=r.get("True from", ""), rec=rec))
        for r in table(t, "Quotations"):
            quotes.append(dict(r, Speaker=slug(r.get("Speaker", "")), src=src, rec=rec))
        for r in table(t, "New names"):
            names.append(dict(r, rec=rec))
    return roster, facts, quotes, names


def merge(pk):
    """Apply the merger's rules (agents/merger.md). Returns {target: lines}, problems."""
    roster, facts, quotes, _ = gather(pk)
    sources, ruler = pk.sources(), pk.ruler()
    key = lambda p: point_key(ruler, p)
    problems = []

    def invalid(tgt, r):
        bad = []
        if key(r["asof"]) is None:
            bad.append(f"{r['asof'] or 'empty'} is not on the ruler")
        elif r["tf"] and (key(r["tf"]) is None or key(r["tf"]) > key(r["asof"])):
            bad.append(f"True from {r['tf']} is later than As of {r['asof']}, or off the ruler")
        if r["src"] not in sources:
            bad.append(f"source {r['src']} is not in sources.md")
        used = []
        m = re.fullmatch(r"characters/(.+)\.md", tgt)
        if m:
            used.append(m.group(1))
        if tgt == "relationships.md":
            used += r["ent"].split("+")
        if r["attr"].startswith("state:"):
            used.append(r["attr"][6:])
        bad += [f"slug {u} is not in the roster" for u in used if u not in roster]
        return bad

    def history(tgt, rows):
        out, conflicts, groups = [], [], collections.OrderedDict()
        for r in rows:
            bad = invalid(tgt, r)
            if bad:
                conflicts.append(f"{r['ent'] + '.' if r['ent'] else ''}{r['attr']} at {r['asof']}: "
                                 f"\"{r['val']}\" ({r['cit']}): " + "; ".join(bad))
                continue
            groups.setdefault((r["ent"], r["attr"], r["asof"]), []).append(r)
        for (ent, attr, asof), rs in groups.items():
            vals = collections.OrderedDict()
            for r in rs:
                vals.setdefault((r["val"], r["src"], r["tf"]), []).append(r["cit"])
            if len(vals) > 1:
                conflicts.append(f"{ent + '.' if ent else ''}{attr} at {asof}: " + " vs ".join(
                    f"\"{v}\" ({'; '.join(dict.fromkeys(c))})" for (v, _, _), c in vals.items()))
                continue
            (v, s, tf), cits = next(iter(vals.items()))
            out.append(dict(ent=ent, attr=attr, val=v, asof=asof, src=s, tf=tf,
                            cit="; ".join(dict.fromkeys(cits))))
        out.sort(key=lambda r: (r["ent"], r["attr"], key(r["asof"])))
        return out, conflicts

    def tail(tgt, conflicts):
        problems.extend(f"{tgt}: {c}" for c in conflicts)
        return ["", "## Unresolved conflicts"] + [f"- {c}" for c in conflicts] if conflicts else []

    written = {}
    for tgt, rows in sorted(facts.items()):
        out, conflicts = history(tgt, rows)
        tf = any(r["tf"] for r in out)
        extra = lambda r: [r["tf"]] if tf else []
        if tgt.startswith("characters/"):
            s = tgt[len("characters/"):-3]
            r0 = roster.get(s, {"Name": s, "Origin": "canon"})
            lines = ["---", f"slug: {s}", f"name: {r0['Name']}", f"origin: {r0['Origin']}", "---",
                     "## State history"] + fmt(["Attribute", "Value", "As of", "Source", "Citation"]
                                               + (["True from"] if tf else []),
                                               [[r["attr"], r["val"], r["asof"], r["src"], r["cit"]] + extra(r)
                                                for r in out])
        elif tgt == "knowledge.md":
            sec = [r for r in out if r["attr"] == "truth"]
            kn = sorted((r for r in out if r["attr"].startswith("state:")),
                        key=lambda r: (r["ent"], key(r["asof"]), r["attr"]))
            lines = ["# Knowledge", "", "## Secrets"] + fmt(
                ["Secret", "Truth", "Source", "Citation"],
                [[r["ent"], r["val"], r["src"], r["cit"]] for r in sec]) + ["", "## Knowledge"] + fmt(
                ["Character", "Secret", "State", "As of", "Source", "Citation"],
                [[r["attr"][6:], r["ent"], r["val"], r["asof"], r["src"], r["cit"]] for r in kn])
        elif tgt == "glossary.md":
            terms = collections.OrderedDict()
            for r in sorted(out, key=lambda r: key(r["asof"])):
                t = terms.setdefault(r["ent"], dict(r, cits=[]))
                if (t["val"], t["attr"]) != (r["val"], r["attr"]):
                    conflicts.append(f"{r['ent']}: \"{t['val']}\" ({t['cit']}) vs \"{r['val']}\" ({r['cit']})")
                else:
                    t["cits"].append(r["cit"])
            lines = ["# Glossary", "", "## Terms"] + fmt(
                ["Term", "Meaning", "Kind", "Source", "Citation"],
                [[k, t["val"], t["attr"], t["src"], "; ".join(dict.fromkeys(t["cits"]))]
                 for k, t in sorted(terms.items())])
        else:
            title = tgt[:-3].replace("-", " ").replace("/", ": ").capitalize()
            first = "Pair" if tgt == "relationships.md" else "Entity"
            lines = [f"# {title}", "", "## State history"] + fmt(
                [first, "Attribute", "Value", "As of", "Source", "Citation"] + (["True from"] if tf else []),
                [[r["ent"], r["attr"], r["val"], r["asof"], r["src"], r["cit"]] + extra(r) for r in out])
        written[tgt] = lines + tail(tgt, conflicts)

    if quotes:
        n, rows, conflicts = collections.Counter(), [], []
        for q in sorted(quotes, key=lambda q: key(q.get("As of", "")) or (999,)):
            sp = q["Speaker"]
            n[sp] += 1
            if sp not in roster:
                conflicts.append(f"\"{q.get('Line')}\" ({q.get('Citation')}): speaker {sp} is not in the roster")
            rows.append([f"{sp}-{n[sp]}", q.get("Line", ""), sp, q.get("Rank", ""), q.get("As of", ""),
                         q["src"], q.get("Citation", "")])
        written["quotations.md"] = ["# Quotations", "", "## Quotations"] + fmt(
            ["ID", "Line", "Speaker", "Rank", "As of", "Source", "Citation"], rows) + tail("quotations.md", conflicts)
    return written, problems


def cmd_merge(a):
    pk = Package(a.pkg)
    written, problems = merge(pk)
    for p in problems:
        print("conflict:", p)
    print(f"{len(written)} targets, {len(problems)} unresolved conflict(s)")
    if not a.dry:
        for tgt, lines in written.items():
            write(pk.bible / tgt, lines)
        print(f"wrote worlds/{a.pkg}/; run `index` next")
    return 1 if problems else 0


# ---------------------------------------------------------------- index (F4)

def catalog():
    """File pattern -> (layer, holds), from the world-layer catalog of §3.3."""
    text = read(SPEC / "spec/03-layers.md")
    out = {}
    for r in table(text, "World layer"):
        name = re.match(r"`([^`]+)`", r.get("File (under `bible/`)", "") or next(iter(r.values())))
        if name:
            holds = re.sub(r"\s*\(§[\d.]+\)", "", r.get("Holds", "")).split(". ")[0]
            out.setdefault(name.group(1), (r.get("Layer", "world"), holds))
    return out


def cmd_index(a):
    pk = Package(a.pkg)
    cat = catalog()
    old = {}
    if (pk.bible / "index.md").exists():
        old = {r["Path"]: r["Holds"] for r in table(read(pk.bible / "index.md"), "Files")}
    first = ["package.yaml", "canon-timeline.md", "sources.md"]
    files = [p.relative_to(pk.bible).as_posix() for p in pk.bible.rglob("*")
             if p.is_file() and (p.suffix == ".md" or p.name == "package.yaml")
             and p.name not in ("index.md", "README.md", "LICENSE.md")]
    order = list(old)  # keep an existing index's order; new files follow, sorted
    files.sort(key=lambda f: (f not in order, order.index(f) if f in order else 0,
                              f not in first, first.index(f) if f in first else 0,
                              f.startswith("characters/"), f != "characters/_roster.md", f))
    rows, unknown = [], []
    for f in files:
        layer, holds = cat.get(f) or (cat.get("characters/<slug>.md") if re.fullmatch(r"characters/[a-z0-9-]+\.md", f) else None) or (None, None)
        if layer is None:
            unknown.append(f)
            layer, holds = "world", ""
        if f.startswith("characters/") and f != "characters/_roster.md":
            holds = "Character sheet"
        rows.append([f, layer, old.get(f) or holds])
    name = re.search(r'^name:\s*"?(.*?)"?\s*$', read(pk.bible / "package.yaml"), re.M)
    write(pk.bible / "index.md", [f"# Index: {name.group(1) if name else a.pkg}", "", "## Files"]
          + fmt(["Path", "Layer", "Holds"], rows))
    for f in unknown:
        print(f"not in the §3.3 catalog, listed as world: {f}")
    print(f"wrote worlds/{a.pkg}/index.md, {len(rows)} files")


# ---------------------------------------------------------------- status

def cmd_status(a):
    pk = Package(a.pkg)
    units, records = pk.units(), pk.records()
    done = {(r.parent.name, r.name) for r in records}
    todo = [u for u in units if (u.parent.name, u.name) not in done]
    print(f"package worlds/{a.pkg}/")
    try:
        import json, yaml, jsonschema
        schema = json.loads(read(SPEC / "schemas/package.schema.json"))
        errs = list(jsonschema.Draft202012Validator(schema).iter_errors(yaml.safe_load(read(pk.bible / "package.yaml"))))
        print("  package.yaml:", "valid" if not errs else "; ".join(e.message for e in errs))
    except ImportError:
        print("  package.yaml: not checked (pip install -r lorestore/tools/requirements.txt)")
    print("  ruler:", "present" if pk.ruler() else "missing (F0)")
    print("  roster:", f"{len(pk.roster())} characters" if pk.roster() else "missing (F0b)")
    print(f"F1: {len(records)} of {len(units)} units have records")
    if todo:
        print("  next:", ", ".join(f"{u.parent.name}/{u.name}" for u in todo[:5]) + (" …" if len(todo) > 5 else ""))
    roster, _, _, names = gather(pk)
    known = set(roster) | {x.strip() for r in roster.values() for x in r.get("Aliases", "").split(";")}
    new = [n for n in names if n.get("Proposed slug") and n["Proposed slug"] not in known]
    print(f"F2a: {len(new)} new name(s) not yet in the roster")
    for n in new:
        print(f"  {n['Proposed slug']} ({n['rec']}): {n.get('Context', '')}")
    asks = 0
    for f in records:
        m = re.search(r"^## Needs a human\s*$(.*?)(?=^## |\Z)", read(f), re.M | re.S)
        asks += len(re.findall(r"^- ", m.group(1), re.M)) if m else 0
    print(f"     {asks} Needs-a-human item(s) across the records; settle them in log.md")
    written, problems = merge(pk)
    print(f"F2b: {len(written)} targets, {len(problems)} unresolved conflict(s)")
    for p in problems:
        print("  ", p)
    stale = [t for t, lines in written.items()
             if not (pk.bible / t).exists() or read(pk.bible / t).splitlines() != lines]
    if stale:
        print(f"     {len(stale)} merged file(s) out of date: run `merge`")
    print("F4:", "index.md present" if (pk.bible / "index.md").exists() else "no index.md")


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(prog="lx", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    s = sub.add_parser("new"); s.add_argument("pkg"); s.add_argument("--name", required=True)
    s.add_argument("--license", default="CC-BY-4.0")
    s = sub.add_parser("split"); s.add_argument("pkg"); s.add_argument("work"); s.add_argument("file")
    s.add_argument("--pattern", required=True, help="regex matching each unit's heading line")
    s.add_argument("--start", help="text where the work begins (drop everything before)")
    s.add_argument("--end", help="text where the work ends (drop it and everything after)")
    for c in ("status", "index"):
        sub.add_parser(c).add_argument("pkg")
    s = sub.add_parser("merge"); s.add_argument("pkg"); s.add_argument("--dry", action="store_true")
    a = p.parse_args()
    sys.exit(globals()["cmd_" + a.cmd](a) or 0)


if __name__ == "__main__":
    main()
