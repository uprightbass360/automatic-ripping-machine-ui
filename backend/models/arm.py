"""Read-only SQLAlchemy models mirroring the ARM database schema."""

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "job"

    job_id = Column(Integer, primary_key=True)
    arm_version = Column(String(20))
    crc_id = Column(String(63))
    logfile = Column(String(256))
    start_time = Column(DateTime)
    stop_time = Column(DateTime)
    job_length = Column(String(20))
    status = Column(String(32))
    stage = Column(String(64))
    no_of_titles = Column(Integer)
    title = Column(String(256))
    title_auto = Column(String(256))
    title_manual = Column(String(256))
    year = Column(String(4))
    year_auto = Column(String(4))
    year_manual = Column(String(4))
    video_type = Column(String(20))
    video_type_auto = Column(String(20))
    video_type_manual = Column(String(20))
    imdb_id = Column(String(15))
    imdb_id_auto = Column(String(15))
    imdb_id_manual = Column(String(15))
    poster_url = Column(String(256))
    poster_url_auto = Column(String(256))
    poster_url_manual = Column(String(256))
    devpath = Column(String(15))
    mountpoint = Column(String(20))
    hasnicetitle = Column(Boolean)
    errors = Column(Text)
    disctype = Column(String(20))
    label = Column(String(256))
    path = Column(String(256))
    raw_path = Column(String(256))
    transcode_path = Column(String(256))
    ejected = Column(Boolean)
    updated = Column(Boolean)
    pid = Column(Integer)
    pid_hash = Column(Integer)

    tracks = relationship("Track", back_populates="job", lazy="selectin")
    config = relationship("Config", back_populates="job", uselist=False, lazy="selectin")


class Track(Base):
    __tablename__ = "track"

    track_id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job.job_id"))
    track_number = Column(String(4))
    length = Column(Integer)
    aspect_ratio = Column(String(20))
    fps = Column(Float)
    main_feature = Column(Boolean)
    basename = Column(String(256))
    filename = Column(String(256))
    orig_filename = Column(String(256))
    new_filename = Column(String(256))
    ripped = Column(Boolean)
    status = Column(String(32))
    error = Column(Text)
    source = Column(String(256))

    job = relationship("Job", back_populates="tracks")


class Config(Base):
    __tablename__ = "config"

    CONFIG_ID = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job.job_id"))
    ARM_CHECK_UDF = Column(String(10))
    GET_VIDEO_TITLE = Column(String(10))
    SKIP_TRANSCODE = Column(String(10))
    VIDEOTYPE = Column(String(20))
    MINLENGTH = Column(String(10))
    MAXLENGTH = Column(String(10))
    MANUAL_WAIT = Column(String(10))
    MANUAL_WAIT_TIME = Column(String(10))
    RAW_PATH = Column(String(256))
    TRANSCODE_PATH = Column(String(256))
    COMPLETED_PATH = Column(String(256))
    EXTRAS_SUB = Column(String(256))
    INSTALLPATH = Column(String(256))
    LOGPATH = Column(String(256))
    LOGLEVEL = Column(String(20))
    LOGLIFE = Column(String(10))
    DBFILE = Column(String(256))
    WEBSERVER_IP = Column(String(20))
    WEBSERVER_PORT = Column(String(10))
    SET_MEDIA_PERMISSIONS = Column(String(10))
    CHMOD_VALUE = Column(String(10))
    SET_MEDIA_OWNER = Column(String(10))
    CHOWN_USER = Column(String(64))
    CHOWN_GROUP = Column(String(64))
    RIPMETHOD = Column(String(20))
    MKV_ARGS = Column(String(256))
    DELRAWFILES = Column(String(10))
    HASHEDKEYS = Column(String(256))
    HB_PRESET_DVD = Column(String(256))
    HB_PRESET_BD = Column(String(256))
    DEST_EXT = Column(String(10))
    HANDBRAKE_CLI = Column(String(256))
    MAINFEATURE = Column(String(10))
    HB_ARGS_DVD = Column(String(256))
    HB_ARGS_BD = Column(String(256))
    EMBY_REFRESH = Column(String(10))
    EMBY_SERVER = Column(String(256))
    EMBY_PORT = Column(String(10))
    NOTIFY_RIP = Column(String(10))
    NOTIFY_TRANSCODE = Column(String(10))
    MAX_CONCURRENT_TRANSCODES = Column(String(10))
    # Sensitive fields tracked for filtering
    EMBY_API_KEY = Column(String(256))
    IFTTT_KEY = Column(String(256))
    PB_KEY = Column(String(256))
    OMDB_API_KEY = Column(String(256))
    TMDB_API_KEY = Column(String(256))
    PO_USER_KEY = Column(String(256))
    PO_APP_KEY = Column(String(256))
    APPRISE = Column(String(1024))

    job = relationship("Job", back_populates="config")


# Sensitive fields to mask in API responses
HIDDEN_CONFIG_FIELDS = {
    "EMBY_API_KEY",
    "IFTTT_KEY",
    "PB_KEY",
    "OMDB_API_KEY",
    "TMDB_API_KEY",
    "PO_USER_KEY",
    "PO_APP_KEY",
    "APPRISE",
}


class AppState(Base):
    __tablename__ = "app_state"

    id = Column(Integer, primary_key=True)
    ripping_paused = Column(Boolean, default=False)


class SystemDrives(Base):
    __tablename__ = "system_drives"

    drive_id = Column(Integer, primary_key=True)
    name = Column(String(100))
    mount = Column(String(100))
    job_id_current = Column(Integer)
    job_id_previous = Column(Integer)
    description = Column(String(200))
    drive_mode = Column(String(100))
    maker = Column(String(25))
    model = Column(String(50))
    serial = Column(String(25))
    connection = Column(String(5))
    read_cd = Column(Boolean)
    read_dvd = Column(Boolean)
    read_bd = Column(Boolean)
    firmware = Column(String(10))
    location = Column(String(255))
    stale = Column(Boolean)
    mdisc = Column(Integer)
    serial_id = Column(String(100))


class SystemInfo(Base):
    __tablename__ = "system_info"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    cpu = Column(String(20))
    description = Column(String(256))
    mem_total = Column(Float)


class Notifications(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    message = Column(Text)
    trigger_time = Column(DateTime)
    seen = Column(Boolean, default=False)
    cleared = Column(Boolean, default=False)
