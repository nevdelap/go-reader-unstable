#!/usr/bin/env bash
# Tag the release and push to prod.
# Usage: scripts/tag_and_push.sh

set -euo pipefail

cd "$(dirname "$0")/.."

# Extract version from index.html subtitle (e.g., "v1.14.0")
VERSION=$(grep "subtitle.*v" index.html | grep -oP 'v[0-9]+\.[0-9]+\.[0-9]+')

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
