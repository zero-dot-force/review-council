"""Check the Lola module under module/ for what breaks it when installed.

- Agents (agents/*.md), top-level commands (commands/*.md) and skills
  (skills/<name>/SKILL.md) need YAML frontmatter with a description; a
  skill's name must match its directory.
- Any frontmatter present must parse as a YAML mapping.
- Relative Markdown links must point at a file that exists.

Exits 1 and prints each problem when any check fails.
"""

import pathlib
import re
import sys

import yaml

MODULE = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "module")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
problems = []


def frontmatter(path):
    text = path.read_text()
    if not text.startswith("---\n"):
        return None
    try:
        _, block, _ = text.split("---\n", 2)
    except ValueError:
        problems.append(f"{path}: frontmatter has no closing ---")
        return None
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as err:
        problems.append(f"{path}: frontmatter isn't valid YAML: {err}")
        return None
    if not isinstance(data, dict):
        problems.append(f"{path}: frontmatter isn't a mapping")
        return None
    return data


def needs_description(path):
    data = frontmatter(path)
    if data is None:
        if not any(p.startswith(str(path)) for p in problems):
            problems.append(f"{path}: needs frontmatter with a description")
        return None
    if not str(data.get("description") or "").strip():
        problems.append(f"{path}: frontmatter has no description")
    return data


for path in sorted(MODULE.rglob("*.md")):
    frontmatter(path)  # anything with frontmatter must parse

for path in sorted((MODULE / "agents").glob("*.md")):
    needs_description(path)
for path in sorted((MODULE / "commands").glob("*.md")):
    needs_description(path)
for path in sorted((MODULE / "skills").glob("*/SKILL.md")):
    data = needs_description(path)
    if data is not None and data.get("name") != path.parent.name:
        problems.append(f"{path}: name {data.get('name')!r} doesn't match its directory {path.parent.name!r}")

for path in sorted(MODULE.rglob("*.md")):
    in_code = False
    for line in path.read_text().splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for target in LINK.findall(line):
            if re.match(r"^[a-z][a-z0-9+.-]*:|^#|^/", target):
                continue  # URL, mailto, anchor or absolute path
            file = target.split("#", 1)[0]
            if file and not (path.parent / file).exists():
                problems.append(f"{path}: broken link to {target}")

problems = sorted(set(problems))
for problem in problems:
    print(problem)
sys.exit(1 if problems else 0)
