#!/usr/bin/env python3
from pathlib import Path
import re, sys
root = Path(__file__).resolve().parents[1]
skill = root/'SKILL.md'
text = skill.read_text(encoding='utf-8')
if not text.startswith('---\n'): raise SystemExit('SKILL.md: missing YAML frontmatter')
parts = text.split('---',2)
if len(parts)<3: raise SystemExit('SKILL.md: invalid frontmatter')
fm = parts[1]
name = re.search(r'^name:\s*([^\n]+)$', fm, re.M)
desc = re.search(r'^description:\s*(.+)$', fm, re.M)
if not name or not desc: raise SystemExit('SKILL.md: name/description required')
n = name.group(1).strip()
if not re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?', n) or '--' in n: raise SystemExit('SKILL.md: invalid name')
if len(desc.group(1).strip()) > 1024: raise SystemExit('SKILL.md: description too long')
if n != root.name: raise SystemExit('SKILL.md: name must match directory')
print('PASS: basic Agent Skills structure and frontmatter checks')
