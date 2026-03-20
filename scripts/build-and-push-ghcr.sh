#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is required but not found in PATH." >&2
  exit 1
fi

if [[ ! -f VERSION ]]; then
  echo "Error: VERSION file not found. Run this script from repo root." >&2
  exit 1
fi

if [[ -z "${GHCR_TOKEN:-}" ]]; then
  echo "Error: GHCR_TOKEN is not set." >&2
  echo "Set it first, for example: export GHCR_TOKEN=ghp_xxx" >&2
  exit 1
fi

OWNER="${GHCR_OWNER:-jakespocket}"
IMAGE_NAME="${GHCR_IMAGE_NAME:-arm-ui}"
IMAGE="ghcr.io/${OWNER,,}/${IMAGE_NAME}"
VERSION_TAG="$(tr -d '[:space:]' < VERSION)"
BUILDER_NAME="${BUILDX_BUILDER_NAME:-arm-ui-builder}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

echo "$GHCR_TOKEN" | docker login ghcr.io -u "$OWNER" --password-stdin

if ! docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1; then
  docker buildx create --name "$BUILDER_NAME" --use >/dev/null
else
  docker buildx use "$BUILDER_NAME"
fi

docker buildx build \
  --platform "$PLATFORMS" \
  --tag "${IMAGE}:${VERSION_TAG}" \
  --tag "${IMAGE}:latest" \
  --push \
  .

echo "Pushed:"
echo "  ${IMAGE}:${VERSION_TAG}"
echo "  ${IMAGE}:latest"
