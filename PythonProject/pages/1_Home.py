import streamlit as st

from utils.database import (
    get_user,
    get_active_challenge,
    get_user_rank
)

from utils.auth import (
    initialize_auth,
    get_current_user_id,
    is_logged_in
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Home | FitQuest AI",
    page_icon="🏋️",
    layout="wide"
)


# ============================================================
# INITIALIZE AUTHENTICATION
# ============================================================

initialize_auth()


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🏠 FitQuest AI Home")

st.markdown(
    """
    Welcome to your personal AI-powered fitness journey.
    Track your workouts, improve your form, complete challenges,
    earn XP, and compete on the leaderboard.
    """
)

st.divider()


# ============================================================
# USER LOGIN CHECK
# ============================================================

if not is_logged_in():

    st.warning(
        "🔐 You are currently not logged in."
    )

    st.info(
        """
        The multi-user system is currently being connected.

        Soon you will be able to:

        - Create your own FitQuest account
        - Log in securely
        - Save your own workout progress
        - Build your own XP and streak
        - Compete against other real users
        """
    )

    st.stop()


# ============================================================
# GET CURRENT USER
# ============================================================

user_id = get_current_user_id()

user = get_user(user_id)


# ============================================================
# USER VALIDATION
# ============================================================

if user is None:

    st.error(
        "Your user profile could not be loaded."
    )

    st.stop()


# ============================================================
# GET USER INFORMATION
# ============================================================

username = user.get(
    "username",
    "FitQuest User"
)

xp = user.get(
    "xp",
    0
)

level = user.get(
    "level",
    1
)

streak = user.get(
    "streak",
    0
)

total_workouts = user.get(
    "total_workouts",
    0
)


# ============================================================
# GET USER RANK
# ============================================================

rank = get_user_rank(
    user_id
)

if rank is None:
    rank = "-"


# ============================================================
# WELCOME SECTION
# ============================================================

st.markdown(
    f"""
    # 👋 Welcome back, {username}!

    Continue your fitness journey and become stronger every day.
    """
)


# ============================================================
# USER STATISTICS
# ============================================================

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "⭐ Total XP",
        xp
    )


with col2:

    st.metric(
        "🏆 Level",
        level
    )


with col3:

    st.metric(
        "🔥 Current Streak",
        f"{streak} Days"
    )


with col4:

    st.metric(
        "🏋️ Workouts",
        total_workouts
    )


with col5:

    st.metric(
        "🌍 Global Rank",
        f"#{rank}"
    )


st.divider()


# ============================================================
# ACTIVE CHALLENGE
# ============================================================

st.subheader(
    "🎯 Current Challenge"
)

challenge = get_active_challenge(
    user_id
)


if challenge is None:

    st.info(
        """
        You do not have an active challenge yet.

        Go to the Challenges page and start your first challenge.
        """
    )

else:

    challenge_name = challenge.get(
        "challenge_name",
        "Fitness Challenge"
    )

    current_day = challenge.get(
        "current_day",
        1
    )

    total_days = challenge.get(
        "total_days",
        7
    )

    progress_percentage = (
        current_day / total_days
    )

    st.markdown(
        f"""
        ### 🏅 {challenge_name}

        **Day {current_day} of {total_days}**
        """
    )

    st.progress(
        min(progress_percentage, 1.0)
    )

    st.caption(
        f"Challenge progress: {current_day}/{total_days} days completed"
    )


st.divider()


# ============================================================
# QUICK ACTIONS
# ============================================================

st.subheader(
    "🚀 Quick Actions"
)


action1, action2, action3 = st.columns(3)


with action1:

    st.markdown(
        """
        ### 🤖 AI Workout

        Analyze your workout posture using AI and get feedback.
        """
    )

    if st.button(
        "Start AI Workout",
        use_container_width=True
    ):

        st.switch_page(
            "pages/4_Ai_workout.py"
        )


with action2:

    st.markdown(
        """
        ### 🎯 Challenges

        Start a fitness challenge and build your consistency.
        """
    )

    if st.button(
        "View Challenges",
        use_container_width=True
    ):

        st.switch_page(
            "pages/3_Challenges.py"
        )


with action3:

    st.markdown(
        """
        ### 🏆 Leaderboard

        Compare your fitness progress with other FitQuest users.
        """
    )

    if st.button(
        "View Leaderboard",
        use_container_width=True
    ):

        st.switch_page(
            "pages/6_Leaderboard.py"
        )


st.divider()


# ============================================================
# FITNESS JOURNEY
# ============================================================

st.subheader(
    "📈 Your Fitness Journey"
)


if total_workouts == 0:

    st.info(
        """
        Your fitness journey starts here.

        Complete your first AI workout to begin earning XP,
        increasing your streak, and climbing the leaderboard.
        """
    )

else:

    st.success(
        f"""
        Great progress, {username}! You have completed
        {total_workouts} workout(s) and earned {xp} XP.
        Keep going!
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "FitQuest AI • Train Smart • Stay Consistent • Level Up"
)