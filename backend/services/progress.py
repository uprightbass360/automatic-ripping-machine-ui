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
            data = f.read().decode("utf-8", errors="replace")
    except OSError:
        return result

    lines = data.splitlines()

    # PRGT messages are rare (one per phase transition) and can be anywhere
    # in the file, so scan all lines.  PRGV/PRGC are high-frequency and we
    # only need the last occurrence, but scanning all lines is cheap for
    # progress files (typically < 200 KB).
    last_prgv = None
    last_prgc = None
    last_prgt = None
    for line in lines:
        if line.startswith("PRGT:"):
            m = re.match(r'PRGT:\d+,\d+,"([^"]+)"', line)
            if m:
                last_prgt = m.group(1)
        elif line.startswith("PRGV:"):
            m = re.match(r"PRGV:(\d+),(\d+),(\d+)", line)
            if m:
                last_prgv = m
        elif line.startswith("PRGC:"):
            m = re.match(r'PRGC:\d+,(\d+),"([^"]+)"', line)
            if m:
                last_prgc = m

    if last_prgv:
        # PRGV:current,total,max — total/max gives overall disc progress.
        # MakeMKV resets total/max per major phase (scan, decrypt, save),
        # so total==max during the scan phase is NOT 100% rip completion.
        # Only report progress during the actual "Saving" rip phase.
        total = int(last_prgv.group(2))
        maximum = int(last_prgv.group(3))
        if maximum > 0:
            is_rip_phase = last_prgt and "Saving" in last_prgt
            if is_rip_phase:
                result["progress"] = round(total / maximum * 100, 1)
            else:
                result["stage"] = last_prgt

    if last_prgc:
        index = int(last_prgc.group(1)) + 1
        name = last_prgc.group(2)
        result["stage"] = f"Title {index}: {name}"

    return result
