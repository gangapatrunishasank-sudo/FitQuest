from pathlib import Path
import sys
from datetime import date

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
    page_title="Dashboard | FitQuest AI",
    page_icon="📊",
    layout="wide"
)

from utils.ui import apply_fitquest_theme
apply_fitquest_theme()


# ============================================================
# IMPORT DATABASE AND AUTHENTICATION
# ============================================================

try:

    from utils.database import (
        initialize_database,
        get_connection,
        get_active_challenge
    )

    from utils.auth import (
        initialize_auth,
        get_current_user_id,
        is_logged_in
    )

    SYSTEM_AVAILABLE = True
    SYSTEM_ERROR = None


except Exception as error:

    SYSTEM_AVAILABLE = False
    SYSTEM_ERROR = str(error)


# ============================================================
# INITIALIZE SYSTEM
# ============================================================

if SYSTEM_AVAILABLE:

    try:

        initialize_database()

        initialize_auth()


    except Exception as error:

        SYSTEM_AVAILABLE = False
        SYSTEM_ERROR = str(error)


# ============================================================
# SYSTEM ERROR
# ============================================================

if not SYSTEM_AVAILABLE:

    st.error(
        f"FitQuest system could not start: {SYSTEM_ERROR}"
    )

    st.stop()


# ============================================================
# LOGIN CHECK
# ============================================================

if not is_logged_in():

    st.title("📊 FitQuest Dashboard")

    st.warning(
        "🔐 Please log in to view your personal dashboard."
    )

    st.info(
        """
        Your dashboard is personalized for your FitQuest account.

        After logging in, you will be able to see:

        - Your XP and level
        - Your workout statistics
        - Your streak
        - Your form performance
        - Your recent workouts
        - Your challenge progress
        - Your AI fitness summary
        """
    )

    st.stop()


# ============================================================
# GET CURRENT USER
# ============================================================

current_user_id = get_current_user_id()


# ============================================================
# GET DASHBOARD DATA
# ============================================================

def get_dashboard_data(user_id):

    default_data = {
        "user": None,
        "recent_workouts": [],
        "average_form_score": 0,
        "total_reps": 0,
        "today_workouts": 0
    }


    connection = None


    try:

        connection = get_connection()

        cursor = connection.cursor()


        # ----------------------------------------------------
        # GET CURRENT USER
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()


        if user:

            default_data["user"] = dict(
                user
            )

        else:

            return default_data


        # ----------------------------------------------------
        # GET RECENT WORKOUTS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                workout_date,
                exercise_name,
                reps,
                form_score,
                xp_earned
            FROM workouts
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (user_id,)
        )

        workouts = cursor.fetchall()


        default_data["recent_workouts"] = [

            dict(workout)

            for workout in workouts
        ]


        # ----------------------------------------------------
        # GET AVERAGE FORM SCORE
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT AVG(form_score) AS average_score
            FROM workouts
            WHERE user_id = ?
            """,
            (user_id,)
        )

        average_result = cursor.fetchone()


        if (
            average_result
            and average_result["average_score"] is not None
        ):

            default_data[
                "average_form_score"
            ] = round(
                average_result["average_score"],
                1
            )


        # ----------------------------------------------------
        # GET TOTAL REPS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT SUM(reps) AS total_reps
            FROM workouts
            WHERE user_id = ?
            """,
            (user_id,)
        )

        reps_result = cursor.fetchone()


        if (
            reps_result
            and reps_result["total_reps"] is not None
        ):

            default_data[
                "total_reps"
            ] = int(
                reps_result["total_reps"]
            )


        # ----------------------------------------------------
        # GET TODAY'S WORKOUTS
        # ----------------------------------------------------

        today = date.today().isoformat()


        cursor.execute(
            """
            SELECT COUNT(*) AS workout_count
            FROM workouts
            WHERE user_id = ?
            AND workout_date = ?
            """,
            (
                user_id,
                today
            )
        )

        today_result = cursor.fetchone()


        if today_result:

            default_data[
                "today_workouts"
            ] = int(
                today_result["workout_count"]
            )


        return default_data


    except Exception:

        return default_data


    finally:

        if connection is not None:

            connection.close()


# ============================================================
# LOAD DASHBOARD DATA
# ============================================================

dashboard_data = get_dashboard_data(
    current_user_id
)


user = dashboard_data[
    "user"
]


# ============================================================
# USER VALIDATION
# ============================================================

if user is None:

    st.error(
        "Your user profile could not be loaded."
    )

    st.stop()


# ============================================================
# EXTRACT DATA
# ============================================================

recent_workouts = dashboard_data[
    "recent_workouts"
]


average_form_score = dashboard_data[
    "average_form_score"
]


total_reps = dashboard_data[
    "total_reps"
]


today_workouts = dashboard_data[
    "today_workouts"
]


# ============================================================
# USER VALUES
# ============================================================

username = user.get(
    "username",
    "FitQuest Player"
)


xp = int(
    user.get(
        "xp",
        0
    ) or 0
)


level = int(
    user.get(
        "level",
        1
    ) or 1
)


streak = int(
    user.get(
        "streak",
        0
    ) or 0
)


total_workouts = int(
    user.get(
        "total_workouts",
        0
    ) or 0
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📊 FitQuest Dashboard")

st.write(
    f"Welcome back, **{username}**! "
    "Here is your personal fitness progress."
)


# ============================================================
# MAIN PLAYER STATS
# ============================================================

st.divider()

st.subheader(
    "⚡ Your Fitness Overview"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "⭐ Total XP",
        xp
    )


with col2:

    st.metric(
        "🏆 Current Level",
        level
    )


with col3:

    st.metric(
        "🔥 Current Streak",
        f"{streak} Days"
    )


with col4:

    st.metric(
        "💪 Total Workouts",
        total_workouts
    )


# ============================================================
# FITNESS PERFORMANCE
# ============================================================

st.divider()

st.subheader(
    "📈 Fitness Performance"
)


performance_col1, performance_col2, performance_col3 = (
    st.columns(3)
)


with performance_col1:

    st.metric(
        "🎯 Average Form Score",
        f"{average_form_score}%"
    )


with performance_col2:

    st.metric(
        "🔢 Total Repetitions",
        total_reps
    )


with performance_col3:

    st.metric(
        "📅 Workouts Today",
        today_workouts
    )


# ============================================================
# LEVEL PROGRESS
# ============================================================

st.divider()

st.subheader(
    "⚡ Level Progress"
)


xp_for_current_level = (
    (level - 1) * 500
)


xp_for_next_level = (
    level * 500
)


xp_progress = (
    xp - xp_for_current_level
)


xp_needed_for_level = 500


progress_percentage = min(
    max(
        xp_progress / xp_needed_for_level,
        0
    ),
    1.0
)


st.write(
    f"You are currently **Level {level}**."
)


st.write(
    f"Progress toward Level {level + 1}: "
    f"**{max(xp_progress, 0)} / "
    f"{xp_needed_for_level} XP**"
)


st.progress(
    progress_percentage
)


remaining_xp = max(
    xp_for_next_level - xp,
    0
)


st.caption(
    f"{remaining_xp} XP remaining until "
    f"Level {level + 1}."
)


# ============================================================
# CURRENT CHALLENGE
# ============================================================

st.divider()

st.subheader(
    "🏁 Current Challenge"
)


active_challenge = None


try:

    active_challenge = get_active_challenge(
        current_user_id
    )


except Exception as error:

    st.warning(
        f"Challenge information could not be loaded: {error}"
    )


if active_challenge is None:

    st.info(
        """
        You have not selected a challenge yet.

        Go to the Challenges page and start your
        next fitness quest.
        """
    )


else:

    challenge_name = active_challenge.get(
        "challenge_name",
        "Fitness Challenge"
    )


    current_day = int(
        active_challenge.get(
            "current_day",
            0
        ) or 0
    )


    total_days = int(
        active_challenge.get(
            "total_days",
            1
        ) or 1
    )


    challenge_progress = min(
        current_day / total_days,
        1.0
    )


    challenge_col1, challenge_col2, challenge_col3 = (
        st.columns(3)
    )


    with challenge_col1:

        st.metric(
            "🎯 Active Challenge",
            challenge_name
        )


    with challenge_col2:

        st.metric(
            "📅 Progress",
            f"{current_day}/{total_days} Days"
        )


    with challenge_col3:

        st.metric(
            "📈 Completion",
            f"{int(challenge_progress * 100)}%"
        )


    st.progress(
        challenge_progress
    )


    remaining_days = max(
        total_days - current_day,
        0
    )


    if remaining_days > 0:

        st.caption(
            f"Complete {remaining_days} more day(s) "
            "to finish your challenge."
        )


    else:

        st.success(
            "🎉 Challenge completed!"
        )


# ============================================================
# RECENT WORKOUT HISTORY
# ============================================================

st.divider()

st.subheader(
    "📝 Recent Workout Activity"
)


if len(recent_workouts) == 0:

    st.info(
        """
        No workouts have been completed yet.

        Go to AI Workout and complete your first workout
        to start building your FitQuest profile.
        """
    )


else:

    for workout in recent_workouts:

        workout_col1, workout_col2 = st.columns(
            [2, 1]
        )


        with workout_col1:

            st.markdown(
                f"### 💪 {workout['exercise_name']}"
            )


            st.caption(
                f"Completed on: "
                f"{workout['workout_date']}"
            )


        with workout_col2:

            st.metric(
                "Repetitions",
                workout["reps"]
            )


        workout_stat1, workout_stat2 = st.columns(
            2
        )


        with workout_stat1:

            st.write(
                f"🎯 Form Score: "
                f"**{workout['form_score']}%**"
            )


        with workout_stat2:

            st.write(
                f"⭐ XP Earned: "
                f"**+{workout['xp_earned']} XP**"
            )


        st.divider()


# ============================================================
# AI COACH SUMMARY
# ============================================================

st.subheader(
    "🧠 AI Coach Summary"
)


if len(recent_workouts) == 0:

    st.info(
        """
        Complete your first workout to unlock
        personalized AI fitness feedback.
        """
    )


elif average_form_score >= 90:

    st.success(
        """
        Excellent performance!

        Your average form score is very strong.
        Focus on consistency and gradually increase
        your workout difficulty.
        """
    )


elif average_form_score >= 75:

    st.info(
        """
        You are making good progress.

        Continue focusing on controlled movement,
        correct posture, and workout consistency.
        """
    )


else:

    st.warning(
        """
        Your fitness journey is progressing,
        but your form can improve.

        Use the AI Workout feedback and focus
        on controlled and correct movement.
        """
    )


# ============================================================
# PERSONAL MOTIVATION
# ============================================================

st.divider()

st.subheader(
    "🚀 Your Next Goal"
)


if total_workouts == 0:

    st.info(
        """
        Start your first AI Workout.

        Every workout can help you earn XP,
        build your streak, and improve your
        position on the global leaderboard.
        """
    )


elif remaining_xp > 0:

    st.info(
        f"""
        Keep going, {username}!

        You need **{remaining_xp} more XP**
        to reach Level {level + 1}.
        """
    )


else:

    st.success(
        """
        Excellent work!

        You have enough XP to continue
        progressing toward the next stage
        of your FitQuest journey.
        """
    )


# ============================================================
# QUICK NAVIGATION
# ============================================================

st.divider()

st.subheader(
    "🚀 Quick Actions"
)


action1, action2, action3 = st.columns(3)


with action1:

    if st.button(
        "🤖 Start AI Workout",
        use_container_width=True
    ):

        st.switch_page(
            "pages/4_Ai_workout.py"
        )


with action2:

    if st.button(
        "🎯 View Challenges",
        use_container_width=True
    ):

        st.switch_page(
            "pages/3_Challenges.py"
        )


with action3:

    if st.button(
        "🏅 View Leaderboard",
        use_container_width=True
    ):

        st.switch_page(
            "pages/6_Leaderboard.py"
        )


# ============================================================
# REFRESH DASHBOARD
# ============================================================

st.divider()


if st.button(
    "🔄 Refresh Dashboard",
    use_container_width=True
):

    st.rerun()


# ============================================================
# SYSTEM STATUS
# ============================================================

with st.expander(
    "🔧 Dashboard System Status"
):

    st.success(
        "Your dashboard is connected to your personal FitQuest account."
    )