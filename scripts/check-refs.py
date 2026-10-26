#!/usr/bin/env python3
"""Check the references between files that `claude plugin validate` does not.

- Relative Markdown links, and their #anchors, resolve.
- Every marketplace entry points at a plugin whose plugin.json name matches.
- Every skill an agent preloads (`skills:` frontmatter) exists in the same plugin.
- Every `<plugin>:<name>` reference in Markdown names an agent or skill of that plugin.

Standard library only. Prints GitHub annotations and exits 1 on any error.
Usage: scripts/check-refs.py [repo-root]
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors = []


def error(path, line, message):
    rel = path.relative_to(ROOT) if path.is_absolute() else path
    errors.append(f"::error file={rel},line={line}::{message}")


def frontmatter(path):
    """The simple key: value pairs of a file's YAML frontmatter, values as raw strings."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def yaml_list(raw):
    """A flow-style list (["a", "b"]) or a single scalar, as a list of strings."""
    raw = raw.strip()
    if raw.startswith("["):
        return [s.strip().strip("'\"") for s in raw.strip("[]").split(",") if s.strip()]
    return [raw.strip("'\"")] if raw else []


def slug(heading):
    """GitHub's anchor for a heading."""
    text = re.sub(r"[`*_]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path):
    found, in_fence = set(), False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and (m := re.match(r"^#{1,6}\s+(.*)$", line)):
            found.add(slug(m.group(1)))
    return found


markdown = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)

# Plugins, from the marketplace.
plugins = {}
marketplace = ROOT / ".claude-plugin" / "marketplace.json"
for entry in json.loads(marketplace.read_text(encoding="utf-8")).get("plugins", []):
    source = entry.get("source")
    if not isinstance(source, str):
        continue
    plugin_dir = (ROOT / source).resolve()
    manifest = plugin_dir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        error(marketplace, 1, f"plugin '{entry['name']}': no {manifest.relative_to(ROOT)}")
        continue
    name = json.loads(manifest.read_text(encoding="utf-8")).get("name")
    if name != entry["name"]:
        error(manifest, 1, f"name '{name}' differs from the marketplace entry '{entry['name']}'")
    skills = {}
    for skill in sorted(plugin_dir.glob("skills/*/SKILL.md")):
        skills[frontmatter(skill).get("name") or skill.parent.name] = skill
    agents = {}
    for agent in sorted(plugin_dir.glob("agents/*.md")):
        agents[frontmatter(agent).get("name") or agent.stem] = agent
    plugins[entry["name"]] = {"skills": skills, "agents": agents}

# Preloaded skills.
for plugin, parts in plugins.items():
    for agent in parts["agents"].values():
        for skill in yaml_list(frontmatter(agent).get("skills", "")):
            if skill.split(":", 1)[-1] not in parts["skills"]:
                error(agent, 1, f"preloads skill '{skill}', which plugin '{plugin}' does not have")

# Links and plugin:name references.
link = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
ref = re.compile(r"(?<![\w@./-])(" + "|".join(map(re.escape, plugins)) + r"):([a-z0-9][a-z0-9-]*)") if plugins else None
for path in markdown:
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if ref:
            for m in ref.finditer(line):
                plugin, name = m.groups()
                if name not in plugins[plugin]["skills"] and name not in plugins[plugin]["agents"]:
                    error(path, number, f"'{plugin}:{name}' is not an agent or skill of plugin '{plugin}'")
        if in_fence:
            continue
        for target in link.findall(re.sub(r"`[^`]*`", "", line)):
            if re.match(r"^[a-z][a-z0-9+.-]*:", target):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (path.parent / file_part).resolve() if file_part else path
            if not dest.exists():
                error(path, number, f"link target '{target}' does not exist")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                error(path, number, f"link target '{target}': no heading for '#{anchor}'")

for e in errors:
    print(e)
print(f"check-refs: {len(markdown)} Markdown files, {len(plugins)} plugins, {len(errors)} errors")
sys.exit(1 if errors else 0)
