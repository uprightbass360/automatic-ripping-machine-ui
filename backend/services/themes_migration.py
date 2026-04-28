"""One-shot first-boot migration for user themes.

Before v17.x.x, arm-ui themes lived at ``/data/config/themes`` - a path
bind-mounted from arm-neu's config directory. After the bind-mount is
retired in favor of a UI-owned named volume mounted at ``/data/themes``,
operators upgrading in place still have their existing theme files at the
old path. This module copies them over on first boot.

Idempotent: only copies if the destination directory is empty. Safe to
run on every startup; effectively a no-op after the first successful
migration.
"""
import logging
import shutil
from pathlib import Path

log = logging.getLogger(__name__)

_LEGACY_THEMES_DIR = Path("/data/config/themes")


def migrate_legacy_themes(themes_path: str) -> int:
    """Copy theme files from the legacy bind-mount location to the new volume.

    Returns the number of files migrated (0 if nothing to do).
    """
    target = Path(themes_path)

    # Only run if the target is empty (or doesn't exist) - otherwise the
    # operator has already been on the new layout and we'd risk overwriting
    # their authoritative files.
    if target.is_dir() and any(target.iterdir()):
        return 0

    if not _LEGACY_THEMES_DIR.is_dir():
        return 0

    target.mkdir(parents=True, exist_ok=True)
    migrated = 0
    for entry in _LEGACY_THEMES_DIR.iterdir():
        if entry.is_file() and entry.suffix in (".json", ".css"):
            try:
                shutil.copy2(entry, target / entry.name)
                migrated += 1
            except OSError as exc:
                log.warning("Failed to migrate theme file %s: %s", entry.name, exc)

    if migrated:
        log.info(
            "Migrated %d theme file(s) from legacy %s to %s. "
            "You can safely remove the old bind mount from your compose file.",
            migrated, _LEGACY_THEMES_DIR, target,
        )
    return migrated
