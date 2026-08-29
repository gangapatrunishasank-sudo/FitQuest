import streamlit as st

from utils.database import initialize_database
from utils.auth import (
    initialize_auth,
    is_logged_in,
    login_user,
    register_user,
    logout_user,
    get_current_user
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="FitQuest AI",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# INITIALIZE DATABASE AND AUTHENTICATION
# ============================================================

initialize_database()
initialize_auth()


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
        .hero-title {
            text-align: center;
            font-size: 3.2rem;
            font-weight: 800;
            margin-bottom: 0.3rem;
        }

        .hero-subtitle {
            text-align: center;
            font-size: 1.2rem;
            opacity: 0.8;
            margin-bottom: 2rem;
        }

        .feature-card {
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(128, 128, 128, 0.25);
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AUTHENTICATION PAGE
# ============================================================

if not is_logged_in():

    st.markdown(
        """
        <div class="hero-title">
            🏋️ FitQuest AI
        </div>

        <div class="hero-subtitle">
            Train smarter. Track progress. Level up.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    left, center, right = st.columns([1, 1.4, 1])

    with center:

        login_tab, signup_tab = st.tabs(
            [
                "🔐 Login",
                "✨ Create Account"
            ]
        )

        # ====================================================
        # LOGIN TAB
        # ====================================================

        with login_tab:

            st.subheader(
                "Welcome back!"
            )

            login_username = st.text_input(
                "Username",
                key="login_username"
            )

            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            if st.button(
                "Login to FitQuest",
                use_container_width=True,
                type="primary"
            ):

                success, message = login_user(
                    login_username,
                    login_password
                )

                if success:

                    st.success(message)

                    st.rerun()

                else:

                    st.error(message)

        # ====================================================
        # SIGNUP TAB
        # ====================================================

        with signup_tab:

            st.subheader(
                "Create your FitQuest account"
            )

            signup_username = st.text_input(
                "Choose a Username",
                key="signup_username"
            )

            signup_password = st.text_input(
                "Create Password",
                type="password",
                key="signup_password"
            )

            signup_confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="signup_confirm_password"
            )

            if st.button(
                "Create My Account",
                use_container_width=True,
                type="primary"
            ):

                success, result = register_user(
                    signup_username,
                    signup_password,
                    signup_confirm_password
                )

                if success:

                    st.success(
                        result["message"]
                    )

                    st.info(
                        "Your account is ready. Please log in using your new username and password."
                    )

                else:

                    st.error(result)

    st.divider()

    st.subheader(
        "🚀 What you can do with FitQuest AI"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            """
            ### 🤖 AI Workout

            Analyze exercise movement and track repetitions.
            """
        )

    with col2:

        st.markdown(
            """
            ### 📈 Track Progress

            Build XP, levels, streaks, and workout history.
            """
        )

    with col3:

        st.markdown(
            """
            ### 🏆 Compete

            Compare your real progress with other FitQuest users.
            """
        )

    st.stop()


# ============================================================
# LOGGED-IN USER AREA
# ============================================================

current_user = get_current_user()

if current_user is None:

    st.error(
        "Could not load your user profile."
    )

    st.stop()


# ============================================================
# SIDEBAR USER PANEL
# ============================================================

with st.sidebar:

    st.markdown(
        f"""
        ### 👤 {current_user["username"]}
        """
    )

    st.caption(
        f"🏆 Level {current_user['level']}"
    )

    st.caption(
        f"⭐ {current_user['xp']} XP"
    )

    st.caption(
        f"🔥 {current_user['streak']} Day Streak"
    )

    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout_user()

        st.rerun()


# ============================================================
# REDIRECT TO HOME
# ============================================================

st.markdown(
    f"""
    # Welcome back, {current_user["username"]}! 👋

    Your FitQuest AI account is active.
    """
)

st.info(
    """
    Use the navigation menu on the left to access:

    🏠 Home  
    📊 Dashboard  
    🤖 AI Workout  
    🎯 Challenges  
    📈 Progress  
    🏆 Leaderboard  
    """
)

st.success(
    "You are now logged into the multi-user FitQuest AI system."
)