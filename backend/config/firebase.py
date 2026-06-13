"""Singleton Firestore client for Zerofy India backend.

Supports three initialisation paths:
  Path A — Local dev:   FIREBASE_CREDENTIALS_PATH is set → credentials file
  Path B — GCP Cloud Run: FIREBASE_PROJECT_ID set, no credentials path → ADC
  Path C — Neither set: raises RuntimeError on startup

Module-level guard ensures Firebase is never initialised twice.
"""

# Standard library
import os

# Third-party
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

# Module-level singleton guard — initialised at most once
_db: firestore.Client | None = None


def _initialise_firebase() -> None:
    """Initialise the Firebase Admin SDK exactly once.

    Selects the correct credential strategy based on environment variables.
    Raises RuntimeError if neither FIREBASE_CREDENTIALS_PATH nor
    FIREBASE_PROJECT_ID is present.
    """
    try:
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        project_id = os.getenv("FIREBASE_PROJECT_ID")

        if credentials_path:
            # Path A — local development: initialise using service account file
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
        elif project_id:
            # Path B — GCP Cloud Run: use Application Default Credentials
            # The attached service account is picked up automatically by ADC
            firebase_admin.initialize_app(options={"projectId": project_id})
        else:
            # Path C — neither variable is set: fail loudly at startup
            raise RuntimeError(
                "Firebase configuration missing. "
                "Set FIREBASE_CREDENTIALS_PATH (local dev) "
                "or FIREBASE_PROJECT_ID (GCP Cloud Run) in your environment."
            )
    except Exception as e:
        # Re-raise so the app fails to start with a clear message
        raise RuntimeError(f"Firebase initialisation failed: {e}") from e


def get_db() -> firestore.Client:
    """Return the singleton Firestore client, initialising Firebase on first call.

    Returns:
        firestore.Client: The shared Firestore database client.

    Raises:
        RuntimeError: If Firebase cannot be initialised due to missing config.
    """
    global _db
    try:
        if _db is None:
            # Only initialise if no Firebase app has been set up yet
            if not firebase_admin._apps:
                _initialise_firebase()
            _db = firestore.client()
        return _db
    except RuntimeError:
        # Propagate config errors unchanged — they carry clear messages
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to obtain Firestore client: {e}") from e
