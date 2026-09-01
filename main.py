import streamlit as st

from utils.database import initialize_database
from utils.auth import (
    initialize_auth,
    is_logged_in,
    login_user,
    register_user,
    logout_user,
    get_current_user,
)
from utils.ui import apply_fitquest_theme, brand, kpi


st.set_page_config(
    page_title="FitQuest AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize the selected database (SQLite locally, PostgreSQL on Render)
try:
    initialize_database()
except Exception as exc:
    st.error("FitQuest could not connect to its database.")
    st.code(str(exc))
    st.info(
        "For Render, add a PostgreSQL DATABASE_URL environment variable. "
        "Local development automatically uses SQLite."
    )
    st.stop()

initialize_auth()
apply_fitquest_theme()


# ============================================================
# LOGIN / SIGNUP
# ============================================================

if not is_logged_in():
    brand()

    st.markdown(
        """
        <section class="fq-hero">
          <div class="fq-eyebrow">AI FITNESS OPERATING SYSTEM</div>
          <div class="fq-hero-title">Train smarter.<br><span class="fq-gradient">Level up.</span></div>
          <div class="fq-lead">FitQuest turns real movement into measurable progress using computer vision, intelligent form validation and game-style progression.</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:22px"></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    features = [
        ("🤖", "AI Motion Engine", "Real-time pose landmarks, exercise recognition and rep validation."),
        ("⚡", "XP Progression", "Earn XP only from validated movement and build your level over time."),
        ("🏆", "Competitive Quests", "Complete challenges, protect your streak and climb the leaderboard."),
    ]

    for col, (icon, title, copy) in zip((c1, c2, c3), features):
        with col:
            st.markdown(
                f'<div class="fq-card"><div class="fq-feature-icon">{icon}</div>'
                f'<div class="fq-card-title">{title}</div><div class="fq-muted">{copy}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="fq-login">', unsafe_allow_html=True)
    st.markdown(
        '<div class="fq-login-head"><div class="fq-login-title">Enter the arena</div>'
        '<div class="fq-login-copy">Create an account or continue your quest.</div></div>',
        unsafe_allow_html=True,
    )

    login_tab, signup_tab = st.tabs(["🔐 Login", "✨ Create account"])

    with login_tab:
        login_username = st.text_input(
            "Username", key="login_username", autocomplete="username"
        )
        login_password = st.text_input(
            "Password", type="password", key="login_password", autocomplete="current-password"
        )

        if st.button(
            "Enter FitQuest →",
            type="primary",
            use_container_width=True,
            key="login_button",
        ):
            if not login_username.strip() or not login_password:
                st.error("Please enter both username and password.")
            else:
                ok, message = login_user(login_username, login_password)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    with signup_tab:
        signup_username = st.text_input(
            "Choose username", key="signup_username", autocomplete="username"
        )
        signup_password = st.text_input(
            "Create password", type="password", key="signup_password", autocomplete="new-password"
        )
        signup_confirm = st.text_input(
            "Confirm password", type="password", key="signup_confirm_password", autocomplete="new-password"
        )

        if st.button(
            "Create my quest →",
            type="primary",
            use_container_width=True,
            key="signup_button",
        ):
            ok, result = register_user(
                signup_username,
                signup_password,
                signup_confirm,
            )
            if ok:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(str(result))

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="fq-footer">FITQUEST AI • Built with Python, Streamlit, MediaPipe & computer vision</div>',
        unsafe_allow_html=True,
    )
    st.stop()


# ============================================================
# LOGGED-IN DASHBOARD SHELL
# ============================================================

user = get_current_user()

if user is None:
    logout_user()
    st.warning("Your session has expired. Please log in again.")
    st.rerun()

username = user.get("username", "User")
level = int(user.get("level", 1) or 1)
xp = int(user.get("xp", 0) or 0)
streak = int(user.get("streak", 0) or 0)
total_workouts = int(user.get("total_workouts", 0) or 0)

with st.sidebar:
    brand(compact=True)
    st.markdown(
        f'<div class="fq-card"><div class="fq-card-title">👤 {username}</div>'
        f'<div class="fq-muted">Level {level} • {xp} XP</div>'
        f'<div class="fq-muted">🔥 {streak} day streak</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚪 Sign out", use_container_width=True, key="logout_button"):
        logout_user()
        st.rerun()

st.markdown(
    f'<div class="fq-eyebrow">FITQUEST COMMAND CENTER</div>'
    f'<h1>Welcome back, {username}. ⚡</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="fq-lead">Your AI training system is ready. Use the navigation to train, complete quests and compete.</div>',
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

cols = st.columns(4)
for col, html in zip(
    cols,
    [
        kpi("Level", level),
        kpi("Total XP", xp, True),
        kpi("Streak", f"{streak} 🔥"),
        kpi("Workouts", total_workouts),
    ],
):
    with col:
        st.markdown(html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.info(
    "Use **Dashboard** for today's quest, **AI Workout** for camera-based training, "
    "**Challenges** for long-term goals, **Progress** for analytics and **Leaderboard** for competition."
)
