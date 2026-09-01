from pathlib import Path
import sys

import streamlit as st
import pandas as pd


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
    page_title="Progress | FitQuest AI",
    page_icon="📈",
    layout="wide"
)

from utils.ui import apply_fitquest_theme
apply_fitquest_theme()


# ============================================================
# IMPORT SYSTEM
# ============================================================

try:

    from utils.database import (
        initialize_database,
        get_connection
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

    st.title("📈 Your Fitness Progress")

    st.warning(
        "🔐 Please log in to view your personal fitness progress."
    )

    st.info(
        """
        Your progress page is personalized for your FitQuest account.

        After logging in, you can track:

        - Your workout history
        - XP growth
        - Form score improvement
        - Exercise volume
        - Total repetitions
        - Workout consistency
        """
    )

    st.stop()


# ============================================================
# GET CURRENT USER
# ============================================================

current_user_id = get_current_user_id()


# ============================================================
# GET USER DATA
# ============================================================

def get_user_data(user_id):

    default_user = {
        "username": "FitQuest Player",
        "xp": 0,
        "level": 1,
        "streak": 0,
        "total_workouts": 0
    }


    connection = None


    try:

        connection = get_connection()

        cursor = connection.cursor()

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

            return dict(user)


        return default_user


    except Exception:

        return default_user


    finally:

        if connection is not None:

            connection.close()


# ============================================================
# GET WORKOUT DATA
# ============================================================

def get_workout_data(user_id):

    connection = None


    try:

        connection = get_connection()

        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                id,
                workout_date,
                exercise_name,
                reps,
                form_score,
                xp_earned
            FROM workouts
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_id,)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        return pd.DataFrame(rows)


    except Exception:

        return pd.DataFrame()


    finally:

        if connection is not None:

            connection.close()


# ============================================================
# LOAD CURRENT USER DATA
# ============================================================

user = get_user_data(
    current_user_id
)


workout_data = get_workout_data(
    current_user_id
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📈 Your Fitness Progress")

st.write(
    f"Track your personal transformation journey, "
    f"**{user.get('username', 'FitQuest Player')}**."
)


st.caption(
    "All progress shown on this page belongs only "
    "to your logged-in FitQuest account."
)


# ============================================================
# NO WORKOUT DATA
# ============================================================

if workout_data.empty:

    st.divider()

    st.info(
        """
        You have not completed any workouts yet.

        Go to AI Workout and complete your first workout.
        Your personal progress charts will appear here automatically.
        """
    )


    if st.button(
        "🤖 Start AI Workout",
        use_container_width=True
    ):

        st.switch_page(
            "pages/4_Ai_workout.py"
        )


    st.stop()


# ============================================================
# PREPARE DATA
# ============================================================

workout_data["reps"] = pd.to_numeric(
    workout_data["reps"],
    errors="coerce"
).fillna(0)


workout_data["form_score"] = pd.to_numeric(
    workout_data["form_score"],
    errors="coerce"
).fillna(0)


workout_data["xp_earned"] = pd.to_numeric(
    workout_data["xp_earned"],
    errors="coerce"
).fillna(0)


workout_data["workout_date"] = (
    workout_data["workout_date"]
    .astype(str)
)


workout_data["cumulative_xp"] = (
    workout_data["xp_earned"].cumsum()
)


# ============================================================
# SUMMARY METRICS
# ============================================================

st.divider()

st.subheader(
    "🏆 Transformation Summary"
)


total_workouts = len(
    workout_data
)


total_reps = int(
    workout_data["reps"].sum()
)


average_form = round(
    workout_data["form_score"].mean(),
    1
)


total_xp_earned = int(
    workout_data["xp_earned"].sum()
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "💪 Workouts",
        total_workouts
    )


with col2:

    st.metric(
        "🔢 Total Reps",
        total_reps
    )


with col3:

    st.metric(
        "🎯 Average Form",
        f"{average_form}%"
    )


with col4:

    st.metric(
        "⭐ Workout XP",
        total_xp_earned
    )


# ============================================================
# CURRENT PLAYER STATUS
# ============================================================

st.divider()

st.subheader(
    "🎮 Current FitQuest Status"
)


status_col1, status_col2, status_col3, status_col4 = (
    st.columns(4)
)


with status_col1:

    st.metric(
        "⭐ Total XP",
        user.get("xp", 0)
    )


with status_col2:

    st.metric(
        "🏆 Level",
        user.get("level", 1)
    )


with status_col3:

    st.metric(
        "🔥 Current Streak",
        f"{user.get('streak', 0)} Days"
    )


with status_col4:

    st.metric(
        "💪 Recorded Workouts",
        user.get("total_workouts", total_workouts)
    )


# ============================================================
# XP PROGRESS
# ============================================================

st.divider()

st.subheader(
    "⭐ XP Growth"
)


xp_chart_data = workout_data[
    [
        "workout_date",
        "cumulative_xp"
    ]
].copy()


xp_chart_data = xp_chart_data.rename(
    columns={
        "cumulative_xp": "Cumulative XP"
    }
)


xp_chart_data = xp_chart_data.set_index(
    "workout_date"
)


st.line_chart(
    xp_chart_data
)


# ============================================================
# FORM SCORE PROGRESS
# ============================================================

st.divider()

st.subheader(
    "🎯 Form Score Progress"
)


form_chart_data = workout_data[
    [
        "workout_date",
        "form_score"
    ]
].copy()


form_chart_data = form_chart_data.rename(
    columns={
        "form_score": "Form Score"
    }
)


form_chart_data = form_chart_data.set_index(
    "workout_date"
)


st.line_chart(
    form_chart_data
)


# ============================================================
# EXERCISE VOLUME
# ============================================================

st.divider()

st.subheader(
    "💪 Exercise Volume"
)


rep_chart_data = workout_data[
    [
        "workout_date",
        "reps"
    ]
].copy()


rep_chart_data = rep_chart_data.rename(
    columns={
        "reps": "Repetitions"
    }
)


rep_chart_data = rep_chart_data.set_index(
    "workout_date"
)


st.bar_chart(
    rep_chart_data
)


# ============================================================
# PERSONAL PERFORMANCE INSIGHT
# ============================================================

st.divider()

st.subheader(
    "📊 Your Performance Insight"
)


if len(workout_data) >= 2:

    first_form_score = float(
        workout_data.iloc[0][
            "form_score"
        ]
    )


    latest_form_score = float(
        workout_data.iloc[-1][
            "form_score"
        ]
    )


    improvement = round(
        latest_form_score - first_form_score,
        1
    )


    insight_col1, insight_col2, insight_col3 = (
        st.columns(3)
    )


    with insight_col1:

        st.metric(
            "First Form Score",
            f"{first_form_score}%"
        )


    with insight_col2:

        st.metric(
            "Latest Form Score",
            f"{latest_form_score}%"
        )


    with insight_col3:

        if improvement >= 0:

            st.metric(
                "Form Improvement",
                f"+{improvement}%"
            )

        else:

            st.metric(
                "Form Improvement",
                f"{improvement}%"
            )


else:

    st.info(
        """
        Complete more workouts to unlock detailed
        performance comparison.
        """
    )


# ============================================================
# EXERCISE BREAKDOWN
# ============================================================

st.divider()

st.subheader(
    "🏋️ Exercise Breakdown"
)


exercise_summary = workout_data.groupby(
    "exercise_name"
).agg(

    Workouts=(
        "exercise_name",
        "count"
    ),

    Total_Reps=(
        "reps",
        "sum"
    ),

    Average_Form=(
        "form_score",
        "mean"
    ),

    Total_XP=(
        "xp_earned",
        "sum"
    )

)


exercise_summary = exercise_summary.reset_index()


exercise_summary[
    "Average_Form"
] = exercise_summary[
    "Average_Form"
].round(1)


exercise_summary = exercise_summary.rename(
    columns={
        "exercise_name": "Exercise",
        "Total_Reps": "Total Reps",
        "Average_Form": "Average Form",
        "Total_XP": "Total XP"
    }
)


st.dataframe(
    exercise_summary,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# COMPLETE WORKOUT HISTORY
# ============================================================

st.divider()

st.subheader(
    "📋 Complete Workout History"
)


history_display = workout_data[
    [
        "workout_date",
        "exercise_name",
        "reps",
        "form_score",
        "xp_earned"
    ]
].copy()


history_display = history_display.rename(
    columns={
        "workout_date": "Date",
        "exercise_name": "Exercise",
        "reps": "Reps",
        "form_score": "Form Score",
        "xp_earned": "XP Earned"
    }
)


history_display = history_display.iloc[
    ::-1
]


st.dataframe(
    history_display,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# AI PROGRESS FEEDBACK
# ============================================================

st.divider()

st.subheader(
    "🧠 AI Progress Summary"
)


if average_form >= 90:

    st.success(
        """
        Excellent performance!

        Your overall form score is very strong.
        Keep focusing on consistency and gradual
        improvement in your workouts.
        """
    )


elif average_form >= 75:

    st.info(
        """
        You are making good progress.

        Your next goal should be improving movement
        quality while maintaining consistency.
        """
    )


else:

    st.warning(
        """
        Your workout journey is progressing, but your
        average form score needs improvement.

        Use the AI Workout feedback and focus on
        slower and more controlled movements.
        """
    )


# ============================================================
# CONSISTENCY
# ============================================================

st.divider()

st.subheader(
    "🔥 Consistency"
)


st.metric(
    "Current Streak",
    f"{user.get('streak', 0)} Days"
)


if user.get("streak", 0) == 0:

    st.info(
        "Complete a workout to start building your streak."
    )


elif user.get("streak", 0) == 1:

    st.info(
        "You have started your streak. Come back tomorrow "
        "and complete another workout to keep it alive."
    )


else:

    st.success(
        f"You are on a {user.get('streak', 0)}-day streak! "
        "Keep your consistency going."
    )


# ============================================================
# CONTINUE YOUR JOURNEY
# ============================================================

st.divider()

st.subheader(
    "🚀 Continue Your Journey"
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
        "📊 Open Dashboard",
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


# ============================================================
# REFRESH
# ============================================================

st.divider()


if st.button(
    "🔄 Refresh Progress",
    use_container_width=True
):

    st.rerun()


# ============================================================
# SYSTEM STATUS
# ============================================================

with st.expander(
    "🔧 Progress System Status"
):

    st.success(
        "Your progress data is loaded only for your "
        "currently logged-in FitQuest account."
    )