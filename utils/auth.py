"""Authentication and persistent browser-session helpers for FitQuest AI."""

import hashlib
import secrets
from datetime import datetime, timedelta

import streamlit as st

from utils.database import (
    clear_session_token,
    create_user,
    get_user,
    get_user_by_session_token,
    get_user_by_username,
    set_session_token,
)

SESSION_DAYS = 30
QUERY_PARAM = "auth"


def hash_password(password: str) -> str:
    """Hash a password using the project's backward-compatible SHA-256 format."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return secrets.compare_digest(hash_password(password), password_hash)


def _hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_browser_token() -> str | None:
    try:
        value = st.query_params.get(QUERY_PARAM)
    except Exception:
        return None
    if isinstance(value, list):
        return value[0] if value else None
    return value or None


def _set_query_token(token: str) -> None:
    try:
        st.query_params[QUERY_PARAM] = token
    except Exception:
        # Session state remains the primary authentication state. The query
        # parameter is only the cross-page/browser-refresh fallback.
        pass


def _clear_query_token() -> None:
    try:
        st.query_params.pop(QUERY_PARAM, None)
    except Exception:
        pass


def _set_authenticated_state(user: dict) -> None:
    """Set all authentication state in one place."""
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.username = user["username"]


def _restore_login_from_browser() -> bool:
    token = _get_browser_token()
    if not token:
        return False

    user = get_user_by_session_token(_hash_session_token(token))
    if not user:
        _clear_query_token()
        return False

    _set_authenticated_state(user)
    return True


def initialize_auth() -> None:
    """Initialize Streamlit session state and restore a valid browser session."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = None

    # A Streamlit rerun normally preserves session_state. If it does not have
    # an authenticated user, use the signed/hashed browser token as fallback.
    if not st.session_state.authenticated:
        try:
            _restore_login_from_browser()
        except Exception:
            _clear_query_token()


def is_logged_in() -> bool:
    initialize_auth()
    user_id = st.session_state.get("user_id")
    if not st.session_state.get("authenticated") or user_id is None:
        return False

    try:
        user = get_user(user_id)
    except Exception:
        return False

    if user is None:
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = None
        return False

    # Keep the display name synchronized with the database.
    st.session_state.username = user["username"]
    return True


def get_current_user_id():
    initialize_auth()
    return st.session_state.get("user_id")


def get_current_user():
    initialize_auth()
    if not st.session_state.get("authenticated"):
        return None
    return get_user(st.session_state.get("user_id"))


def _start_session(user: dict) -> None:
    if not user:
        raise RuntimeError("Cannot start a session without a user account.")

    token = secrets.token_urlsafe(32)
    token_hash = _hash_session_token(token)
    expires_at = (datetime.utcnow() + timedelta(days=SESSION_DAYS)).isoformat()

    # Persist the session before marking the Streamlit session authenticated.
    set_session_token(user["id"], token_hash, expires_at)
    _set_authenticated_state(user)
    st.session_state.auth_token = token
    _set_query_token(token)


def register_user(username, password, confirm_password):
    username = (username or "").strip()
    password = password or ""
    confirm_password = confirm_password or ""

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."
    if len(username) > 30:
        return False, "Username cannot be longer than 30 characters."
    if not username.replace("_", "").isalnum():
        return False, "Username can contain only letters, numbers, and underscores."
    if len(password) < 6:
        return False, "Password must contain at least 6 characters."
    if password != confirm_password:
        return False, "Passwords do not match."

    try:
        if get_user_by_username(username) is not None:
            return False, "This username is already taken."

        user_id = create_user(username, hash_password(password))
        user = get_user(user_id)
        if user is None:
            raise RuntimeError(
                "The account was created but could not be read back from the database."
            )

        _start_session(user)
        return True, {"message": "Account created successfully!", "user_id": user_id}
    except Exception as error:
        message = str(error)
        if "unique" in message.lower() or "duplicate" in message.lower():
            message = "This username is already taken."
        return False, f"Could not create account: {message}"


def login_user(username, password):
    username = (username or "").strip()
    password = password or ""

    if not username or not password:
        return False, "Please enter both username and password."

    try:
        user = get_user_by_username(username)
        if user is None:
            return False, "Username or password is incorrect."

        if not verify_password(password, user.get("password_hash")):
            return False, "Username or password is incorrect."

        # Re-read after authentication so the session always points at the
        # current PostgreSQL row, not stale UI data.
        user = get_user(user["id"])
        _start_session(user)
        return True, f"Welcome back, {user['username']}!"
    except Exception as error:
        return False, f"Login failed: {error}"


def logout_user():
    user_id = st.session_state.get("user_id")
    try:
        clear_session_token(user_id)
    except Exception:
        pass

    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.pop("auth_token", None)
    _clear_query_token()


def require_login():
    initialize_auth()
    if not is_logged_in():
        st.warning("🔐 Please log in to access this page.")
        st.info("Go to the main FitQuest AI page to log in or create an account.")
        st.stop()
