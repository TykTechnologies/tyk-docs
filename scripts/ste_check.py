#!/usr/bin/env python3
"""Run the ASD-STE100 `ste` validator against .mdx/.md files changed vs a base branch.

Usage:
    python scripts/ste_check.py                  # check current branch vs origin/main
    python scripts/ste_check.py --base main       # check vs a local branch
    python scripts/ste_check.py path/to/file.mdx  # check specific files directly, no git diff involved

Strips YAML frontmatter, import statements, and standalone JSX tag lines
before handing prose to `ste`, since those aren't STE100 subject matter.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
IMPORT_RE = re.compile(r"^\s*import\s+.+\s+from\s+['\"].+['\"];?\s*$")
JSX_LINE_RE = re.compile(r"^\s*</?[A-Za-z][^\n]*>\s*$")


def find_ste_binary():
    for candidate in ("ste", str(Path.home() / "go/bin/ste")):
        try:
            subprocess.run([candidate, "version"], capture_output=True, check=True)
            return candidate
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    sys.exit("ste binary not found; run: go install github.com/probelabs/ste/cmd/ste@latest")


def changed_files(base):
    out = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [f for f in out.splitlines() if f.endswith((".mdx", ".md"))]


def strip_non_prose(text):
    text = FRONTMATTER_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text, count=1)
    lines = text.split("\n")
    return "\n".join(
        "" if IMPORT_RE.match(line) or JSX_LINE_RE.match(line) else line
        for line in lines
    )


def run_ste(binary, content, config=None, fmt="json"):
    cmd = [binary, "check", "--markdown", "--format", fmt]
    if config:
        cmd += ["--config", config]
    cmd.append("-")
    proc = subprocess.run(cmd, input=content, capture_output=True, text=True)
    if proc.returncode == 2:
        sys.exit(f"ste execution error: {proc.stderr}")
    return proc.stdout


def check_file(binary, f, config, need_json):
    content = strip_non_prose(Path(f).read_text())
    raw_pretty = run_ste(binary, content, config, fmt="pretty")
    body = "\n".join(
        line for line in raw_pretty.splitlines()
        if not re.match(r"^\d+ files checked:", line)
    ).replace("stdin:", f"{f}:").strip("\n")
    errors = raw_pretty.count("\nerror[") + (1 if raw_pretty.startswith("error[") else 0)
    warnings = raw_pretty.count("\nwarning[") + (1 if raw_pretty.startswith("warning[") else 0)
    raw_json = run_ste(binary, content, config, fmt="json") if need_json else None
    return {"file": f, "errors": errors, "warnings": warnings, "body": body, "json": raw_json}


def render_pretty(results, total_errors, total_warnings, file_count):
    for r in results:
        if r["errors"] or r["warnings"]:
            print(f"\n=== {r['file']}: {r['errors']} errors, {r['warnings']} warnings ===")
            print(r["body"])
    print(f"\n{file_count} files checked: {total_errors} errors, {total_warnings} warnings")


def render_json(results, total_errors, total_warnings, file_count):
    for r in results:
        if r["errors"] or r["warnings"]:
            print(r["json"])
    print(f"\n{file_count} files checked: {total_errors} errors, {total_warnings} warnings")


def render_markdown(results, total_errors, total_warnings):
    flagged = [r for r in results if r["errors"] or r["warnings"]]
    print(MARKDOWN_MARKER)
    print("## STE100 style check (advisory)")
    print()
    if not flagged:
        print("No findings against the ASD-STE100 style rules in the files this PR changed.")
        return
    print(f"{total_errors} errors, {total_warnings} warnings across {len(flagged)} file(s).")
    print()
    print("| File | Errors | Warnings |")
    print("|---|---|---|")
    for r in flagged:
        print(f"| `{r['file']}` | {r['errors']} | {r['warnings']} |")
    print()
    print("<details><summary>Full findings</summary>")
    print()
    print("```")
    for r in flagged:
        print(r["body"])
        print()
    print("```")
    print("</details>")
    print()
    print("_Advisory only, this does not block merging. Run `python3 scripts/ste_check.py` locally to check before pushing._")


MARKDOWN_MARKER = "<!-- ste100-advisory-check -->"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="origin/main", help="base ref to diff against (default: origin/main)")
    parser.add_argument("--config", help="path to ste.yaml (default: auto-discovered from cwd upward)")
    parser.add_argument("--format", choices=["pretty", "json", "markdown"], default="pretty",
                         help="pretty: source snippet with a caret per finding (default). "
                              "json: raw ste-diagnostics/v1 per flagged file. "
                              "markdown: PR-comment-ready summary table + collapsible findings")
    parser.add_argument("files", nargs="*", help="specific files to check instead of the diff")
    args = parser.parse_args()

    binary = find_ste_binary()
    direct = bool(args.files)
    files = args.files if direct else changed_files(args.base)
    if not files:
        if args.format == "markdown":
            print(MARKDOWN_MARKER)
            print("## STE100 style check (advisory)")
            print()
            print(f"No changed .mdx/.md files vs {args.base}.")
        else:
            print(f"No changed .mdx/.md files vs {args.base}")
        return
    if direct:
        missing = [f for f in files if not Path(f).exists()]
        if missing:
            sys.exit(f"file not found: {', '.join(missing)}")

    results = [check_file(binary, f, args.config, need_json=args.format == "json") for f in files]
    total_errors = sum(r["errors"] for r in results)
    total_warnings = sum(r["warnings"] for r in results)

    if args.format == "pretty":
        render_pretty(results, total_errors, total_warnings, len(files))
    elif args.format == "json":
        render_json(results, total_errors, total_warnings, len(files))
    else:
        render_markdown(results, total_errors, total_warnings)

    sys.exit(1 if total_errors or total_warnings else 0)


if __name__ == "__main__":
    main()
