"""Read MakeMKV rip progress from ARM progress files.

MakeMKV writes real-time PRGV/PRGC messages to a dedicated progress file
at {LOGPATH}/progress/{job_id}.log via the ``--progress=`` flag.  This is
separate from the main job log which only receives this data after the
subprocess completes (stdout is buffered by subprocess.run).
"""
import logging
import os
import re

from backend.config import settings

log = logging.getLogger(__name__)


def get_rip_progress(job_id: int) -> dict:
    """Parse MakeMKV progress from a job's progress file.

    Returns {"progress": float | None, "stage": str | None}
    """
    result: dict = {"progress": None, "stage": None}

    path = os.path.join(settings.arm_log_path, "progress", f"{job_id}.log")
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
        m = re.match(r"PRGV:(\d+),(\d+),(\d+)", line)
        if m:
            last_prgv = m
        m = re.match(r'PRGC:\d+,(\d+),"([^"]+)"', line)
        if m:
            last_prgc = m

    if last_prgv:
        # PRGV:current,total,max — total/max gives overall disc progress
        total = int(last_prgv.group(2))
        maximum = int(last_prgv.group(3))
        if maximum > 0:
            result["progress"] = round(total / maximum * 100, 1)

    if last_prgc:
        index = int(last_prgc.group(1)) + 1
        name = last_prgc.group(2)
        result["stage"] = f"Title {index}: {name}"

    return result
