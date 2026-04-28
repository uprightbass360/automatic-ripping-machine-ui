"""Tests for the one-shot legacy themes migration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from backend.services import themes_migration


def test_no_legacy_dir_no_op(tmp_path):
    target = tmp_path / "themes"
    with patch.object(themes_migration, "_LEGACY_THEMES_DIR", tmp_path / "missing"):
        copied = themes_migration.migrate_legacy_themes(str(target))
    assert copied == 0
    # Target wasn't created either - nothing to migrate, so don't make it.
    assert not target.exists()


def test_target_already_populated_no_op(tmp_path):
    target = tmp_path / "themes"
    target.mkdir()
    (target / "existing.json").write_text("{}")

    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "old.json").write_text(json.dumps({"id": "old", "label": "Old", "tokens": {}}))

    with patch.object(themes_migration, "_LEGACY_THEMES_DIR", legacy):
        copied = themes_migration.migrate_legacy_themes(str(target))
    assert copied == 0
    # The pre-existing file is unchanged; the legacy file did NOT overwrite anything.
    assert (target / "existing.json").exists()
    assert not (target / "old.json").exists()


def test_copies_json_and_css_from_legacy(tmp_path):
    target = tmp_path / "themes"
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "dark.json").write_text(json.dumps({"id": "dark", "label": "Dark", "tokens": {}}))
    (legacy / "dark.css").write_text("body{}")
    # README.md should NOT be copied
    (legacy / "README.md").write_text("docs")

    with patch.object(themes_migration, "_LEGACY_THEMES_DIR", legacy):
        copied = themes_migration.migrate_legacy_themes(str(target))
    assert copied == 2
    assert (target / "dark.json").exists()
    assert (target / "dark.css").exists()
    assert not (target / "README.md").exists()


def test_idempotent_after_first_run(tmp_path):
    target = tmp_path / "themes"
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "dark.json").write_text(json.dumps({"id": "dark", "label": "Dark", "tokens": {}}))

    with patch.object(themes_migration, "_LEGACY_THEMES_DIR", legacy):
        first = themes_migration.migrate_legacy_themes(str(target))
        second = themes_migration.migrate_legacy_themes(str(target))
    assert first == 1
    # Second call sees populated target, does nothing.
    assert second == 0


def test_logs_and_skips_when_copy_fails(tmp_path, caplog):
    """A single corrupt/unreadable file is logged and skipped; siblings still copy."""
    target = tmp_path / "themes"
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "good.json").write_text(json.dumps({"id": "g", "label": "G", "tokens": {}}))
    (legacy / "bad.json").write_text(json.dumps({"id": "b", "label": "B", "tokens": {}}))

    real_copy = themes_migration.shutil.copy2

    def fail_for_bad(src, dst, *args, **kwargs):
        if Path(src).name == "bad.json":
            raise OSError("simulated EACCES")
        return real_copy(src, dst, *args, **kwargs)

    with patch.object(themes_migration, "_LEGACY_THEMES_DIR", legacy), \
         patch.object(themes_migration.shutil, "copy2", side_effect=fail_for_bad), \
         caplog.at_level("WARNING", logger=themes_migration.log.name):
        copied = themes_migration.migrate_legacy_themes(str(target))

    assert copied == 1
    assert (target / "good.json").exists()
    assert not (target / "bad.json").exists()
    assert any("bad.json" in rec.message and "simulated" in rec.message for rec in caplog.records)
