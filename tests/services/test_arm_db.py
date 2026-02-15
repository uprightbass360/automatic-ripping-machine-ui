"""Tests for backend.services.arm_db — config extraction, pagination, YAML reading."""

from __future__ import annotations

import math
from unittest.mock import patch

from backend.models.arm import HIDDEN_CONFIG_FIELDS
from backend.services import arm_db

from tests.factories import make_config, make_job


# --- _extract_config_safe ---


def test_extract_config_safe_masks_sensitive_fields():
    """Sensitive fields with values are masked to '***'."""
    config = make_config(OMDB_API_KEY="real_key", EMBY_API_KEY="emby_secret")
    result = arm_db._extract_config_safe(config)
    assert result is not None
    for field in HIDDEN_CONFIG_FIELDS:
        assert field in result, f"{field} missing from result"
        assert result[field] == "***", f"{field} should be masked"


def test_extract_config_safe_none_sensitive_stays_none():
    """Sensitive fields that are None remain None (not masked)."""
    config = make_config(OMDB_API_KEY=None, TMDB_API_KEY=None)
    result = arm_db._extract_config_safe(config)
    assert result is not None
    assert result["OMDB_API_KEY"] is None
    assert result["TMDB_API_KEY"] is None


def test_extract_config_safe_excludes_config_id_and_job_id():
    """CONFIG_ID and job_id are excluded from the output dict."""
    config = make_config(CONFIG_ID=42, job_id=7)
    result = arm_db._extract_config_safe(config)
    assert result is not None
    assert "CONFIG_ID" not in result
    assert "job_id" not in result


def test_extract_config_safe_none_input():
    """None config returns None."""
    assert arm_db._extract_config_safe(None) is None


def test_extract_config_safe_includes_normal_fields():
    """Non-sensitive fields are passed through unchanged."""
    config = make_config(RIPMETHOD="mkv", MINLENGTH="600")
    result = arm_db._extract_config_safe(config)
    assert result is not None
    assert result["RIPMETHOD"] == "mkv"
    assert result["MINLENGTH"] == "600"


# --- get_jobs_paginated_response pagination math ---


def test_pagination_response_math():
    """Pages calculation: ceil(total / per_page), minimum 1."""
    with patch.object(arm_db, "get_jobs_paginated") as mock_paginated:
        mock_paginated.return_value = ([make_job()] * 10, 47)
        result = arm_db.get_jobs_paginated_response(page=2, per_page=10)
    assert result["total"] == 47
    assert result["page"] == 2
    assert result["per_page"] == 10
    assert result["pages"] == math.ceil(47 / 10)  # 5


def test_pagination_response_empty():
    """Empty result set returns pages=1."""
    with patch.object(arm_db, "get_jobs_paginated") as mock_paginated:
        mock_paginated.return_value = ([], 0)
        result = arm_db.get_jobs_paginated_response()
    assert result["total"] == 0
    assert result["pages"] == 1
    assert result["jobs"] == []


# --- _read_arm_yaml ---


def test_read_arm_yaml_missing_path():
    """Returns None when arm_config_path is empty."""
    with patch.object(arm_db.settings, "arm_config_path", ""):
        assert arm_db._read_arm_yaml() is None


def test_read_arm_yaml_missing_file():
    """Returns None when the file does not exist."""
    with patch.object(arm_db.settings, "arm_config_path", "/nonexistent/arm.yaml"):
        assert arm_db._read_arm_yaml() is None


def test_read_arm_yaml_masks_sensitive_fields(tmp_path):
    """Sensitive fields in arm.yaml are masked to '***'."""
    yaml_file = tmp_path / "arm.yaml"
    yaml_file.write_text(
        "RIPMETHOD: mkv\n"
        "OMDB_API_KEY: real_key\n"
        "EMBY_API_KEY: emby_secret\n"
        "MINLENGTH: 600\n"
    )
    with patch.object(arm_db.settings, "arm_config_path", str(yaml_file)):
        result = arm_db._read_arm_yaml()
    assert result is not None
    assert result["OMDB_API_KEY"] == "***"
    assert result["EMBY_API_KEY"] == "***"
    assert result["RIPMETHOD"] == "mkv"
    assert result["MINLENGTH"] == 600
