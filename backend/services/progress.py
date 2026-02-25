"""Read MakeMKV rip progress from ARM log files."""
import logging
import os
import re

from backend.config import settings

log = logging.getLogger(__name__)


def get_rip_progress(logfile: str | None) -> dict:
    """Parse MakeMKV progress from an ARM job's log file.

    Returns {"progress": float | None, "stage": str | None}
    """
    result: dict = {"progress": None, "stage": None}
    if not logfile:
        return result

    path = os.path.join(settings.arm_log_path, logfile)
    if not os.path.isfile(path):
        return result

    try:
        with open(path, "rb") as f:
            # Read last 8KB — progress lines are near the end
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - 8192))
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return result

    lines = tail.splitlines()

    last_prgv = None
    last_prgc = None
    for line in lines:
        m = re.search(r"PRGV:(\d{3,}),(\d+),(\d{3,})", line)
        if m:
            last_prgv = m
        m = re.search(r'PRGC:\d+,(\d+),"([\w -]{2,})"', line)
        if m:
            last_prgc = m

    if last_prgv:
        current = int(last_prgv.group(1))
        maximum = int(last_prgv.group(3))
        if maximum > 0:
            result["progress"] = round(current / maximum * 100, 1)

    if last_prgc:
        index = int(last_prgc.group(1)) + 1
        name = last_prgc.group(2)
        result["stage"] = f"{index} - {name}"

    return result
