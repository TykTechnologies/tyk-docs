#!/usr/bin/env python3
"""Check that the Latest Releases data matches the release notes.

For each component in snippets/release-data.mdx (or the inline releaseData in
developer-support/release-notes/overview.mdx on older branches):
- `latest` and `latestData.name` equal the highest version in its release notes.
- `lts`, if set, equals the highest version in its release notes for that minor line.
- `latestData.date` equals the "Release Date" of the latest version.
- `latestData.docker` and `latestData.tag`, if they contain a version, point to the latest version.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

DATA_FILES = ["snippets/release-data.mdx", "developer-support/release-notes/overview.mdx"]
HEADING_RE = re.compile(r"^#{2,4}\s+v?(\d+\.\d+\.\d+)\b[^\n]*Release Notes", re.M)
RELEASE_DATE_RE = re.compile(r"Release Date:?\s*([^\n<]+)")
VERSION_IN_URL_RE = re.compile(r"(?<![\d.])v?(\d+\.\d+\.\d+)(?![\d.])")


def load_release_data(root):
    for rel in DATA_FILES:
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        m = re.search(r"export const releaseData\s*=\s*", text)
        if not m:
            continue
        obj, _ = json.JSONDecoder().raw_decode(text, m.end())
        return rel, obj
    raise SystemExit("❌ No releaseData found in " + " or ".join(DATA_FILES))


def vkey(v):
    return tuple(int(x) for x in v.split("."))


def parse_date(s):
    s = re.sub(r"(\d+)(st|nd|rd|th)\b", r"\1", s.strip().rstrip("."))
    s = s.replace(",", "")
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def release_date(notes, version):
    for m in HEADING_RE.finditer(notes):
        if m.group(1) == version:
            nxt = HEADING_RE.search(notes, m.end())
            section = notes[m.end(): nxt.start() if nxt else len(notes)]
            d = RELEASE_DATE_RE.search(section)
            return d.group(1).strip() if d else None
    return None


def check_component(c, root):
    name = c.get("name", "?")
    errors = []
    notes_path = os.path.join(root, c["releaseNotesPath"] + ".mdx")
    if not os.path.exists(notes_path):
        return [f"{name}: release notes file {c['releaseNotesPath']}.mdx does not exist"]
    notes = open(notes_path, encoding="utf-8").read()
    versions = sorted({m.group(1) for m in HEADING_RE.finditer(notes)}, key=vkey)
    if not versions:
        return [f"{name}: no 'X.Y.Z Release Notes' headings found in {c['releaseNotesPath']}.mdx"]

    newest = versions[-1]
    data = c.get("latestData", {})
    if c.get("latest") != newest:
        errors.append(f"{name}: latest is {c.get('latest')}, but the newest release notes are for {newest}")
    if data.get("name") != newest:
        errors.append(f"{name}: latestData.name is {data.get('name')}, but the newest release notes are for {newest}")

    lts = c.get("lts")
    if lts:
        line = [v for v in versions if vkey(v)[:2] == vkey(lts)[:2]]
        if not line:
            errors.append(f"{name}: lts is {lts}, but there are no release notes for {'.'.join(lts.split('.')[:2])}.x")
        elif lts != line[-1]:
            errors.append(f"{name}: lts is {lts}, but the newest release notes in that line are for {line[-1]}")

    raw = release_date(notes, newest)
    expected = parse_date(raw) if raw else None
    actual = None
    try:
        actual = datetime.strptime(data.get("date", ""), "%d/%m/%Y").date()
    except ValueError:
        errors.append(f"{name}: latestData.date '{data.get('date')}' is not in DD/MM/YYYY format")
    if raw is None:
        errors.append(f"{name}: no 'Release Date' found in the {newest} release notes")
    elif expected is None:
        errors.append(f"{name}: cannot read the {newest} release date '{raw}'")
    elif actual and actual != expected:
        errors.append(f"{name}: latestData.date is {data['date']}, but the {newest} release notes say {raw}"
                      f" ({expected.strftime('%d/%m/%Y')})")

    for field in ("docker", "tag"):
        url = data.get(field) or ""
        found = {m.group(1) for m in VERSION_IN_URL_RE.finditer(url)}
        if found and found != {newest}:
            errors.append(f"{name}: latestData.{field} points to {', '.join(sorted(found))}, not {newest}: {url}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", default=".", help="docs repository root")
    args = parser.parse_args(argv)

    data_file, data = load_release_data(args.root)
    components = [c for group in data.values() for c in group]
    errors = [e for c in components for e in check_component(c, args.root)]
    for e in errors:
        print(f"❌ {e}")
    if errors:
        print(f"\n❌ {len(errors)} problem(s) in {data_file}. Update it in the same PR as the release notes.")
        return 1
    print(f"✅ {data_file} matches the release notes for {len(components)} components.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
