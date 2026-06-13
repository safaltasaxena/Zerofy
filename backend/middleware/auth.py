"""Firebase token verification — FastAPI dependency for all authenticated routes.

SECURITY (SECURITY_SPEC.md §5):
  - Token is verified via Firebase Admin SDK.
  - user_id (uid) is extracted from the decoded token — never from request body.
  - The token itself is never logged.
  - Any failure raises HTTPException 401 — no detail about why verification failed.
"""

# Standard library
import logging

# Third-party
import firebase_admin.auth
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

logger = logging.getLogger(__name__)

# OAuth2 scheme — extracts Bearer token from Authorization header
# tokenUrl is a placeholder; Zerofy uses Firebase client-side auth, not OAuth2 grant
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login", auto_error=True)


def verify_token(token: str = Depends(oauth2_scheme)) -> str:
    """Verify a Firebase ID token and return the uid.

    Extracts the Bearer token from the Authorization header (via oauth2_scheme),
    verifies it with Firebase Admin SDK, and returns the decoded uid.

    Args:
        token: Firebase ID token extracted from the Authorization header.

    Returns:
        uid (str) — the verified user ID, used as user_id in all route logic.

    Raises:
        HTTPException 401: On any token verification failure — generic message only.
    """
    try:
        decoded = firebase_admin.auth.verify_id_token(token)
        uid: str = decoded["uid"]
        return uid
    except firebase_admin.auth.ExpiredIdTokenError:
        # Log at warning level — expired tokens are not anomalous
        logger.warning("Token verification failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_admin.auth.InvalidIdTokenError:
        logger.warning("Token verification failed: invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        # Catch-all — never log the token value itself
        logger.warning("Token verification failed: unexpected error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
