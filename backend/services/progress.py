"""Read rip progress from ARM progress files and abcde logs.

MakeMKV writes real-time PRGV/PRGC messages to a dedicated progress file
at {LOGPATH}/progress/{job_id}.log via the ``--progress=`` flag.  This is
separate from the main job log which only receives this data after the
subprocess completes (stdout is buffered by subprocess.run).

For music (abcde) rips, progress is parsed from the main job log using
Grabbing/Encoding/Tagging track patterns.
"""
import logging
import os
import re

from backend.config import settings

log = logging.getLogger(__name__)


def _parse_progress_lines(lines: list[str]) -> tuple:
    """Scan MakeMKV progress lines and return (last_prgv, last_prgc, last_prgt)."""
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
    return last_prgv, last_prgc, last_prgt


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

    last_prgv, last_prgc, last_prgt = _parse_progress_lines(data.splitlines())

    if last_prgv:
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


def get_music_progress(logfile: str | None, total_tracks: int) -> dict:
    """Parse abcde progress from the job's main log file.

    Returns {"progress": float | None, "stage": str | None}
    """
    result: dict = {"progress": None, "stage": None}

    if not logfile:
        return result

    path = os.path.join(settings.arm_log_path, logfile)
    if not os.path.isfile(path):
        return result

    try:
        with open(path, "r", errors="replace") as f:
            content = f.read()
    except OSError:
        return result

    # Same patterns as ARM's _poll_music_progress / process_audio_logfile
    grabbing = {int(m.group(1)) for m in re.finditer(r"Grabbing track (\d+):", content)}
    encoding = {int(m.group(1)) for m in re.finditer(r"Encoding track (\d+) of", content)}
    tagging = {int(m.group(1)) for m in re.finditer(r"Tagging track (\d+) of", content)}

    all_seen = grabbing | encoding | tagging
    if not all_seen:
        return result

    total = total_tracks or len(all_seen)
    completed = len(tagging)
    current_track = max(all_seen)

    if tagging:
        phase = "tagged"
    elif encoding:
        phase = "encoding"
    else:
        phase = "ripping"

    result["stage"] = f"{completed}/{total} - {phase} track {current_track}"
    if total > 0:
        result["progress"] = round(completed / total * 100, 1)

    return result
