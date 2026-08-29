import hashlib
import streamlit as st

from utils.database import (
    create_user,
    get_user,
    get_user_by_username
)


# ============================================================
# PASSWORD SECURITY
# ============================================================

def hash_password(password):
    """
    Convert a password into a SHA-256 hash.
    """

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verify_password(password, password_hash):
    """
    Verify whether a password matches the stored hash.
    """

    return (
        hash_password(password)
        == password_hash
    )


# ============================================================
# SESSION INITIALIZATION
# ============================================================

def initialize_auth():
    """
    Initialize authentication session variables.
    """

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_id" not in st.session_state:
        st.session_state.user_id = None

    if "username" not in st.session_state:
        st.session_state.username = None


# ============================================================
# CHECK LOGIN STATUS
# ============================================================

def is_logged_in():
    """
    Return True if a user is currently logged in.
    """

    initialize_auth()

    return (
        st.session_state.authenticated
        and st.session_state.user_id is not None
    )


# ============================================================
# GET CURRENT USER ID
# ============================================================

def get_current_user_id():
    """
    Return the ID of the currently logged-in user.
    """

    initialize_auth()

    return st.session_state.user_id


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user():
    """
    Return the currently logged-in user's database record.
    """

    initialize_auth()

    if not is_logged_in():
        return None

    return get_user(
        st.session_state.user_id
    )


# ============================================================
# REGISTER USER
# ============================================================

def register_user(
    username,
    password,
    confirm_password
):
    """
    Register a new FitQuest user.
    """

    username = username.strip()

    # Validate username
    if len(username) < 3:
        return (
            False,
            "Username must contain at least 3 characters."
        )

    if len(username) > 30:
        return (
            False,
            "Username cannot be longer than 30 characters."
        )

    if not username.replace("_", "").isalnum():
        return (
            False,
            "Username can contain only letters, numbers, and underscores."
        )

    # Validate password
    if len(password) < 6:
        return (
            False,
            "Password must contain at least 6 characters."
        )

    if password != confirm_password:
        return (
            False,
            "Passwords do not match."
        )

    # Check if username already exists
    existing_user = get_user_by_username(
        username
    )

    if existing_user is not None:
        return (
            False,
            "This username is already taken."
        )

    try:
        password_hash = hash_password(
            password
        )

        user_id = create_user(
            username,
            password_hash
        )

        return (
            True,
            {
                "message": "Account created successfully!",
                "user_id": user_id
            }
        )

    except Exception as error:
        return (
            False,
            f"Could not create account: {error}"
        )


# ============================================================
# LOGIN USER
# ============================================================

def login_user(
    username,
    password
):
    """
    Log an existing user into FitQuest.
    """

    initialize_auth()

    username = username.strip()

    user = get_user_by_username(
        username
    )

    if user is None:
        return (
            False,
            "Username or password is incorrect."
        )

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return (
            False,
            "Username or password is incorrect."
        )

    # Store logged-in user in Streamlit session
    st.session_state.authenticated = True
    st.session_state.user_id = user["id"]
    st.session_state.username = user["username"]

    return (
        True,
        f"Welcome back, {user['username']}!"
    )


# ============================================================
# LOGOUT USER
# ============================================================

def logout_user():
    """
    Log out the currently logged-in user.
    """

    initialize_auth()

    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None


# ============================================================
# LOGIN REQUIRED
# ============================================================

def require_login():
    """
    Stop page execution if no user is logged in.
    """

    initialize_auth()

    if not is_logged_in():

        st.warning(
            "🔐 Please log in to access this page."
        )

        st.info(
            "Go to the main FitQuest AI page to log in or create an account."
        )

        st.stop()