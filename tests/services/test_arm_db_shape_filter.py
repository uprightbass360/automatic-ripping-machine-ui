"""Tests for transcode_overrides shape filtering in arm_db.get_job_retranscode_info.

Old-shape keys (pre-preset-rollout flat keys like video_encoder,
handbrake_preset*) must be stripped on read with a WARN log. Allowlist:
{preset_slug, overrides, delete_source, output_extension}.

Belt-and-braces guard: the arm-neu Alembic migration NULLs old-shape rows
on upgrade, but rollback, snapshot-restore, or future shape drift could
reintroduce them. This filter strips unknown keys on read so the UI and
the transcoder never see shapes the transcoder can't interpret.
"""

from __future__ import annotations

import json
import logging
from unittest.mock import MagicMock, patch

from backend.services import arm_db
from tests.factories import make_job


def _patched_session(job):
    """Build a context-manager mock for arm_db.get_session returning `job`."""
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=ctx)
    ctx.__exit__ = MagicMock(return_value=False)
    ctx.scalars.return_value.unique.return_value.first.return_value = job
    return ctx


def test_old_shape_keys_stripped_with_warning(caplog):
    """Legacy flat keys are removed from config_overrides; WARN names them."""
    old_shape = {
        "video_encoder": "nvenc_h265",
        "handbrake_preset": "Foo",
        "handbrake_preset_dvd": "Bar",
        "preset_slug": "nvidia_balanced",  # keep this one
    }
    job = make_job(
        job_id=42, disctype="bluray",
        transcode_overrides=json.dumps(old_shape),
        multi_title=False,
    )
    job.tracks = []

    with patch.object(arm_db, "get_session", return_value=_patched_session(job)), \
         caplog.at_level(logging.WARNING, logger="backend.services.arm_db"):
        result = arm_db.get_job_retranscode_info(42)

    assert result is not None
    config_overrides = result["config_overrides"]
    assert config_overrides == {"preset_slug": "nvidia_balanced"}
    assert "video_encoder" not in config_overrides
    assert "handbrake_preset" not in config_overrides
    assert "handbrake_preset_dvd" not in config_overrides

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings, "expected a WARN log naming stripped keys"
    messages = "\n".join(r.getMessage() for r in warnings)
    assert "42" in messages, "WARN must reference the job_id"
    assert "video_encoder" in messages
    assert "handbrake_preset" in messages


def test_new_shape_unchanged(caplog):
    """Pure new-shape values pass through untouched with no WARN."""
    new_shape = {
        "preset_slug": "amd_balanced",
        "overrides": {"shared": {"video_quality": 20}},
        "delete_source": True,
        "output_extension": "mkv",
    }
    job = make_job(
        job_id=7, disctype="dvd",
        transcode_overrides=json.dumps(new_shape),
        multi_title=False,
    )
    job.tracks = []

    with patch.object(arm_db, "get_session", return_value=_patched_session(job)), \
         caplog.at_level(logging.WARNING, logger="backend.services.arm_db"):
        result = arm_db.get_job_retranscode_info(7)

    assert result is not None
    assert result["config_overrides"] == new_shape

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == [], (
        "no WARN logs expected for pure new-shape values; got: "
        + "; ".join(r.getMessage() for r in warnings)
    )


def test_null_transcode_overrides_no_warning(caplog):
    """NULL column yields config_overrides=None with no WARN."""
    job = make_job(
        job_id=3, disctype="dvd",
        transcode_overrides=None,
        multi_title=False,
    )
    job.tracks = []

    with patch.object(arm_db, "get_session", return_value=_patched_session(job)), \
         caplog.at_level(logging.WARNING, logger="backend.services.arm_db"):
        result = arm_db.get_job_retranscode_info(3)

    assert result is not None
    assert result["config_overrides"] is None

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


def test_malformed_json_returns_none_with_warning(caplog):
    """Malformed JSON does not raise; config_overrides falls back to None + WARN."""
    job = make_job(
        job_id=9, disctype="bluray",
        transcode_overrides="not valid json {",
        multi_title=False,
    )
    job.tracks = []

    with patch.object(arm_db, "get_session", return_value=_patched_session(job)), \
         caplog.at_level(logging.WARNING, logger="backend.services.arm_db"):
        result = arm_db.get_job_retranscode_info(9)

    assert result is not None
    assert result["config_overrides"] is None

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) >= 1
    messages = "\n".join(r.getMessage() for r in warnings)
    assert "9" in messages, "WARN should reference the job_id"


def test_non_dict_json_returns_none_with_warning(caplog):
    """JSON value that isn't an object (e.g. list) is treated as malformed."""
    job = make_job(
        job_id=11, disctype="bluray",
        transcode_overrides=json.dumps(["not", "a", "dict"]),
        multi_title=False,
    )
    job.tracks = []

    with patch.object(arm_db, "get_session", return_value=_patched_session(job)), \
         caplog.at_level(logging.WARNING, logger="backend.services.arm_db"):
        result = arm_db.get_job_retranscode_info(11)

    assert result is not None
    assert result["config_overrides"] is None

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) >= 1


def test_allowlist_matches_migration_shape():
    """Constant must match the arm-neu migration's 4-key allowlist."""
    expected = frozenset({"preset_slug", "overrides", "delete_source", "output_extension"})
    assert frozenset(arm_db.TRANSCODE_OVERRIDES_ALLOWLIST) == expected
