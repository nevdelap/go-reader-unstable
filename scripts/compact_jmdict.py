#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = ["zopfli"]
# ///
#
# Converts a jmdict-eng-*.json.zip (from scriptin/jmdict-simplified) into the
# ultra-compact and full English JMdict gzip files used by the app at runtime.
#
# Usage:
#   scripts/compact_jmdict.py
#
# Expects exactly one jmdict-eng-*.json.zip in the repo root (run from there).
# Normally run via scripts/update_jmdict_and_compact_repo.sh, but can be run directly
# after manually downloading the zip from:
#   https://github.com/scriptin/jmdict-simplified/releases
#
# Output format: { "word": {"p": ["pos", ...], "g": [["gloss", ...], ...], "pg": ["gloss", ...]}, ... }
#   p  — POS tags from the first English sense; merged across same-priority entries
#   g  — list of gloss groups; ultra-compact keeps common and grammar entries,
#        and full keeps every English sense for every entry
#   pg — (optional) glosses from particle (prt), expression (exp), and auxiliary (aux/aux-v/aux-adj) senses

import json
import os
import glob
import tempfile
import zipfile
from pathlib import Path
from typing import Any
import zopfli.gzip  # type: ignore[import-not-found]

# JMdict POS tags that signal a grammar/particle sense suitable for pg/pg2.
# exp covers compound particles like により, として that JMdict tags as expressions.
# aux/aux-v/aux-adj covers auxiliary verbs like ない, た, だ, られる.
GRAMMAR_POS = {'prt', 'exp', 'aux', 'aux-v', 'aux-adj'}


def _merge(entry: dict[str, Any], key: str, items: list[str]) -> None:
    """Merge items into entry[key] without duplicates. Modifies entry in-place."""
    existing = entry.get(key, [])
    seen = set(existing)
    for item in items:
        if item not in seen:
            existing.append(item)
            seen.add(item)
    entry[key] = existing


def _english_glosses(sense: dict[str, Any]) -> list[str]:
    """Extract English glosses from a sense."""
    return [g['text'] for g in sense['gloss'] if g['lang'] == 'eng']


def _entry_gloss_groups(entry: dict[str, Any], max_senses: int | None = None) -> list[list[str]]:
    """Extract gloss groups from an entry, optionally limiting to max_senses."""
    groups: list[list[str]] = []
    for sense in entry['sense']:
        glosses = _english_glosses(sense)
        if not glosses:
            continue
        groups.append(glosses)
        if max_senses and len(groups) >= max_senses:
            break
    return groups


def build_dict(max_senses: int | None = None, common_only: bool = False) -> dict[str, dict[str, Any]]:
    """Build a dictionary from JMdict entries.

    Args:
        max_senses: Maximum number of senses to include per entry (None = all)
        common_only: If True, only include common entries and grammar-related entries

    Returns:
        Dictionary mapping words to their gloss data
    """
    out: dict[str, dict[str, Any]] = {}
    common: dict[str, bool] = {}

    for entry in d['words']:
        is_common = any(k.get('common', False) for k in entry['kanji'] + entry['kana'])

        first_sense = next(
            (s for s in entry['sense'] if any(g['lang'] == 'eng' for g in s['gloss'])),
            None
        )
        if not first_sense:
            continue

        gloss_groups = _entry_gloss_groups(entry, max_senses)
        if not gloss_groups:
            continue

        # Collect glosses from grammar senses (pg is for disambiguation — words where g[0]
        # would be wrong in particle/auxiliary context; others fall back to g[0] at runtime).
        particle_glosses = list(dict.fromkeys(
            g['text']
            for sense in entry['sense']
            if GRAMMAR_POS.intersection(sense.get('partOfSpeech', []))
            for g in sense['gloss']
            if g['lang'] == 'eng'
        ))

        if common_only and not is_common and not particle_glosses:
            continue

        for k in entry['kanji'] + entry['kana']:
            word = k['text']
            if word not in out or (is_common and not common.get(word, False)):
                # New entry wins outright (first seen, or common displacing uncommon)
                prev_pg = out.get(word, {}).get('pg')
                out[word] = {
                    'p': list(first_sense.get('partOfSpeech', [])),
                    'g': [list(group) for group in gloss_groups]
                }
                if particle_glosses:
                    out[word]['pg'] = particle_glosses
                elif prev_pg:
                    out[word]['pg'] = prev_pg
                common[word] = is_common
            elif is_common == common.get(word, False):
                # Same priority: append glosses as new groups, merge POS tags
                for glosses in gloss_groups:
                    if glosses not in out[word]['g']:
                        out[word]['g'].append(list(glosses))
                _merge(out[word], 'p', first_sense.get('partOfSpeech', []))
                if particle_glosses:
                    _merge(out[word], 'pg', particle_glosses)
            else:
                # Uncommon entry skipped for g/p, but collect its grammar glosses.
                # If the common entry already has pg (competing senses, e.g. て/で), store
                # in pg2 so callers can distinguish. Otherwise merge into pg — no conflict.
                if particle_glosses:
                    _merge(out[word], 'pg2' if 'pg' in out[word] else 'pg', particle_glosses)

    return out


def write_dict(out: dict[str, dict[str, Any]], output: Path) -> None:
    """Write dictionary to a gzipped JSON file.

    Uses atomic write with a temporary file to avoid partial writes.

    Args:
        out: The dictionary data to write
        output: Path where the output file should be written

    Raises:
        ValueError: If the output dictionary is empty
    """
    data = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    json_size = len(data.encode()) / 1024 / 1024
    print(f'{output.name}: entries={len(out)}, JSON={json_size:.1f}MB')

    if len(out) == 0:
        raise ValueError(f'{output.name}: generated dictionary is empty')

    output.parent.mkdir(exist_ok=True)
    tmp_output: Path | None = None
    try:
        with tempfile.NamedTemporaryFile('wb', dir=output.parent, prefix=f'.{output.name}.', suffix='.tmp', delete=False) as f:
            tmp_output = Path(f.name)
            f.write(zopfli.gzip.compress(data.encode('utf-8')))
        # os.replace is atomic on POSIX systems (Linux, macOS)
        os.replace(tmp_output, output)
    finally:
        if tmp_output and tmp_output.exists():
            try:
                tmp_output.unlink()
            except OSError:
                pass

    gzipped_size = os.path.getsize(output) / 1024 / 1024
    print(f'{output.name}: gzipped={gzipped_size:.1f}MB')


# Find and load source file
matches = sorted(glob.glob('jmdict-eng-*.json.zip'))
if not matches:
    raise FileNotFoundError("No jmdict-eng-*.json.zip found in current directory.")
source = matches[-1]
print(f"Loading {source}...")
with zipfile.ZipFile(source) as zf:
    d = json.load(zf.open(zf.namelist()[0]))

if not d.get('words'):
    raise ValueError('Source file contains no words')
print(f"Loaded {len(d['words'])} entries from {source}")

# Build and write both dictionary modes
write_dict(build_dict(common_only=True), Path('dict') / 'jmdict-ultra-compact.json.gz')
write_dict(build_dict(), Path('dict') / 'jmdict-full.json.gz')
print('Done')
