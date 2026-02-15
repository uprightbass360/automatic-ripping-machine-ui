"""Test data factories for ARM models."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from backend.models.arm import Config, Job, SystemDrives, Track


def make_job(**overrides) -> MagicMock:
    """Return a MagicMock(spec=Job) with realistic defaults."""
    defaults = {
        "job_id": 1,
        "arm_version": "2.8.0",
        "crc_id": "abc123",
        "logfile": "job_1.log",
        "start_time": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        "stop_time": None,
        "job_length": "01:30:00",
        "status": "active",
        "stage": "rip",
        "no_of_titles": 5,
        "title": "Test Movie",
        "title_auto": "Test Movie",
        "title_manual": None,
        "year": "2024",
        "year_auto": "2024",
        "year_manual": None,
        "video_type": "movie",
        "video_type_auto": "movie",
        "video_type_manual": None,
        "imdb_id": "tt1234567",
        "imdb_id_auto": None,
        "imdb_id_manual": None,
        "poster_url": "https://example.com/poster.jpg",
        "poster_url_auto": None,
        "poster_url_manual": None,
        "devpath": "/dev/sr0",
        "mountpoint": "/mnt/dev/sr0",
        "hasnicetitle": True,
        "errors": None,
        "disctype": "dvd",
        "label": "TEST_MOVIE",
        "path": "/home/arm/media/Test Movie (2024)",
        "raw_path": "/home/arm/raw/Test Movie (2024)",
        "transcode_path": "/home/arm/transcode",
        "ejected": False,
        "updated": False,
        "pid": 12345,
        "pid_hash": 67890,
        "tracks": [],
        "config": None,
    }
    defaults.update(overrides)
    mock = MagicMock(spec=Job)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def make_track(**overrides) -> MagicMock:
    """Return a MagicMock(spec=Track) with realistic defaults."""
    defaults = {
        "track_id": 1,
        "job_id": 1,
        "track_number": "1",
        "length": 5400,
        "aspect_ratio": "16:9",
        "fps": 23.976,
        "main_feature": True,
        "basename": "title_t01",
        "filename": "title_t01.mkv",
        "orig_filename": "title_t01.mkv",
        "new_filename": "Test Movie (2024).mkv",
        "ripped": True,
        "status": "success",
        "error": None,
        "source": "/dev/sr0",
    }
    defaults.update(overrides)
    mock = MagicMock(spec=Track)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock


def make_config(**overrides) -> Config:
    """Return a real Config() instance (needed for __table__.columns iteration)."""
    defaults = {
        "CONFIG_ID": 1,
        "job_id": 1,
        "RIPMETHOD": "mkv",
        "MAINFEATURE": "false",
        "MINLENGTH": "600",
        "MAXLENGTH": "99999",
        "VIDEOTYPE": "auto",
        "ARM_CHECK_UDF": "true",
        "GET_VIDEO_TITLE": "true",
        "SKIP_TRANSCODE": "false",
        "MANUAL_WAIT": "true",
        "MANUAL_WAIT_TIME": "60",
        "RAW_PATH": "/home/arm/raw",
        "TRANSCODE_PATH": "/home/arm/transcode",
        "COMPLETED_PATH": "/home/arm/completed",
        "EXTRAS_SUB": "extras",
        "INSTALLPATH": "/opt/arm",
        "LOGPATH": "/home/arm/logs",
        "LOGLEVEL": "DEBUG",
        "LOGLIFE": "1",
        "DBFILE": "/home/arm/db/arm.db",
        "WEBSERVER_IP": "0.0.0.0",
        "WEBSERVER_PORT": "8080",
        "SET_MEDIA_PERMISSIONS": "false",
        "CHMOD_VALUE": "777",
        "SET_MEDIA_OWNER": "false",
        "CHOWN_USER": "arm",
        "CHOWN_GROUP": "arm",
        "MKV_ARGS": "",
        "DELRAWFILES": "true",
        "HASHEDKEYS": "",
        "HB_PRESET_DVD": "HQ 480p30 Surround",
        "HB_PRESET_BD": "HQ 1080p30 Surround",
        "DEST_EXT": "mkv",
        "HANDBRAKE_CLI": "HandBrakeCLI",
        "HB_ARGS_DVD": "",
        "HB_ARGS_BD": "",
        "EMBY_REFRESH": "false",
        "EMBY_SERVER": "",
        "EMBY_PORT": "8096",
        "NOTIFY_RIP": "true",
        "NOTIFY_TRANSCODE": "true",
        "MAX_CONCURRENT_TRANSCODES": "1",
        # Sensitive fields
        "EMBY_API_KEY": "secret_emby_key",
        "IFTTT_KEY": "secret_ifttt",
        "PB_KEY": "secret_pb",
        "OMDB_API_KEY": "secret_omdb",
        "TMDB_API_KEY": "secret_tmdb",
        "PO_USER_KEY": "secret_po_user",
        "PO_APP_KEY": "secret_po_app",
        "APPRISE": "tgram://secret_token",
    }
    defaults.update(overrides)
    config = Config()
    for k, v in defaults.items():
        setattr(config, k, v)
    return config


def make_drive(**overrides) -> MagicMock:
    """Return a MagicMock(spec=SystemDrives) with realistic defaults."""
    defaults = {
        "drive_id": 1,
        "name": "BD Drive 1",
        "mount": "/mnt/dev/sr0",
        "job_id_current": None,
        "job_id_previous": None,
        "description": "Primary Blu-ray drive",
        "drive_mode": "auto",
        "maker": "LG",
        "model": "WH16NS60",
        "serial": "ABC123",
        "connection": "SATA",
        "read_cd": True,
        "read_dvd": True,
        "read_bd": True,
        "firmware": "1.02",
        "location": "0:0:0:0",
        "stale": False,
        "mdisc": 0,
        "serial_id": "lg-wh16ns60-abc123",
    }
    defaults.update(overrides)
    mock = MagicMock(spec=SystemDrives)
    for k, v in defaults.items():
        setattr(mock, k, v)
    return mock
