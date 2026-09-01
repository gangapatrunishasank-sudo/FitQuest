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
    page_title="Leaderboard | FitQuest AI",
    page_icon="🏅",
    layout="wide"
)

from utils.ui import apply_fitquest_theme
apply_fitquest_theme()


# ============================================================
# IMPORT DATABASE
# ============================================================

try:
    from utils.database import (
        initialize_database,
        get_connection
    )

    DATABASE_AVAILABLE = True
    DATABASE_ERROR = None

except Exception as error:
    DATABASE_AVAILABLE = False
    DATABASE_ERROR = str(error)


# ============================================================
# IMPORT AUTHENTICATION
# ============================================================

try:
    from utils.auth import (
        initialize_auth,
        get_current_user_id,
        is_logged_in
    )

    AUTH_AVAILABLE = True

except Exception:
    AUTH_AVAILABLE = False


# ============================================================
# INITIALIZE SYSTEMS
# ============================================================

if AUTH_AVAILABLE:
    initialize_auth()


if DATABASE_AVAILABLE:

    try:
        initialize_database()

    except Exception as error:
        DATABASE_AVAILABLE = False
        DATABASE_ERROR = str(error)


# ============================================================
# GET LEADERBOARD DATA
# ============================================================

def get_leaderboard():

    if not DATABASE_AVAILABLE:
        return pd.DataFrame()

    connection = None

    try:

        connection = get_connection()

        query = """
            SELECT
                id,
                username,
                xp,
                level,
                streak,
                total_workouts
            FROM users
            ORDER BY
                xp DESC,
                total_workouts DESC,
                streak DESC
        """

        cursor = connection.cursor()
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        return pd.DataFrame(rows)

    except Exception:

        return pd.DataFrame()

    finally:

        if connection:
            connection.close()


# ============================================================
# GET LOGGED-IN USER
# ============================================================

def get_logged_in_user():

    if not DATABASE_AVAILABLE:
        return None

    if not AUTH_AVAILABLE:
        return None

    if not is_logged_in():
        return None

    current_user_id = get_current_user_id()

    if not current_user_id:
        return None

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
            (current_user_id,)
        )

        user = cursor.fetchone()

        if user:
            return dict(user)

        return None

    except Exception:

        return None

    finally:

        if connection:
            connection.close()


# ============================================================
# LOAD DATA
# ============================================================

leaderboard = get_leaderboard()

current_user = get_logged_in_user()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🏅 FitQuest Leaderboard")

st.write(
    "Compete with real FitQuest players. Earn XP, complete "
    "workouts, maintain your streak, and climb the global rankings."
)


# ============================================================
# DATABASE ERROR
# ============================================================

if not DATABASE_AVAILABLE:

    st.error(
        f"Leaderboard database error: {DATABASE_ERROR}"
    )

    st.stop()


# ============================================================
# EMPTY LEADERBOARD
# ============================================================

if leaderboard.empty:

    st.info(
        "No players are available on the leaderboard yet."
    )

    st.write(
        "Create an account and complete workouts to begin "
        "your FitQuest journey."
    )

    st.stop()


# ============================================================
# ADD RANK
# ============================================================

leaderboard.insert(
    0,
    "Rank",
    range(
        1,
        len(leaderboard) + 1
    )
)


# ============================================================
# TOP PLAYER SUMMARY
# ============================================================

st.divider()

summary_col1, summary_col2, summary_col3 = st.columns(3)


with summary_col1:

    st.metric(
        "👥 Total Players",
        len(leaderboard)
    )


with summary_col2:

    highest_xp = int(
        leaderboard.iloc[0]["xp"] or 0
    )

    st.metric(
        "⭐ Highest XP",
        highest_xp
    )


with summary_col3:

    total_workouts = int(
        leaderboard["total_workouts"].fillna(0).sum()
    )

    st.metric(
        "🏋️ Community Workouts",
        total_workouts
    )


# ============================================================
# TOP 3 PLAYERS
# ============================================================

st.divider()

st.subheader("👑 Top Players")

top_players = leaderboard.head(3)

top_columns = st.columns(3)

medals = [
    "🥇",
    "🥈",
    "🥉"
]


for index in range(3):

    with top_columns[index]:

        if index < len(top_players):

            player = top_players.iloc[index]

            st.markdown(
                f"## {medals[index]} #{int(player['Rank'])}"
            )

            st.subheader(
                str(player["username"])
            )

            st.metric(
                "XP",
                int(player["xp"] or 0)
            )

            st.write(
                f"🏆 Level: "
                f"**{int(player['level'] or 1)}**"
            )

            st.write(
                f"🔥 Streak: "
                f"**{int(player['streak'] or 0)} Days**"
            )

            st.write(
                f"🏋️ Workouts: "
                f"**{int(player['total_workouts'] or 0)}**"
            )

        else:

            st.info(
                "Waiting for more players."
            )


# ============================================================
# CURRENT USER COMPETITIVE POSITION
# ============================================================

st.divider()

st.subheader("🎯 Your Competitive Position")


if current_user:

    current_user_id = current_user.get("id")

    current_rank_data = leaderboard[
        leaderboard["id"] == current_user_id
    ]


    if not current_rank_data.empty:

        player_row = current_rank_data.iloc[0]

        user_rank = int(
            player_row["Rank"]
        )

        total_players = len(
            leaderboard
        )

        user_xp = int(
            player_row["xp"] or 0
        )

        highest_xp = int(
            leaderboard.iloc[0]["xp"] or 0
        )

        xp_difference = max(
            highest_xp - user_xp,
            0
        )


        rank_col1, rank_col2, rank_col3, rank_col4 = (
            st.columns(4)
        )


        with rank_col1:

            st.metric(
                "🏅 Your Rank",
                f"#{user_rank}"
            )


        with rank_col2:

            st.metric(
                "⭐ Your XP",
                user_xp
            )


        with rank_col3:

            st.metric(
                "👥 Total Players",
                total_players
            )


        with rank_col4:

            st.metric(
                "⬆️ XP to #1",
                xp_difference
            )


        if user_rank == 1:

            st.success(
                "👑 You are currently the #1 player on FitQuest AI!"
            )

        elif user_rank <= 3:

            st.success(
                "🔥 Excellent! You are currently in the Top 3."
            )

        else:

            st.info(
                f"Keep training! You need {xp_difference} XP "
                f"to catch the current #1 player."
            )

    else:

        st.warning(
            "Your account was detected, but your rank could not "
            "be found in the leaderboard."
        )


else:

    st.info(
        "Log in to see your personal rank and competitive position."
    )


# ============================================================
# GLOBAL RANKINGS
# ============================================================

st.divider()

st.subheader("📊 Global Rankings")


display_data = leaderboard[
    [
        "Rank",
        "username",
        "xp",
        "level",
        "streak",
        "total_workouts"
    ]
].copy()


display_data = display_data.rename(
    columns={
        "username": "Player",
        "xp": "XP",
        "level": "Level",
        "streak": "Streak",
        "total_workouts": "Workouts"
    }
)


st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# PLAYER PROFILE
# ============================================================

if current_user:

    st.divider()

    st.subheader("🎮 Your FitQuest Status")


    profile_col1, profile_col2, profile_col3 = (
        st.columns(3)
    )


    with profile_col1:

        st.metric(
            "🏆 Level",
            int(current_user.get("level", 1) or 1)
        )


    with profile_col2:

        st.metric(
            "🔥 Current Streak",
            f"{int(current_user.get('streak', 0) or 0)} Days"
        )


    with profile_col3:

        st.metric(
            "🏋️ Workouts",
            int(
                current_user.get(
                    "total_workouts",
                    0
                ) or 0
            )
        )


# ============================================================
# COMPETITIVE MESSAGE
# ============================================================

st.divider()

st.subheader("⚔️ Keep Climbing")


if current_user:

    current_xp = int(
        current_user.get("xp", 0) or 0
    )

    current_level = int(
        current_user.get("level", 1) or 1
    )

    next_level_xp = (
        current_level * 500
    )

    remaining_xp = max(
        next_level_xp - current_xp,
        0
    )


    if remaining_xp > 0:

        st.info(
            f"Earn approximately **{remaining_xp} more XP** "
            f"to continue progressing toward your next level."
        )

    else:

        st.success(
            "🚀 You have enough XP for your next level progress!"
        )


else:

    st.info(
        "Create an account, log in, and start earning XP "
        "to compete with other players."
    )


# ============================================================
# REFRESH BUTTON
# ============================================================

st.divider()


if st.button(
    "🔄 Refresh Leaderboard",
    use_container_width=True
):

    st.rerun()


# ============================================================
# SYSTEM STATUS
# ============================================================

with st.expander(
    "🔧 Leaderboard System Status"
):

    st.success(
        "Global leaderboard is connected to the shared "
        "FitQuest database."
    )

    if current_user:

        st.success(
            f"Logged-in player detected: "
            f"{current_user.get('username', 'FitQuest User')}"
        )

    else:

        st.warning(
            "No logged-in player is currently detected."
        )