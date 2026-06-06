#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# ///

import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

REPO = 'https://api.github.com/repos/scriptin/jmdict-simplified/releases/latest'
ROOT = Path(__file__).parent.parent


def is_fresh(path: Path) -> bool:
    """Return True if the file was modified today (after midnight local time)."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    today = datetime.now().date()
    return mtime.date() == today


BUILD = ROOT / 'build'
BUILD.mkdir(exist_ok=True)
current = sorted(BUILD.glob('jmdict-eng-*.json.zip'))
if current and is_fresh(current[-1]):
    print(f'JMdict source is fresh (downloaded today): {current[-1].name}')
    raise SystemExit(0)

print('Checking latest JMdict release...')
try:
    with urllib.request.urlopen(REPO, timeout=30) as response:
        release = json.load(response)
except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
    raise RuntimeError(f'Failed to fetch release info from {REPO}: {e}') from e

asset = next(
    (a for a in release.get('assets', []) if re.fullmatch(r'jmdict-eng-.+\.json\.zip', a.get('name', ''))),
    None,
)
if not asset:
    raise RuntimeError('Latest release has no jmdict-eng-*.json.zip asset.')

target = BUILD / asset['name']
if target.exists() and is_fresh(target):
    print(f'JMdict source is fresh (downloaded today): {target.name}')
    raise SystemExit(0)

print(f'Downloading {asset["name"]}...')
tmp = target.with_suffix(target.suffix + '.tmp')
try:
    urllib.request.urlretrieve(asset['browser_download_url'], tmp)
    tmp.replace(target)
except (urllib.error.URLError, OSError) as e:
    raise RuntimeError(f'Failed to download {asset["name"]}: {e}') from e
finally:
    if tmp.exists():
        try:
            tmp.unlink()
        except OSError:
            pass

for old in current:
    if old != target:
        old.unlink()

print(f'Done -> {target.name}')
