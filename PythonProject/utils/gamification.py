from datetime import date, timedelta

from utils.database import (
    get_user,
    get_today_workout_count,
    save_workout,
    update_user_stats,
    update_challenge_progress
)


# ============================================================
# LEVEL SYSTEM
# ============================================================

def calculate_level(xp):
    """
    Calculate the user's level.

    Every 500 XP gives one new level.
    """

    return (xp // 500) + 1


# ============================================================
# XP SYSTEM
# ============================================================

def calculate_xp(form_score):
    """
    Calculate XP based on workout form score.
    """

    xp_earned = 100


    if form_score >= 90:

        xp_earned += 50


    elif form_score >= 75:

        xp_earned += 25


    return xp_earned


# ============================================================
# STREAK SYSTEM
# ============================================================

def calculate_new_streak(user):
    """
    Calculate the new streak for one specific user.

    The streak increases only once per day.
    """

    today = date.today()

    last_workout = user.get(
        "last_workout_date"
    )

    current_streak = int(
        user.get(
            "streak",
            0
        ) or 0
    )


    # --------------------------------------------------------
    # FIRST WORKOUT
    # --------------------------------------------------------

    if not last_workout:

        return 1


    try:

        last_date = date.fromisoformat(
            last_workout
        )

    except ValueError:

        return 1


    # --------------------------------------------------------
    # ALREADY WORKED OUT TODAY
    # --------------------------------------------------------

    if last_date == today:

        return current_streak


    # --------------------------------------------------------
    # WORKED OUT YESTERDAY
    # --------------------------------------------------------

    if last_date == (
        today - timedelta(days=1)
    ):

        return current_streak + 1


    # --------------------------------------------------------
    # STREAK BROKEN
    # --------------------------------------------------------

    return 1


# ============================================================
# COMPLETE WORKOUT
# ============================================================

def complete_workout(
        user_id,
        exercise_name,
        reps,
        form_score
):
    """
    Complete a workout for one specific logged-in user.

    Flow:

    1. Load the correct user
    2. Check today's workout count
    3. Calculate XP
    4. Calculate level
    5. Calculate streak
    6. Save workout
    7. Increase workout count
    8. Update user XP and statistics
    9. Update the user's challenge progress
    """

    # --------------------------------------------------------
    # LOAD CURRENT USER
    # --------------------------------------------------------

    user = get_user(
        user_id
    )


    if user is None:

        raise Exception(
            "User not found in database."
        )


    # --------------------------------------------------------
    # CHECK TODAY'S WORKOUT COUNT
    # --------------------------------------------------------

    workouts_before = get_today_workout_count(
        user_id
    )


    # --------------------------------------------------------
    # CALCULATE XP
    # --------------------------------------------------------

    xp_earned = calculate_xp(
        form_score
    )


    current_xp = int(
        user.get(
            "xp",
            0
        ) or 0
    )


    new_xp = (
        current_xp + xp_earned
    )


    # --------------------------------------------------------
    # CALCULATE LEVEL
    # --------------------------------------------------------

    new_level = calculate_level(
        new_xp
    )


    # --------------------------------------------------------
    # CALCULATE STREAK
    # --------------------------------------------------------

    new_streak = calculate_new_streak(
        user
    )


    # --------------------------------------------------------
    # SAVE WORKOUT
    # --------------------------------------------------------

    save_workout(
        user_id=user_id,
        exercise_name=exercise_name,
        reps=reps,
        form_score=form_score,
        xp_earned=xp_earned
    )


    # --------------------------------------------------------
    # UPDATE USER STATISTICS
    # --------------------------------------------------------

    update_user_stats(
        user_id=user_id,
        xp=new_xp,
        level=new_level,
        streak=new_streak,
        last_workout_date=date.today().isoformat()
    )


    # --------------------------------------------------------
    # UPDATE CHALLENGE
    # --------------------------------------------------------

    # Challenge progress should increase
    # only for the first workout of the day.

    if workouts_before == 0:

        update_challenge_progress(
            user_id
        )


    # --------------------------------------------------------
    # RETURN WORKOUT RESULT
    # --------------------------------------------------------

    return {
        "user_id": user_id,
        "exercise": exercise_name,
        "reps": reps,
        "form_score": form_score,
        "xp_earned": xp_earned,
        "total_xp": new_xp,
        "level": new_level,
        "streak": new_streak
    }