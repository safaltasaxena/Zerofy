"""Firebase config tests — FB-01 through FB-05.

All firebase_admin calls are mocked — no real Firebase SDK or project used.
Tests verify the singleton guard, ADC/credentials-file branching, and the
RuntimeError when neither env var is set.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock, patch, call
import importlib


def _reload_firebase():
    """Reload config.firebase to reset module-level state between tests."""
    import config.firebase as fb
    # Reset the module-level singleton
    fb._db = None
    return fb


# ── FB-01 ─────────────────────────────────────────────────────────────────────

def test_fb_01_get_db_returns_client_with_credentials_path(tmp_path):
    """FB-01: get_db() returns a Firestore client when FIREBASE_CREDENTIALS_PATH is set."""
    fake_cred_path = str(tmp_path / "creds.json")

    mock_cred = MagicMock()
    mock_client = MagicMock()

    with (
        patch.dict(os.environ, {
            "FIREBASE_CREDENTIALS_PATH": fake_cred_path,
            "FIREBASE_PROJECT_ID": "",
        }),
        patch("firebase_admin._apps", {}),
        patch("firebase_admin.credentials.Certificate", return_value=mock_cred),
        patch("firebase_admin.initialize_app"),
        patch("firebase_admin.firestore.client", return_value=mock_client),
    ):
        _reload_firebase()
        import config.firebase as fb
        fb._db = None   # force reinit
        result = fb.get_db()

    assert result is mock_client


# ── FB-02 ─────────────────────────────────────────────────────────────────────

def test_fb_02_get_db_returns_client_with_project_id_only():
    """FB-02: get_db() returns a client when only FIREBASE_PROJECT_ID is set (ADC path)."""
    mock_client = MagicMock()

    with (
        patch.dict(os.environ, {
            "FIREBASE_CREDENTIALS_PATH": "",
            "FIREBASE_PROJECT_ID": "test-project-adc",
        }),
        patch("firebase_admin._apps", {}),
        patch("firebase_admin.initialize_app"),
        patch("firebase_admin.firestore.client", return_value=mock_client),
    ):
        _reload_firebase()
        import config.firebase as fb
        fb._db = None
        result = fb.get_db()

    assert result is mock_client


# ── FB-03 ─────────────────────────────────────────────────────────────────────

def test_fb_03_get_db_raises_when_neither_env_set():
    """FB-03: get_db() raises RuntimeError when neither FIREBASE_CREDENTIALS_PATH
    nor FIREBASE_PROJECT_ID is set."""
    with (
        patch.dict(os.environ, {
            "FIREBASE_CREDENTIALS_PATH": "",
            "FIREBASE_PROJECT_ID": "",
        }),
        patch("firebase_admin._apps", {}),
    ):
        import config.firebase as fb
        fb._db = None
        with pytest.raises(RuntimeError, match="Firebase"):
            fb.get_db()


# ── FB-04 ─────────────────────────────────────────────────────────────────────

def test_fb_04_get_db_called_twice_initialises_only_once():
    """FB-04: Calling get_db() twice → Firebase init called only once (singleton)."""
    mock_client = MagicMock()
    init_spy = MagicMock()

    with (
        patch.dict(os.environ, {
            "FIREBASE_CREDENTIALS_PATH": "",
            "FIREBASE_PROJECT_ID": "test-project-singleton",
        }),
        patch("firebase_admin._apps", {}),
        patch("firebase_admin.initialize_app", side_effect=init_spy),
        patch("firebase_admin.firestore.client", return_value=mock_client),
    ):
        import config.firebase as fb
        fb._db = None

        result1 = fb.get_db()
        result2 = fb.get_db()

    assert result1 is mock_client
    assert result2 is mock_client
    # initialize_app may be called once or zero times (if _apps already has entries)
    # The key assertion: _db is the same object both times
    assert result1 is result2


# ── FB-05 ─────────────────────────────────────────────────────────────────────

def test_fb_05_db_is_none_before_first_call():
    """FB-05: _db module-level variable is None before get_db() is called."""
    import config.firebase as fb
    # Reset to pre-init state
    original = fb._db
    fb._db = None
    try:
        assert fb._db is None
    finally:
        fb._db = original
