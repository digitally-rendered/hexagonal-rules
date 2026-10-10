#!/usr/bin/env python3
"""Lint for this rules repository. Run: python3 -I tools/check_rules.py

Checks (each a finding class the reviews found by hand):
  refs     every `folder/NN` §M reference points at a file and a numbered heading that exist
  must     every line containing MUST / MUST NOT / NEVER (upper case) has an enforcing check
           named within the same section ("Check:", "check:", "test", "lint", "gate", "fails",
           "CI", "asserts") or the section is a Tests table
  readme   every markdown file under the rule folders is listed in README.md
  private  optional: terms listed one per line in .rules-lint/private-terms.txt (git-ignored,
           never committed) must not appear in any tracked file
Exit code 1 on any finding. Add an exemption with the trailing marker `<!-- lint: ok -->`
on the offending line.
"""
from __future__ import annotations
import re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
FOLDERS = ("shared", "python", "typescript", "go", "specs", "second-brain", "templates")
OK = "<!-- lint: ok -->"

def tracked_md() -> list[pathlib.Path]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / l for l in out.split("\n") if l]

def headings(path: pathlib.Path) -> set[str]:
    nums = set()
    for line in path.read_text().splitlines():
        m = re.match(r"^#{2,3}\s+(\d+[a-z]?)\.?\s", line)
        if m:
            nums.add(m.group(1))
    return nums

def file_by_prefix(folder: str, nn: str) -> pathlib.Path | None:
    d = ROOT / folder
    if not d.is_dir():
        return None
    hits = sorted(d.glob(f"{nn}-*.md"))
    return hits[0] if hits else None

REF = re.compile(r"`(shared|python|typescript|go|specs|second-brain)/(\d{2})`(?:\s*§\s*(\d+[a-z]?))?")

def check_refs(files) -> list[str]:
    out = []
    for f in files:
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if OK in line:
                continue
            for m in REF.finditer(line):
                folder, nn, sec = m.groups()
                target = file_by_prefix(folder, nn)
                if target is None:
                    out.append(f"{f.relative_to(ROOT)}:{i}: reference `{folder}/{nn}` has no file")
                    continue
                if sec and sec not in headings(target):
                    out.append(f"{f.relative_to(ROOT)}:{i}: `{folder}/{nn}` §{sec} is not a heading in {target.name}")
    return out

MUST = re.compile(r"\b(MUST NOT|MUST|NEVER)\b")
CHECK_WORDS = re.compile(r"(Check:|check:|\bcheck\b|\btest\b|\btests\b|\blint\b|\bgate\b|\bfails?\b|\bCI\b|\basserts?\b|Enforced by|enforced by)", re.I)

def sections(text: str):
    cur, buf = "preamble", []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s", line):
            yield cur, buf
            cur, buf = line, []
        else:
            buf.append(line)
    yield cur, buf

def check_must(files) -> list[str]:
    out = []
    for f in files:
        if f.name in ("README.md", "CLAUDE.md") or "reviews" in f.parts:
            continue
        for head, body in sections(f.read_text()):
            must_lines = [l for l in body if MUST.search(l) and OK not in l]
            if not must_lines:
                continue
            if not any(CHECK_WORDS.search(l) for l in body) and not re.search(r"test|check|gate", head, re.I):
                out.append(f"{f.relative_to(ROOT)}: section {head.strip()!r} states MUST/NEVER with no check named")
    return out

def check_readme(files) -> list[str]:
    readme = (ROOT / "README.md").read_text()
    out = []
    for f in files:
        rel = f.relative_to(ROOT)
        if rel.parts[0] in FOLDERS and f.name != "README.md" and f.name not in readme:
            out.append(f"{rel}: not listed in README.md")
    return out

def check_private(files) -> list[str]:
    terms_file = ROOT / ".rules-lint" / "private-terms.txt"
    if not terms_file.exists():
        return []
    terms = [t.strip() for t in terms_file.read_text().splitlines() if t.strip() and not t.startswith("#")]
    out = []
    all_files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
    for rel in all_files:
        if not rel or rel.startswith(".rules-lint"):
            continue
        p = ROOT / rel
        try:
            text = p.read_text()
        except (UnicodeDecodeError, IsADirectoryError):
            continue
        for t in terms:
            if re.search(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])", text, re.I):
                out.append(f"{rel}: private term present (see .rules-lint/private-terms.txt)")
                break
    return out

def main() -> int:
    files = tracked_md()
    findings = []
    for name, fn in (("refs", check_refs), ("must", check_must), ("readme", check_readme), ("private", check_private)):
        res = fn(files)
        findings += [f"[{name}] {r}" for r in res]
    for r in findings:
        print(r)
    print(f"{len(findings)} finding(s)")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
