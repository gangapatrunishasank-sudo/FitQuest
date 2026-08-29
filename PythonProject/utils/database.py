import sqlite3
from pathlib import Path
from datetime import date


# ============================================================
# DATABASE PATH
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATH = PROJECT_DIR / "fitquest.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(DATABASE_PATH)

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            streak INTEGER DEFAULT 0,
            last_workout_date TEXT,
            total_workouts INTEGER DEFAULT 0,
            current_challenge TEXT DEFAULT 'No Challenge'
        )
    """)


    # --------------------------------------------------------
    # CHECK OLD USERS TABLE
    # --------------------------------------------------------

    cursor.execute(
        "PRAGMA table_info(users)"
    )

    columns = [
        row["name"]
        for row in cursor.fetchall()
    ]


    if "password_hash" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN password_hash TEXT"
        )


    if "xp" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN xp INTEGER DEFAULT 0"
        )


    if "level" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN level INTEGER DEFAULT 1"
        )


    if "streak" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN streak INTEGER DEFAULT 0"
        )


    if "last_workout_date" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN last_workout_date TEXT"
        )


    if "total_workouts" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN total_workouts INTEGER DEFAULT 0"
        )


    if "current_challenge" not in columns:

        cursor.execute(
            "ALTER TABLE users "
            "ADD COLUMN current_challenge "
            "TEXT DEFAULT 'No Challenge'"
        )


    # --------------------------------------------------------
    # WORKOUTS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            workout_date TEXT NOT NULL,
            exercise_name TEXT NOT NULL,
            reps INTEGER DEFAULT 0,
            form_score REAL DEFAULT 0,
            xp_earned INTEGER DEFAULT 0
        )
    """)


    # --------------------------------------------------------
    # CHALLENGES TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_name TEXT NOT NULL,
            total_days INTEGER DEFAULT 7,
            current_day INTEGER DEFAULT 0,
            start_date TEXT,
            completed INTEGER DEFAULT 0
        )
    """)


    connection.commit()

    connection.close()


# ============================================================
# USER FUNCTIONS
# ============================================================

def create_user(
        username,
        password_hash
):

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO users (
            username,
            password_hash,
            xp,
            level,
            streak,
            total_workouts,
            current_challenge
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            password_hash,
            0,
            1,
            0,
            0,
            "No Challenge"
        )
    )


    user_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return user_id


# ============================================================
# GET USER
# ============================================================

def get_user(user_id):

    initialize_database()

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


    connection.close()


    if user:

        return dict(user)

    return None


# ============================================================
# GET USER BY USERNAME
# ============================================================

def get_user_by_username(username):

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    )


    user = cursor.fetchone()


    connection.close()


    if user:

        return dict(user)

    return None


# ============================================================
# GET ALL USERS
# ============================================================

def get_all_users():

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        ORDER BY
            xp DESC,
            total_workouts DESC,
            streak DESC,
            username ASC
        """
    )


    users = cursor.fetchall()


    connection.close()


    return [
        dict(user)
        for user in users
    ]


# ============================================================
# UPDATE USER STATISTICS
# ============================================================

def update_user_stats(
        user_id,
        xp,
        level,
        streak,
        last_workout_date
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        UPDATE users
        SET
            xp = ?,
            level = ?,
            streak = ?,
            last_workout_date = ?
        WHERE id = ?
        """,
        (
            xp,
            level,
            streak,
            last_workout_date,
            user_id
        )
    )


    connection.commit()

    connection.close()


# ============================================================
# LEADERBOARD
# ============================================================

def get_leaderboard(limit=None):

    users = get_all_users()

    leaderboard = []


    for rank, user in enumerate(
        users,
        start=1
    ):

        user["rank"] = rank

        leaderboard.append(user)


    if limit is not None:

        return leaderboard[:limit]


    return leaderboard


# ============================================================
# GET USER RANK
# ============================================================

def get_user_rank(user_id):

    leaderboard = get_leaderboard()


    for user in leaderboard:

        if user["id"] == user_id:

            return user["rank"]


    return None


# ============================================================
# SAVE WORKOUT
# ============================================================

def save_workout(
        user_id,
        exercise_name,
        reps,
        form_score,
        xp_earned
):

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()


    # --------------------------------------------------------
    # SAVE WORKOUT RECORD
    # --------------------------------------------------------

    cursor.execute(
        """
        INSERT INTO workouts (
            user_id,
            workout_date,
            exercise_name,
            reps,
            form_score,
            xp_earned
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            date.today().isoformat(),
            exercise_name,
            reps,
            form_score,
            xp_earned
        )
    )


    # --------------------------------------------------------
    # UPDATE WORKOUT COUNT ONLY
    # --------------------------------------------------------

    cursor.execute(
        """
        UPDATE users
        SET total_workouts = total_workouts + 1
        WHERE id = ?
        """,
        (user_id,)
    )


    connection.commit()

    connection.close()


# ============================================================
# WORKOUT HISTORY
# ============================================================

def get_workout_history(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM workouts
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    )


    workouts = cursor.fetchall()


    connection.close()


    return [
        dict(workout)
        for workout in workouts
    ]


# ============================================================
# RECENT WORKOUTS
# ============================================================

def get_recent_workouts(
        user_id,
        limit=10
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM workouts
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            limit
        )
    )


    workouts = cursor.fetchall()


    connection.close()


    return [
        dict(workout)
        for workout in workouts
    ]


# ============================================================
# TOTAL WORKOUT COUNT
# ============================================================

def get_total_workout_count(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM workouts
        WHERE user_id = ?
        """,
        (user_id,)
    )


    result = cursor.fetchone()


    connection.close()


    return result["total"]


# ============================================================
# TODAY WORKOUT COUNT
# ============================================================

def get_today_workout_count(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM workouts
        WHERE user_id = ?
        AND workout_date = ?
        """,
        (
            user_id,
            date.today().isoformat()
        )
    )


    result = cursor.fetchone()


    connection.close()


    return result["total"]


# ============================================================
# AVERAGE FORM SCORE
# ============================================================

def get_average_form_score(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT AVG(form_score) AS average_score
        FROM workouts
        WHERE user_id = ?
        """,
        (user_id,)
    )


    result = cursor.fetchone()


    connection.close()


    if result["average_score"] is None:

        return 0


    return round(
        result["average_score"],
        1
    )


# ============================================================
# ACCEPT CHALLENGE
# ============================================================

def accept_challenge(
        challenge_name,
        total_days,
        user_id
):

    initialize_database()

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO challenges (
            user_id,
            challenge_name,
            total_days,
            current_day,
            start_date,
            completed
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            challenge_name,
            total_days,
            0,
            date.today().isoformat(),
            0
        )
    )


    cursor.execute(
        """
        UPDATE users
        SET current_challenge = ?
        WHERE id = ?
        """,
        (
            challenge_name,
            user_id
        )
    )


    connection.commit()

    connection.close()


    return True


# ============================================================
# GET ACTIVE CHALLENGE
# ============================================================

def get_active_challenge(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM challenges
        WHERE user_id = ?
        AND completed = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )


    challenge = cursor.fetchone()


    connection.close()


    if challenge:

        return dict(challenge)

    return None


# ============================================================
# UPDATE CHALLENGE PROGRESS
# ============================================================

def update_challenge_progress(user_id):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM challenges
        WHERE user_id = ?
        AND completed = 0
        """,
        (user_id,)
    )


    challenges = cursor.fetchall()


    for challenge in challenges:

        new_day = (
            challenge["current_day"] + 1
        )

        completed = 0


        if new_day >= challenge["total_days"]:

            new_day = challenge[
                "total_days"
            ]

            completed = 1


        cursor.execute(
            """
            UPDATE challenges
            SET
                current_day = ?,
                completed = ?
            WHERE id = ?
            """,
            (
                new_day,
                completed,
                challenge["id"]
            )
        )


        if completed == 1:

            cursor.execute(
                """
                UPDATE users
                SET current_challenge = ?
                WHERE id = ?
                """,
                (
                    "No Challenge",
                    user_id
                )
            )


    connection.commit()

    connection.close()


# ============================================================
# START DATABASE
# ============================================================

initialize_database()