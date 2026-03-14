"""Tests for backend.dependencies — get_db session generator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from backend.dependencies import get_db


def test_get_db_yields_session_and_closes():
    """get_db yields a session and closes it after use."""
    mock_session = MagicMock()
    with patch("backend.dependencies.get_session", return_value=mock_session):
        gen = get_db()
        session = next(gen)
        assert session is mock_session
        # Exhaust the generator to trigger finally block
        try:
            next(gen)
        except StopIteration:
            pass
        mock_session.close.assert_called_once()


def test_get_db_closes_on_exception():
    """get_db closes the session even if an exception occurs."""
    mock_session = MagicMock()
    with patch("backend.dependencies.get_session", return_value=mock_session):
        gen = get_db()
        session = next(gen)
        assert session is mock_session
        # Simulate an exception
        try:
            gen.throw(RuntimeError("test error"))
        except RuntimeError:
            pass
        mock_session.close.assert_called_once()
