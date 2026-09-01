import os
import re
import sqlite3
from pathlib import Path
from datetime import date, datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None


PROJECT_DIR = Path(__file__).resolve().parent.parent
SQLITE_DATABASE_PATH = PROJECT_DIR / "data" / "fitquest.db"
SQLITE_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


def using_postgres():
    return bool(os.getenv("DATABASE_URL", "").strip())


class DatabaseCursor:
    def __init__(self, cursor, postgres=False):
        self._cursor = cursor
        self._postgres = postgres

    @staticmethod
    def _convert_query(query):
        return re.sub(r"\?", "%s", query)

    def execute(self, query, params=None):
        if self._postgres:
            query = self._convert_query(query)
        self._cursor.execute(query, params or ())
        return self

    def executemany(self, query, params_seq):
        if self._postgres:
            query = self._convert_query(query)
        self._cursor.executemany(query, params_seq)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def lastrowid(self):
        return getattr(self._cursor, "lastrowid", None)

    @property
    def description(self):
        return self._cursor.description

    def __getattr__(self, name):
        return getattr(self._cursor, name)

    def close(self):
        self._cursor.close()


class DatabaseConnection:
    def __init__(self, connection, postgres=False):
        self._connection = connection
        self._postgres = postgres

    def cursor(self):
        if self._postgres:
            return DatabaseCursor(
                self._connection.cursor(cursor_factory=RealDictCursor),
                postgres=True,
            )
        return DatabaseCursor(self._connection.cursor(), postgres=False)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def get_connection():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError(
                "DATABASE_URL is configured, but psycopg2-binary is not installed."
            )

        url = os.environ["DATABASE_URL"].strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]

        kwargs = {"connect_timeout": 10}
        # Render PostgreSQL normally provides an SSL-enabled URL. Do not override
        # an explicit sslmode in that URL.
        if "sslmode=" not in url:
            kwargs["sslmode"] = os.getenv("PGSSLMODE", "require")

        return DatabaseConnection(
            psycopg2.connect(url, **kwargs),
            postgres=True,
        )

    raw = sqlite3.connect(
        str(SQLITE_DATABASE_PATH),
        timeout=30,
        check_same_thread=False,
    )
    raw.row_factory = sqlite3.Row
    return DatabaseConnection(raw, postgres=False)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if using_postgres():
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    xp INTEGER NOT NULL DEFAULT 0,
                    level INTEGER NOT NULL DEFAULT 1,
                    streak INTEGER NOT NULL DEFAULT 0,
                    last_workout_date TEXT,
                    total_workouts INTEGER NOT NULL DEFAULT 0,
                    current_challenge TEXT NOT NULL DEFAULT 'No Challenge',
                    session_token_hash TEXT,
                    session_expires_at TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workouts (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    workout_date TEXT NOT NULL,
                    exercise_name TEXT NOT NULL,
                    reps INTEGER NOT NULL DEFAULT 0,
                    form_score REAL NOT NULL DEFAULT 0,
                    xp_earned INTEGER NOT NULL DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    challenge_name TEXT NOT NULL,
                    total_days INTEGER NOT NULL DEFAULT 7,
                    current_day INTEGER NOT NULL DEFAULT 0,
                    start_date TEXT,
                    completed INTEGER NOT NULL DEFAULT 0
                )
            """)

            for statement in (
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS xp INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS streak INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_workout_date TEXT",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS total_workouts INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS current_challenge TEXT DEFAULT 'No Challenge'",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_token_hash TEXT",
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS session_expires_at TEXT",
            ):
                cursor.execute(statement)
        else:
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
                    current_challenge TEXT DEFAULT 'No Challenge',
                    session_token_hash TEXT,
                    session_expires_at TEXT
                )
            """)
            cursor.execute("PRAGMA table_info(users)")
            columns = {row["name"] for row in cursor.fetchall()}
            additions = {
                "password_hash": "ALTER TABLE users ADD COLUMN password_hash TEXT",
                "xp": "ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0",
                "level": "ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1",
                "streak": "ALTER TABLE users ADD COLUMN streak INTEGER DEFAULT 0",
                "last_workout_date": "ALTER TABLE users ADD COLUMN last_workout_date TEXT",
                "total_workouts": "ALTER TABLE users ADD COLUMN total_workouts INTEGER DEFAULT 0",
                "current_challenge": "ALTER TABLE users ADD COLUMN current_challenge TEXT DEFAULT 'No Challenge'",
                "session_token_hash": "ALTER TABLE users ADD COLUMN session_token_hash TEXT",
                "session_expires_at": "ALTER TABLE users ADD COLUMN session_expires_at TEXT",
            }
            for name, statement in additions.items():
                if name not in columns:
                    cursor.execute(statement)

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
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def create_user(username, password_hash):
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        if using_postgres():
            cursor.execute("""
                INSERT INTO users
                    (username, password_hash, xp, level, streak,
                     total_workouts, current_challenge)
                VALUES (?, ?, 0, 1, 0, 0, 'No Challenge')
                RETURNING id
            """, (username, password_hash))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("Database did not return the new user ID.")
            user_id = row["id"]
        else:
            cursor.execute("""
                INSERT INTO users
                    (username, password_hash, xp, level, streak,
                     total_workouts, current_challenge)
                VALUES (?, ?, 0, 1, 0, 0, 'No Challenge')
            """, (username, password_hash))
            user_id = cursor.lastrowid
        connection.commit()
        return int(user_id)
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_user(user_id):
    if user_id is None:
        return None
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        connection.close()


def get_user_by_username(username):
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        connection.close()


def set_session_token(user_id, token_hash, expires_at):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE users SET session_token_hash = ?, session_expires_at = ? WHERE id = ?",
            (token_hash, expires_at, user_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_user_by_session_token(token_hash):
    if not token_hash:
        return None
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM users
            WHERE session_token_hash = ?
              AND session_expires_at > ?
            """,
            (token_hash, datetime.utcnow().isoformat()),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        connection.close()


def clear_session_token(user_id):
    if user_id is None:
        return
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE users SET session_token_hash = NULL, session_expires_at = NULL WHERE id = ?",
            (user_id,),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_all_users():
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT * FROM users ORDER BY xp DESC, total_workouts DESC, streak DESC, username ASC"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        connection.close()


def update_user_stats(user_id, xp, level, streak, last_workout_date):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE users
            SET xp = ?, level = ?, streak = ?, last_workout_date = ?
            WHERE id = ?
            """,
            (xp, level, streak, last_workout_date, user_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_leaderboard(limit=None):
    users = get_all_users()
    leaderboard = []
    for rank, user in enumerate(users, start=1):
        user["rank"] = rank
        leaderboard.append(user)
    return leaderboard[:limit] if limit is not None else leaderboard


def get_user_rank(user_id):
    for user in get_leaderboard():
        if user["id"] == user_id:
            return user["rank"]
    return None


def save_workout(user_id, exercise_name, reps, form_score, xp_earned):
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO workouts
                (user_id, workout_date, exercise_name, reps, form_score, xp_earned)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, date.today().isoformat(), exercise_name, reps, form_score, xp_earned),
        )
        cursor.execute(
            "UPDATE users SET total_workouts = COALESCE(total_workouts, 0) + 1 WHERE id = ?",
            (user_id,),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_workout_history(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM workouts WHERE user_id = ? ORDER BY id DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        connection.close()


def get_recent_workouts(user_id, limit=10):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT * FROM workouts WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        connection.close()


def get_total_workout_count(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM workouts WHERE user_id = ?", (user_id,))
        return int(cursor.fetchone()["total"])
    finally:
        cursor.close()
        connection.close()


def get_today_workout_count(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) AS total FROM workouts WHERE user_id = ? AND workout_date = ?",
            (user_id, date.today().isoformat()),
        )
        return int(cursor.fetchone()["total"])
    finally:
        cursor.close()
        connection.close()


def get_average_form_score(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT AVG(form_score) AS average_score FROM workouts WHERE user_id = ?",
            (user_id,),
        )
        result = cursor.fetchone()
        value = result["average_score"] if result else None
        return 0 if value is None else round(float(value), 1)
    finally:
        cursor.close()
        connection.close()


def accept_challenge(challenge_name, total_days, user_id):
    initialize_database()
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO challenges
                (user_id, challenge_name, total_days, current_day, start_date, completed)
            VALUES (?, ?, ?, 0, ?, 0)
            """,
            (user_id, challenge_name, total_days, date.today().isoformat()),
        )
        cursor.execute(
            "UPDATE users SET current_challenge = ? WHERE id = ?",
            (challenge_name, user_id),
        )
        connection.commit()
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_active_challenge(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT * FROM challenges
            WHERE user_id = ? AND completed = 0
            ORDER BY id DESC LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        connection.close()


def update_challenge_progress(user_id):
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT * FROM challenges WHERE user_id = ? AND completed = 0",
            (user_id,),
        )
        challenges = cursor.fetchall()
        for challenge in challenges:
            new_day = int(challenge["current_day"]) + 1
            completed = 0
            if new_day >= int(challenge["total_days"]):
                new_day = int(challenge["total_days"])
                completed = 1

            cursor.execute(
                "UPDATE challenges SET current_day = ?, completed = ? WHERE id = ?",
                (new_day, completed, challenge["id"]),
            )
            if completed:
                cursor.execute(
                    "UPDATE users SET current_challenge = ? WHERE id = ?",
                    ("No Challenge", user_id),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
