#!/bin/bash
# Fetch the latest commit hash from GitHub for the main branch and write to src/lib/github-commit.ts
# Requires: jq

OWNER="thinglabsoss"
REPO="automatic-ripping-machine-ui"
BRANCH="main"

COMMIT=$(curl -s "https://api.github.com/repos/$OWNER/$REPO/commits/$BRANCH" | jq -r .sha | cut -c1-7)
echo "export const GITHUB_COMMIT = '$COMMIT';" > ../src/lib/github-commit.ts
echo "Fetched GitHub commit: $COMMIT"
