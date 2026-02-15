"""Tests for backend.services.bash_script — script read/write/parse."""

from __future__ import annotations

from unittest.mock import mock_open, patch

from backend.services import bash_script


SAMPLE_SCRIPT = '''#!/usr/bin/env bash
TRANSCODER_URL="http://arm-transcoder:5000/webhook/arm"
WEBHOOK_SECRET="my-secret"
LOCAL_RAW_PATH="/home/arm/media/raw"
SHARED_RAW_PATH="/mnt/media/raw"
echo "hello"
'''


# --- _parse_variables ---


def test_parse_variables():
    """Extracts all four variables from script content."""
    result = bash_script._parse_variables(SAMPLE_SCRIPT)
    assert result["transcoder_url"] == "http://arm-transcoder:5000/webhook/arm"
    assert result["webhook_secret"] == "my-secret"
    assert result["local_raw_path"] == "/home/arm/media/raw"
    assert result["shared_raw_path"] == "/mnt/media/raw"


def test_parse_variables_empty():
    """Returns empty strings when variables have empty values."""
    content = 'TRANSCODER_URL=""\nWEBHOOK_SECRET=""\nLOCAL_RAW_PATH=""\nSHARED_RAW_PATH=""\n'
    result = bash_script._parse_variables(content)
    assert result["transcoder_url"] == ""
    assert result["webhook_secret"] == ""
    assert result["local_raw_path"] == ""
    assert result["shared_raw_path"] == ""


# --- read_script ---


def test_read_script_exists():
    """Reads and parses an existing script file."""
    with (
        patch("backend.services.bash_script._get_local_script_path", return_value="/tmp/notify_transcoder.sh"),
        patch("os.path.isfile", return_value=True),
        patch("builtins.open", mock_open(read_data=SAMPLE_SCRIPT)),
    ):
        result = bash_script.read_script()

    assert result["script_exists"] is True
    assert result["arm_path"] == "/etc/arm/config/notify_transcoder.sh"
    assert result["variables"]["transcoder_url"] == "http://arm-transcoder:5000/webhook/arm"
    assert result["variables"]["webhook_secret"] == "my-secret"
    assert result["content"] == SAMPLE_SCRIPT


def test_read_script_not_exists():
    """Returns script_exists=False when file is missing."""
    with (
        patch("backend.services.bash_script._get_local_script_path", return_value="/tmp/notify_transcoder.sh"),
        patch("os.path.isfile", return_value=False),
    ):
        result = bash_script.read_script()

    assert result["script_exists"] is False
    assert result["variables"] is None
    assert result["content"] is None


# --- write_script ---


def test_write_script_success():
    """Writes script with substituted variables."""
    m = mock_open()
    with (
        patch("backend.services.bash_script._get_local_script_path", return_value="/tmp/notify_transcoder.sh"),
        patch("builtins.open", m),
        patch("os.chmod") as mock_chmod,
    ):
        result = bash_script.write_script(
            transcoder_url="http://localhost:5000/webhook/arm",
            webhook_secret="s3cret",
            local_raw_path="/local/raw",
            shared_raw_path="/shared/raw",
        )

    assert result["success"] is True
    assert result["arm_path"] == "/etc/arm/config/notify_transcoder.sh"

    # Verify the written content has the substituted values
    written = "".join(call.args[0] for call in m().write.call_args_list)
    assert 'TRANSCODER_URL="http://localhost:5000/webhook/arm"' in written
    assert 'WEBHOOK_SECRET="s3cret"' in written
    assert 'LOCAL_RAW_PATH="/local/raw"' in written
    assert 'SHARED_RAW_PATH="/shared/raw"' in written
    mock_chmod.assert_called_once_with("/tmp/notify_transcoder.sh", 0o755)


def test_write_script_permission_error():
    """Returns error dict on PermissionError."""
    with (
        patch("backend.services.bash_script._get_local_script_path", return_value="/tmp/notify_transcoder.sh"),
        patch("builtins.open", side_effect=PermissionError("Permission denied")),
    ):
        result = bash_script.write_script(transcoder_url="http://localhost:5000/webhook/arm")

    assert result["success"] is False
    assert "Permission denied" in result["error"]
