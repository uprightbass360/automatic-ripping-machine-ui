"""Tests for arm_db: get_drives_with_jobs, get_all_config_safe, get_job, is_available, etc."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.models.arm import Config, HIDDEN_CONFIG_FIELDS, Job, SystemDrives
from backend.services import arm_db

from tests.factories import make_config, make_drive, make_job, make_track


# --- is_available ---


def test_is_available_success():
    """is_available returns True when DB is reachable."""
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        mock_session.return_value = ctx
        result = arm_db.is_available()
    assert result is True


def test_is_available_failure():
    """is_available returns False when DB raises exception."""
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.execute.side_effect = Exception("DB unavailable")
        mock_session.return_value = ctx
        # Force it to try and fail
        mock_session.side_effect = Exception("connection refused")
        result = arm_db.is_available()
    assert result is False


# --- get_job ---


def test_get_job_success():
    job = make_job(job_id=42)
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job(42)
    assert result is not None
    assert result.job_id == 42


def test_get_job_not_found():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = None
        mock_session.return_value = ctx
        result = arm_db.get_job(999)
    assert result is None


def test_get_job_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_job(1)
    assert result is None


# --- get_job_with_config ---


def test_get_job_with_config_success():
    config = make_config(RIPMETHOD="mkv")
    job = make_job(job_id=1, config=config)
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result_job, result_config = arm_db.get_job_with_config(1)
    assert result_job is not None
    assert result_config is not None
    assert result_config["RIPMETHOD"] == "mkv"


def test_get_job_with_config_not_found():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = None
        mock_session.return_value = ctx
        result_job, result_config = arm_db.get_job_with_config(999)
    assert result_job is None
    assert result_config is None


def test_get_job_with_config_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result_job, result_config = arm_db.get_job_with_config(1)
    assert result_job is None
    assert result_config is None


# --- get_job_config_safe ---


def test_get_job_config_safe_with_config():
    config = make_config(RIPMETHOD="mkv", OMDB_API_KEY="secret")
    job = make_job(config=config)
    result = arm_db.get_job_config_safe(job)
    assert result is not None
    assert result["RIPMETHOD"] == "mkv"
    assert result["OMDB_API_KEY"] == "***"


def test_get_job_config_safe_none_config():
    job = make_job(config=None)
    result = arm_db.get_job_config_safe(job)
    assert result is None


# --- get_active_jobs ---


def test_get_active_jobs_success():
    track1 = make_track(ripped=True)
    track2 = make_track(ripped=False)
    job = MagicMock(spec=Job)
    # Set up __table__.columns to return realistic columns
    job.__table__ = Job.__table__
    for col in Job.__table__.columns:
        setattr(job, col.name, None)
    job.job_id = 1
    job.status = "active"
    job.tracks = [track1, track2]

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.all.return_value = [job]
        mock_session.return_value = ctx
        result = arm_db.get_active_jobs()

    assert len(result) == 1
    assert result[0]["tracks_total"] == 2
    assert result[0]["tracks_ripped"] == 1


def test_get_active_jobs_empty():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.all.return_value = []
        mock_session.return_value = ctx
        result = arm_db.get_active_jobs()
    assert result == []


def test_get_active_jobs_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_active_jobs()
    assert result == []


# --- get_job_track_counts ---


def test_get_job_track_counts_success():
    track1 = make_track(ripped=True)
    track2 = make_track(ripped=False)
    track3 = make_track(ripped=True)
    job = make_job(job_id=1)
    job.tracks = [track1, track2, track3]

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job_track_counts(1)

    assert result["tracks_total"] == 3
    assert result["tracks_ripped"] == 2


def test_get_job_track_counts_not_found():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = None
        mock_session.return_value = ctx
        result = arm_db.get_job_track_counts(999)
    assert result == {"tracks_total": 0, "tracks_ripped": 0}


def test_get_job_track_counts_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_job_track_counts(1)
    assert result == {"tracks_total": 0, "tracks_ripped": 0}


def test_get_job_track_counts_no_tracks():
    job = make_job(job_id=1)
    job.tracks = None
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.unique.return_value.first.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_job_track_counts(1)
    assert result == {"tracks_total": 0, "tracks_ripped": 0}


# --- get_drives_with_jobs ---


def test_get_drives_with_jobs_no_current_job():
    drive = MagicMock(spec=SystemDrives)
    drive.__table__ = SystemDrives.__table__
    for col in SystemDrives.__table__.columns:
        setattr(drive, col.name, None)
    drive.drive_id = 1
    drive.name = "BD Drive"
    drive.stale = False
    drive.job_id_current = None

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.all.return_value = [drive]
        mock_session.return_value = ctx
        result = arm_db.get_drives_with_jobs()

    assert len(result) == 1
    assert result[0]["current_job"] is None


def test_get_drives_with_jobs_with_current_job():
    drive = MagicMock(spec=SystemDrives)
    drive.__table__ = SystemDrives.__table__
    for col in SystemDrives.__table__.columns:
        setattr(drive, col.name, None)
    drive.drive_id = 1
    drive.name = "BD Drive"
    drive.stale = False
    drive.job_id_current = 42

    job = MagicMock(spec=Job)
    job.__table__ = Job.__table__
    for col in Job.__table__.columns:
        setattr(job, col.name, None)
    job.job_id = 42
    job.title = "Matrix"

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.all.return_value = [drive]
        ctx.get.return_value = job
        mock_session.return_value = ctx
        result = arm_db.get_drives_with_jobs()

    assert len(result) == 1
    assert result[0]["current_job"] is not None
    assert result[0]["current_job"]["job_id"] == 42


def test_get_drives_with_jobs_filters_stale():
    drive_ok = MagicMock(spec=SystemDrives)
    drive_ok.__table__ = SystemDrives.__table__
    for col in SystemDrives.__table__.columns:
        setattr(drive_ok, col.name, None)
    drive_ok.stale = False
    drive_ok.job_id_current = None

    drive_stale = MagicMock(spec=SystemDrives)
    drive_stale.__table__ = SystemDrives.__table__
    for col in SystemDrives.__table__.columns:
        setattr(drive_stale, col.name, None)
    drive_stale.stale = True
    drive_stale.job_id_current = None

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.all.return_value = [drive_ok, drive_stale]
        mock_session.return_value = ctx
        result = arm_db.get_drives_with_jobs()

    assert len(result) == 1


def test_get_drives_with_jobs_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_drives_with_jobs()
    assert result == []


# --- get_all_config_safe ---


def test_get_all_config_safe_from_db():
    config = make_config(RIPMETHOD="mkv", OMDB_API_KEY="secret")
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.first.return_value = config
        mock_session.return_value = ctx
        result = arm_db.get_all_config_safe()

    assert result is not None
    assert result["RIPMETHOD"] == "mkv"
    assert result["OMDB_API_KEY"] == "***"
    assert "CONFIG_ID" not in result
    assert "job_id" not in result


def test_get_all_config_safe_no_db_falls_back_to_yaml(tmp_path):
    yaml_file = tmp_path / "arm.yaml"
    yaml_file.write_text("RIPMETHOD: mkv\nOMDB_API_KEY: real_key\n")

    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.first.return_value = None
        mock_session.return_value = ctx
        with patch.object(arm_db.settings, "arm_config_path", str(yaml_file)):
            result = arm_db.get_all_config_safe()

    assert result is not None
    assert result["RIPMETHOD"] == "mkv"
    assert result["OMDB_API_KEY"] == "***"


def test_get_all_config_safe_db_exception_falls_back_to_yaml(tmp_path):
    yaml_file = tmp_path / "arm.yaml"
    yaml_file.write_text("RIPMETHOD: backup\n")

    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        with patch.object(arm_db.settings, "arm_config_path", str(yaml_file)):
            result = arm_db.get_all_config_safe()

    assert result is not None
    assert result["RIPMETHOD"] == "backup"


def test_get_all_config_safe_both_fail():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        with patch.object(arm_db.settings, "arm_config_path", ""):
            result = arm_db.get_all_config_safe()
    assert result is None


# --- get_ripping_paused ---


def test_get_ripping_paused_true():
    state = MagicMock()
    state.ripping_paused = True
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = state
        mock_session.return_value = ctx
        result = arm_db.get_ripping_paused()
    assert result is True


def test_get_ripping_paused_false():
    state = MagicMock()
    state.ripping_paused = False
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = state
        mock_session.return_value = ctx
        result = arm_db.get_ripping_paused()
    assert result is False


def test_get_ripping_paused_no_state():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.get.return_value = None
        mock_session.return_value = ctx
        result = arm_db.get_ripping_paused()
    assert result is False


def test_get_ripping_paused_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_ripping_paused()
    assert result is False


# --- get_notifications ---


def test_get_notifications_success():
    notif = MagicMock()
    notif.cleared = False
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.all.return_value = [notif]
        mock_session.return_value = ctx
        result = arm_db.get_notifications()
    assert len(result) == 1


def test_get_notifications_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_notifications()
    assert result == []


# --- get_notification_count ---


def test_get_notification_count_success():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalar.return_value = 5
        mock_session.return_value = ctx
        result = arm_db.get_notification_count()
    assert result == 5


def test_get_notification_count_none():
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalar.return_value = None
        mock_session.return_value = ctx
        result = arm_db.get_notification_count()
    assert result == 0


def test_get_notification_count_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_notification_count()
    assert result == 0


# --- _read_arm_yaml edge cases ---


def test_read_arm_yaml_non_dict_content(tmp_path):
    """Returns None when yaml content is not a dict (e.g. a list)."""
    yaml_file = tmp_path / "arm.yaml"
    yaml_file.write_text("- item1\n- item2\n")
    with patch.object(arm_db.settings, "arm_config_path", str(yaml_file)):
        result = arm_db._read_arm_yaml()
    assert result is None


def test_read_arm_yaml_invalid_yaml(tmp_path):
    """Returns None on yaml parse error."""
    yaml_file = tmp_path / "arm.yaml"
    yaml_file.write_text("{{invalid yaml::\n")
    with patch.object(arm_db.settings, "arm_config_path", str(yaml_file)):
        result = arm_db._read_arm_yaml()
    assert result is None


# --- get_system_info ---


def test_get_system_info_success():
    info = MagicMock()
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.first.return_value = info
        mock_session.return_value = ctx
        result = arm_db.get_system_info()
    assert result is info


def test_get_system_info_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_system_info()
    assert result is None


# --- get_drives ---


def test_get_drives_success():
    drive = make_drive()
    with patch.object(arm_db, "get_session") as mock_session:
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        ctx.scalars.return_value.all.return_value = [drive]
        mock_session.return_value = ctx
        result = arm_db.get_drives()
    assert len(result) == 1


def test_get_drives_exception():
    with patch.object(arm_db, "get_session") as mock_session:
        mock_session.side_effect = Exception("DB error")
        result = arm_db.get_drives()
    assert result == []
