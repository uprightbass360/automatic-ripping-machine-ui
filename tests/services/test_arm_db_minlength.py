"""Tests for _minlength and _rippable_tracks helpers in backend.services.arm_db."""

from __future__ import annotations

from backend.services.arm_db import _minlength, _rippable_tracks

from tests.factories import make_config, make_job, make_track


# --- _minlength ---


def test_minlength_reads_config_value():
    """MINLENGTH is parsed from the job's config."""
    config = make_config(MINLENGTH="600")
    job = make_job(config=config)
    assert _minlength(job) == 600


def test_minlength_no_config_returns_zero():
    """Job with no config defaults to 0."""
    job = make_job(config=None)
    assert _minlength(job) == 0


def test_minlength_invalid_string_returns_zero():
    """Non-numeric MINLENGTH falls back to 0."""
    config = make_config(MINLENGTH="not_a_number")
    job = make_job(config=config)
    assert _minlength(job) == 0


def test_minlength_empty_string_returns_zero():
    """Empty MINLENGTH string falls back to 0."""
    config = make_config(MINLENGTH="")
    job = make_job(config=config)
    assert _minlength(job) == 0


def test_minlength_none_value_returns_zero():
    """MINLENGTH=None falls back to 0."""
    config = make_config(MINLENGTH=None)
    job = make_job(config=config)
    assert _minlength(job) == 0


# --- _rippable_tracks ---


def test_rippable_tracks_filters_short_tracks():
    """Tracks below MINLENGTH are excluded."""
    config = make_config(MINLENGTH="600")
    long_track = make_track(track_id=1, length=7200)
    short_track = make_track(track_id=2, length=300)
    job = make_job(config=config, tracks=[long_track, short_track])
    result = _rippable_tracks(job)
    assert len(result) == 1
    assert result[0].track_id == 1


def test_rippable_tracks_skips_minlength_for_music():
    """Music discs return ALL tracks regardless of MINLENGTH."""
    config = make_config(MINLENGTH="600")
    track1 = make_track(track_id=1, length=200)
    track2 = make_track(track_id=2, length=180)
    track3 = make_track(track_id=3, length=250)
    job = make_job(config=config, tracks=[track1, track2, track3], disctype="music")
    result = _rippable_tracks(job)
    assert len(result) == 3


def test_rippable_tracks_keeps_none_length():
    """Tracks with length=None are kept (not filtered)."""
    config = make_config(MINLENGTH="600")
    normal_track = make_track(track_id=1, length=7200)
    unknown_track = make_track(track_id=2, length=None)
    job = make_job(config=config, tracks=[normal_track, unknown_track])
    result = _rippable_tracks(job)
    assert len(result) == 2


def test_rippable_tracks_no_config_returns_all():
    """Job with no config returns all tracks (minlength=0)."""
    t1 = make_track(track_id=1, length=100)
    t2 = make_track(track_id=2, length=7200)
    job = make_job(config=None, tracks=[t1, t2])
    result = _rippable_tracks(job)
    assert len(result) == 2


def test_rippable_tracks_invalid_minlength_returns_all():
    """Job with invalid MINLENGTH string returns all tracks."""
    config = make_config(MINLENGTH="bad")
    t1 = make_track(track_id=1, length=100)
    t2 = make_track(track_id=2, length=7200)
    job = make_job(config=config, tracks=[t1, t2])
    result = _rippable_tracks(job)
    assert len(result) == 2


def test_rippable_tracks_empty_tracks():
    """Job with no tracks returns empty list."""
    config = make_config(MINLENGTH="600")
    job = make_job(config=config, tracks=[])
    result = _rippable_tracks(job)
    assert result == []


def test_rippable_tracks_none_tracks():
    """Job with tracks=None returns empty list."""
    config = make_config(MINLENGTH="600")
    job = make_job(config=config, tracks=None)
    result = _rippable_tracks(job)
    assert result == []


def test_rippable_tracks_exact_threshold_kept():
    """Track with length exactly equal to MINLENGTH is kept."""
    config = make_config(MINLENGTH="600")
    exact_track = make_track(track_id=1, length=600)
    job = make_job(config=config, tracks=[exact_track])
    result = _rippable_tracks(job)
    assert len(result) == 1
