from pathlib import Path
import sys

import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Challenges | FitQuest AI",
    page_icon="🏆",
    layout="wide"
)


# ============================================================
# IMPORT AUTHENTICATION
# ============================================================

from utils.auth import (
    initialize_auth,
    get_current_user_id,
    is_logged_in
)


# ============================================================
# IMPORT DATABASE
# ============================================================

from utils.database import (
    initialize_database,
    get_user,
    get_active_challenge,
    accept_challenge
)


# ============================================================
# INITIALIZE SYSTEM
# ============================================================

initialize_database()

initialize_auth()


# ============================================================
# LOGIN CHECK
# ============================================================

if not is_logged_in():

    st.title("🏆 FitQuest Challenges")

    st.warning(
        "🔐 Please log in to access your personal challenges."
    )

    st.info(
        """
        Each FitQuest account has its own:

        - Active challenge
        - Challenge progress
        - Workout progress
        - XP
        - Streak
        """
    )

    st.stop()


# ============================================================
# GET CURRENT USER
# ============================================================

current_user_id = get_current_user_id()

user = get_user(
    current_user_id
)


if user is None:

    st.error(
        "Your user account could not be found."
    )

    st.stop()


# ============================================================
# CHALLENGE CONFIGURATION
# ============================================================

CHALLENGES = {
    "Six-Pack Challenge": {
        "emoji": "🔥",
        "days": 30,
        "description": (
            "Build consistency and strengthen your core "
            "through a 30-day fitness journey."
        ),
        "reward": 500
    },

    "Weight Loss Challenge": {
        "emoji": "⚡",
        "days": 45,
        "description": (
            "Stay consistent and complete your "
            "45-day transformation journey."
        ),
        "reward": 750
    },

    "Full Body Transformation": {
        "emoji": "💪",
        "days": 60,
        "description": (
            "Train consistently and build a stronger "
            "and healthier version of yourself."
        ),
        "reward": 1000
    }
}


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🏆 FitQuest Challenges")

st.write(
    f"Welcome, **{user.get('username', 'FitQuest Player')}**! "
    "Choose a quest, stay consistent, and level up your fitness journey."
)


st.divider()


# ============================================================
# USER QUICK STATS
# ============================================================

stat1, stat2, stat3, stat4 = st.columns(4)


with stat1:

    st.metric(
        "⭐ XP",
        user.get("xp", 0)
    )


with stat2:

    st.metric(
        "🏆 Level",
        user.get("level", 1)
    )


with stat3:

    st.metric(
        "🔥 Streak",
        f"{user.get('streak', 0)} Days"
    )


with stat4:

    st.metric(
        "💪 Workouts",
        user.get("total_workouts", 0)
    )


st.divider()


# ============================================================
# LOAD USER'S ACTIVE CHALLENGE
# ============================================================

active_challenge = get_active_challenge(
    current_user_id
)


# ============================================================
# ACTIVE CHALLENGE VIEW
# ============================================================

if active_challenge:

    challenge_name = active_challenge.get(
        "challenge_name",
        "Fitness Challenge"
    )


    total_days = int(
        active_challenge.get(
            "total_days",
            1
        )
    )


    current_day = int(
        active_challenge.get(
            "current_day",
            0
        )
    )


    challenge_info = CHALLENGES.get(
        challenge_name,
        {
            "emoji": "🏆",
            "days": total_days,
            "description": "Your active FitQuest challenge.",
            "reward": 500
        }
    )


    progress = min(
        current_day / total_days,
        1.0
    )


    st.subheader(
        f"{challenge_info['emoji']} Your Active Quest"
    )


    st.success(
        f"**{challenge_name}** is currently active!"
    )


    # --------------------------------------------------------
    # CHALLENGE PROGRESS
    # --------------------------------------------------------

    progress_col1, progress_col2, progress_col3 = (
        st.columns(3)
    )


    with progress_col1:

        st.metric(
            "Current Progress",
            f"{current_day}/{total_days}"
        )


    with progress_col2:

        st.metric(
            "Completion",
            f"{int(progress * 100)}%"
        )


    with progress_col3:

        st.metric(
            "Final Reward",
            f"+{challenge_info['reward']} XP"
        )


    st.progress(
        progress
    )


    st.write(
        challenge_info["description"]
    )


    remaining_days = max(
        total_days - current_day,
        0
    )


    if remaining_days > 0:

        st.info(
            f"Complete {remaining_days} more workout day(s) "
            "to finish this challenge."
        )


    else:

        st.success(
            "🎉 Challenge completed! "
            "Congratulations on reaching your goal."
        )


# ============================================================
# NO ACTIVE CHALLENGE
# ============================================================

else:

    st.subheader(
        "🎯 Choose Your Next Quest"
    )


    st.write(
        "Choose one challenge and build your consistency."
    )


    challenge_columns = st.columns(3)


    for index, (
        challenge_name,
        challenge_data
    ) in enumerate(
        CHALLENGES.items()
    ):


        with challenge_columns[index]:


            st.markdown(
                f"## {challenge_data['emoji']}"
            )


            st.subheader(
                challenge_name
            )


            st.write(
                challenge_data["description"]
            )


            st.metric(
                "Duration",
                f"{challenge_data['days']} Days"
            )


            st.metric(
                "Final Reward",
                f"+{challenge_data['reward']} XP"
            )


            if st.button(
                f"Start {challenge_name}",
                key=f"challenge_{index}",
                use_container_width=True
            ):


                try:

                    accept_challenge(
                        challenge_name=challenge_name,
                        total_days=challenge_data["days"],
                        user_id=current_user_id
                    )


                    st.success(
                        f"{challenge_name} started successfully!"
                    )


                    st.rerun()


                except Exception as error:

                    st.error(
                        f"Challenge could not be started: {error}"
                    )


# ============================================================
# HOW CHALLENGES WORK
# ============================================================

st.divider()


st.subheader(
    "🎮 How Challenges Work"
)


st.write(
    """
    1. Choose one challenge.
    2. Complete an AI workout.
    3. Your challenge progress increases only for that account.
    4. Multiple workouts on the same day do not increase challenge days again.
    5. Keep your streak alive by working out consistently.
    6. Reach the final day to complete your quest.
    """
)


# ============================================================
# USER ACTIVITY SUMMARY
# ============================================================

st.divider()


st.subheader(
    "📊 Your Challenge Activity"
)


activity_col1, activity_col2 = st.columns(2)


with activity_col1:

    st.metric(
        "Total Workouts",
        user.get(
            "total_workouts",
            0
        )
    )


with activity_col2:

    if active_challenge:

        st.metric(
            "Active Challenge",
            active_challenge.get(
                "challenge_name",
                "None"
            )
        )

    else:

        st.metric(
            "Active Challenge",
            "None"
        )


# ============================================================
# CONTINUE JOURNEY
# ============================================================

st.divider()


st.subheader(
    "🚀 Continue Your Journey"
)


action1, action2, action3 = st.columns(3)


with action1:

    if st.button(
        "🏋️ Start AI Workout",
        use_container_width=True
    ):

        st.switch_page(
            "pages/4_Ai_workout.py"
        )


with action2:

    if st.button(
        "📊 View Dashboard",
        use_container_width=True
    ):

        st.switch_page(
            "pages/2_Dashboard.py"
        )


with action3:

    if st.button(
        "🏅 View Leaderboard",
        use_container_width=True
    ):

        st.switch_page(
            "pages/6_Leaderboard.py"
        )