#!/usr/bin/env bash
# Tag the release and push to prod.
# Usage: scripts/tag_and_push.sh

set -euo pipefail

cd "$(dirname "$0")/.."

# Extract version from index.html subtitle (e.g., "v1.14.0")
VERSION=$(grep "subtitle.*v" index.html | grep -oP 'v[0-9]+\.[0-9]+\.[0-9]+')

# Extract cache bust version from dictionary fetch URLs (e.g., "14" from "v=14")
CACHE_BUSTS=$(grep -oP 'dict/jmdict-[^"'"'"']+\.json\.gz\?v=\K[0-9]+' index.html | sort -u)

# Verify all cache bust versions are identical
NUM_UNIQUE=$(echo "$CACHE_BUSTS" | wc -l)
if [[ $NUM_UNIQUE -ne 1 ]]; then
  echo "Error: Multiple different cache bust versions found:"
  echo "$CACHE_BUSTS"
  exit 1
fi

# Extract minor version number (e.g., "14" from "v1.14.0")
VERSION_MINOR=$(echo "$VERSION" | grep -oP 'v[0-9]+\.\K[0-9]+')

# Check if versions match (cache bust uses minor version)
if [[ "$CACHE_BUSTS" != "$VERSION_MINOR" ]]; then
  echo "Error: Version mismatch!"
  echo "  index.html subtitle: $VERSION (minor: $VERSION_MINOR)"
  echo "  cache bust version: $CACHE_BUSTS"
  exit 1
fi

echo "Version $VERSION matches cache bust v=$CACHE_BUSTS"

# Check if tag already exists
if git rev-parse "$VERSION" >/dev/null 2>&1; then
  echo "Error: Tag $VERSION already exists"
  exit 1
fi

# Create tag and push
echo "Creating tag $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"
echo "Pushing HEAD:main to prod (triggers Pages build)..."
git push prod HEAD:main --force
echo "Waiting for GitHub Pages to register the commit..."
sleep 5
echo "Pushing tags to prod..."
git push prod --tags --no-verify
echo "Done! Released $VERSION"
