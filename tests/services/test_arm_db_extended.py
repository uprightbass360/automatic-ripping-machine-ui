"""Tests for arm_db: retranscode info, transcode overrides, track updates."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.services import arm_db
from tests.factories import make_job, make_track


# --- _coerce_override ---


def test_coerce_override_video_quality():
    assert arm_db._coerce_override("video_quality", "22") == ("video_quality", 22)


def test_coerce_override_delete_source_bool():
    assert arm_db._coerce_override("delete_source", True) == ("delete_source", True)


def test_coerce_override_delete_source_string():
    assert arm_db._coerce_override("delete_source", "yes") == ("delete_source", True)
    assert arm_db._coerce_override("delete_source", "false") == ("delete_source", False)


def test_coerce_override_delete_source_int():
    assert arm_db._coerce_override("delete_source", 1) == ("delete_source", True)
    assert arm_db._coerce_override("delete_source", 0) == ("delete_source", False)


def test_coerce_override_string_field():
    assert arm_db._coerce_override("video_encoder", "x265") == ("video_encoder", "x265")


def test_coerce_override_none_skipped():
    assert arm_db._coerce_override("video_encoder", None) is None


def test_coerce_override_empty_string_skipped():
    assert arm_db._coerce_override("video_encoder", "") is None


# --- get_job_retranscode_info ---


def test_retranscode_info_basic():
    job = make_job(
        job_id=1, title="Matrix", year="1999", disctype="dvd",
        video_type="movie", raw_path="/raw/Matrix",
        poster_url="https://poster.jpg", transcode_overrides=None,
        multi_title=False,
    )
    job.tracks = []
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job_retranscode_info(1)

    assert result is not None
    assert result["title"] == "Matrix"
    assert result["path"] == "/raw/Matrix"
    assert result["status"] == "success"


def test_retranscode_info_not_found():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = None
        mock_session.return_value = ctx
        result = arm_db.get_job_retranscode_info(999)

    assert result is None


def test_retranscode_info_music_disc_returns_none():
    job = make_job(job_id=1, disctype="music")
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job_retranscode_info(1)

    assert result is None


def test_retranscode_info_with_overrides():
    job = make_job(
        job_id=1, disctype="bluray",
        transcode_overrides='{"video_encoder": "x265", "video_quality": 20}',
        multi_title=False,
    )
    job.tracks = []
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job_retranscode_info(1)

    assert result is not None
    assert result["config_overrides"]["video_encoder"] == "x265"


def test_retranscode_info_multi_title_with_tracks():
    track1 = make_track(track_number="1", title="Chapter 1", year="2020",
                        video_type="movie", filename="ch1.mkv")
    track2 = make_track(track_number="2", title=None, filename="ch2.mkv")
    job = make_job(
        job_id=1, disctype="bluray", multi_title=True,
        transcode_overrides=None,
    )
    job.tracks = [track1, track2]

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job_retranscode_info(1)

    assert result is not None
    assert result["multi_title"] is True
    assert len(result["tracks"]) == 1  # only track with title
    assert result["tracks"][0]["title"] == "Chapter 1"


# --- update_job_transcode_overrides ---


def test_update_transcode_overrides_invalid_keys():
    with pytest.raises(ValueError, match="Unknown keys"):
        arm_db.update_job_transcode_overrides(1, {"bad_key": "value"})


def test_update_transcode_overrides_success():
    mock_job = MagicMock()
    with patch.object(arm_db, "get_rw_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = mock_job
        mock_session.return_value = ctx
        result = arm_db.update_job_transcode_overrides(
            1, {"video_encoder": "x265", "video_quality": "20"}
        )

    assert result is not None
    assert result["video_encoder"] == "x265"
    assert result["video_quality"] == 20


def test_update_transcode_overrides_not_found():
    with patch.object(arm_db, "get_rw_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = None
        mock_session.return_value = ctx
        result = arm_db.update_job_transcode_overrides(
            999, {"video_encoder": "x265"}
        )

    assert result is None


# --- update_track_fields ---


def test_update_track_fields_invalid_keys():
    with pytest.raises(ValueError, match="Unknown fields"):
        arm_db.update_track_fields(1, 1, {"bad_field": "value"})


def test_update_track_fields_empty():
    with pytest.raises(ValueError, match="No fields"):
        arm_db.update_track_fields(1, 1, {})


def test_update_track_fields_bool_coercion():
    mock_track = MagicMock()
    with patch.object(arm_db, "get_rw_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.first.return_value = mock_track
        mock_session.return_value = ctx
        result = arm_db.update_track_fields(1, 1, {"enabled": "true"})

    assert result is not None
    assert result["enabled"] is True


def test_update_track_fields_not_found():
    with patch.object(arm_db, "get_rw_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.first.return_value = None
        mock_session.return_value = ctx
        result = arm_db.update_track_fields(1, 99, {"enabled": True})

    assert result is None
