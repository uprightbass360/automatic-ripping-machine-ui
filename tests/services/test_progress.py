"""Tests for backend.services.progress — MakeMKV and music rip progress parsing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.services.progress import get_music_progress, get_rip_progress


# --- get_rip_progress ---


class TestGetRipProgress:
    """Tests for MakeMKV progress file parsing."""

    def test_valid_progress_with_prgv_and_saving_prgt(self, tmp_path):
        """PRGV line during 'Saving' phase returns numeric progress percentage."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        log = progress_dir / "42.log"
        log.write_text(
            'PRGT:0,0,"Saving to MKV file"\n'
            "PRGV:500,500,1000\n"
            'PRGC:0,2,"title_t03.mkv"\n'
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(42)
        assert result["progress"] == pytest.approx(50.0)
        assert result["stage"] == "Title 3: title_t03.mkv"

    def test_missing_progress_file(self, tmp_path):
        """Non-existent progress file returns None/None."""
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(999)
        assert result == {"progress": None, "stage": None}

    def test_scan_phase_no_saving(self, tmp_path):
        """Progress during scan (no 'Saving' in PRGT) returns stage but no numeric progress."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        log = progress_dir / "10.log"
        log.write_text(
            'PRGT:0,0,"Analyzing seamless segments"\n'
            "PRGV:200,200,1000\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(10)
        # No PRGC line, so stage comes from the non-saving PRGT branch
        assert result["progress"] is None
        assert result["stage"] == "Analyzing seamless segments"

    def test_scan_phase_with_prgc(self, tmp_path):
        """During scan phase, PRGC overrides the PRGT stage string."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        log = progress_dir / "11.log"
        log.write_text(
            'PRGT:0,0,"Analyzing seamless segments"\n'
            "PRGV:100,100,1000\n"
            'PRGC:0,0,"title_t01.mkv"\n'
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(11)
        assert result["progress"] is None
        assert result["stage"] == "Title 1: title_t01.mkv"

    def test_empty_progress_file(self, tmp_path):
        """Empty progress file returns None/None."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        (progress_dir / "7.log").write_text("")
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(7)
        assert result == {"progress": None, "stage": None}

    def test_saving_phase_100_percent(self, tmp_path):
        """Progress at maximum returns 100%."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        log = progress_dir / "50.log"
        log.write_text(
            'PRGT:0,0,"Saving to MKV file"\n'
            "PRGV:2000,2000,2000\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(50)
        assert result["progress"] == pytest.approx(100.0)

    def test_os_error_reading_file(self, tmp_path):
        """OSError when reading progress file returns None/None."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        log = progress_dir / "8.log"
        log.write_text("PRGV:1,1,10\n")
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            with patch("builtins.open", side_effect=OSError("permission denied")):
                result = get_rip_progress(8)
        assert result == {"progress": None, "stage": None}

    def test_multiple_prgv_lines_uses_last(self, tmp_path):
        """Multiple PRGV lines — uses the last one."""
        progress_dir = tmp_path / "progress"
        progress_dir.mkdir()
        log = progress_dir / "20.log"
        log.write_text(
            'PRGT:0,0,"Saving to MKV file"\n'
            "PRGV:100,100,1000\n"
            "PRGV:700,700,1000\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_rip_progress(20)
        assert result["progress"] == pytest.approx(70.0)


# --- get_music_progress ---


class TestGetMusicProgress:
    """Tests for abcde music log progress parsing."""

    def test_grabbing_encoding_tagging(self, tmp_path):
        """Log with all three phases returns correct counts and 'tagged' phase."""
        log = tmp_path / "music.log"
        log.write_text(
            "Grabbing track 1: some_track\n"
            "Grabbing track 2: another_track\n"
            "Grabbing track 3: third_track\n"
            "Encoding track 1 of 3\n"
            "Encoding track 2 of 3\n"
            "Tagging track 1 of 3\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_music_progress("music.log", total_tracks=3)
        assert result["progress"] is not None
        assert result["progress"] == pytest.approx(round(2 / 3 * 100, 1))
        assert "tagging" in result["stage"]
        assert "2/3" in result["stage"]

    def test_grabbing_only_phase_ripping(self, tmp_path):
        """Log with only Grabbing lines returns phase='ripping'."""
        log = tmp_path / "music.log"
        log.write_text(
            "Grabbing track 1: foo\n"
            "Grabbing track 2: bar\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_music_progress("music.log", total_tracks=5)
        assert "ripping" in result["stage"]
        assert result["progress"] == pytest.approx(0.0)  # 0 tagged / 5 total

    def test_grabbing_and_encoding_phase(self, tmp_path):
        """Log with Grabbing + Encoding returns phase='encoding'."""
        log = tmp_path / "music.log"
        log.write_text(
            "Grabbing track 1: foo\n"
            "Grabbing track 2: bar\n"
            "Encoding track 1 of 2\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_music_progress("music.log", total_tracks=2)
        assert "encoding" in result["stage"]
        assert result["progress"] == pytest.approx(50.0)  # 1 encoded / 2 total

    def test_empty_log(self, tmp_path):
        """Empty log file returns None/None."""
        log = tmp_path / "music.log"
        log.write_text("")
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_music_progress("music.log", total_tracks=5)
        assert result == {"progress": None, "stage": None}

    def test_missing_log(self, tmp_path):
        """Missing log file returns None/None."""
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_music_progress("nonexistent.log", total_tracks=5)
        assert result == {"progress": None, "stage": None}

    def test_none_logfile(self):
        """None logfile returns None/None without filesystem access."""
        result = get_music_progress(None, total_tracks=5)
        assert result == {"progress": None, "stage": None}

    def test_total_tracks_zero_uses_all_seen(self, tmp_path):
        """When total_tracks=0, uses len(all_seen) as the total."""
        log = tmp_path / "music.log"
        log.write_text(
            "Grabbing track 1: foo\n"
            "Grabbing track 2: bar\n"
            "Grabbing track 3: baz\n"
            "Encoding track 1 of 3\n"
            "Tagging track 1 of 3\n"
        )
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            result = get_music_progress("music.log", total_tracks=0)
        # total should be 3 (len of all_seen), 1 tagged
        assert result["progress"] == pytest.approx(round(1 / 3 * 100, 1))
        assert "1/3" in result["stage"]

    def test_os_error_reading_log(self, tmp_path):
        """OSError when reading log returns None/None."""
        log = tmp_path / "music.log"
        log.write_text("Grabbing track 1: foo\n")
        with patch("backend.services.progress.settings") as mock_settings:
            mock_settings.arm_log_path = str(tmp_path)
            with patch("builtins.open", side_effect=OSError("denied")):
                result = get_music_progress("music.log", total_tracks=5)
        assert result == {"progress": None, "stage": None}
