from pathlib import Path
import sys
from datetime import datetime

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
    page_title="AI Safety Coach | FitQuest AI",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# DATABASE IMPORT
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
# INITIALIZE DATABASE
# ============================================================

if DATABASE_AVAILABLE:

    try:
        initialize_database()

    except Exception as error:
        DATABASE_AVAILABLE = False
        DATABASE_ERROR = str(error)


# ============================================================
# USER FUNCTION
# ============================================================

def get_user():

    default_user = {
        "username": "FitQuest Player",
        "level": 1,
        "streak": 0
    }

    if not DATABASE_AVAILABLE:
        return default_user

    try:

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE id = 1
        """)

        user = cursor.fetchone()

        connection.close()

        if user:
            return dict(user)

        return default_user

    except Exception:

        return default_user


# ============================================================
# AI SAFETY ANALYSIS
# ============================================================

def get_safety_guidance(
    pain_area,
    pain_level,
    symptom_type
):

    result = {
        "title": "",
        "message": "",
        "recommendations": [],
        "alternative": "",
        "emergency": False
    }

    # --------------------------------------------------------
    # HIGH SEVERITY
    # --------------------------------------------------------

    if pain_level in [
        "Severe",
        "Very Severe"
    ]:

        result["title"] = (
            "⚠️ Stop the Exercise"
        )

        result["message"] = (
            "Do not continue the current exercise while "
            "experiencing severe or very severe pain."
        )

        result["recommendations"] = [
            "Stop the exercise immediately.",
            "Do not push through severe pain.",
            "Rest the affected area.",
            "Consider consulting a qualified healthcare professional."
        ]

        result["alternative"] = (
            "Choose rest and recovery instead of continuing "
            "the current workout."
        )

        result["emergency"] = True

        return result

    # --------------------------------------------------------
    # KNEE GUIDANCE
    # --------------------------------------------------------

    if pain_area == "Knee":

        result["title"] = (
            "🦵 Knee Safety Guidance"
        )

        result["message"] = (
            "Reduce movements that create discomfort in the knee."
        )

        result["recommendations"] = [
            "Reduce squat depth if it causes discomfort.",
            "Avoid sudden jumping movements.",
            "Keep knee movement controlled.",
            "Reduce workout intensity.",
            "Focus on stable and balanced movement."
        ]

        result["alternative"] = (
            "Try lower-impact movements such as gentle walking "
            "or controlled mobility exercises."
        )

    # --------------------------------------------------------
    # LOWER BACK GUIDANCE
    # --------------------------------------------------------

    elif pain_area == "Lower Back":

        result["title"] = (
            "🔙 Lower Back Safety Guidance"
        )

        result["message"] = (
            "Avoid exercises that increase strain or discomfort "
            "in your lower back."
        )

        result["recommendations"] = [
            "Avoid excessive bending or twisting.",
            "Keep your movements slow and controlled.",
            "Focus on neutral body alignment.",
            "Reduce resistance or repetitions.",
            "Stop if discomfort increases."
        ]

        result["alternative"] = (
            "Choose gentle mobility or lower-intensity exercises "
            "until you can exercise comfortably."
        )

    # --------------------------------------------------------
    # SHOULDER GUIDANCE
    # --------------------------------------------------------

    elif pain_area == "Shoulder":

        result["title"] = (
            "💪 Shoulder Safety Guidance"
        )

        result["message"] = (
            "Reduce movements that increase shoulder discomfort."
        )

        result["recommendations"] = [
            "Avoid painful overhead movements.",
            "Reduce exercise range of motion.",
            "Avoid forcing the shoulder through pain.",
            "Use controlled movements.",
            "Reduce resistance and intensity."
        ]

        result["alternative"] = (
            "Choose movements that do not cause shoulder discomfort."
        )

    # --------------------------------------------------------
    # WRIST GUIDANCE
    # --------------------------------------------------------

    elif pain_area == "Wrist":

        result["title"] = (
            "✋ Wrist Safety Guidance"
        )

        result["message"] = (
            "Avoid placing excessive pressure on the painful wrist."
        )

        result["recommendations"] = [
            "Avoid painful weight-bearing positions.",
            "Keep the wrist in a comfortable position.",
            "Reduce exercise intensity.",
            "Take breaks between sets."
        ]

        result["alternative"] = (
            "Try exercises that do not require painful wrist loading."
        )

    # --------------------------------------------------------
    # NECK GUIDANCE
    # --------------------------------------------------------

    elif pain_area == "Neck":

        result["title"] = (
            "🧠 Neck Safety Guidance"
        )

        result["message"] = (
            "Avoid forcing your neck into uncomfortable positions."
        )

        result["recommendations"] = [
            "Keep your neck relaxed.",
            "Avoid sudden neck movements.",
            "Do not force extreme positions.",
            "Maintain comfortable alignment."
        ]

        result["alternative"] = (
            "Choose low-intensity exercises while keeping the neck relaxed."
        )

    # --------------------------------------------------------
    # GENERAL GUIDANCE
    # --------------------------------------------------------

    else:

        result["title"] = (
            "🛡️ General Safety Guidance"
        )

        result["message"] = (
            "Listen to your body and reduce intensity if discomfort increases."
        )

        result["recommendations"] = [
            "Slow down your movements.",
            "Reduce repetitions.",
            "Reduce workout intensity.",
            "Take a short rest.",
            "Stop the exercise if pain increases."
        ]

        result["alternative"] = (
            "Choose a lower-intensity workout or recovery session."
        )

    # --------------------------------------------------------
    # SYMPTOM-SPECIFIC MESSAGE
    # --------------------------------------------------------

    if symptom_type == "Sharp Pain":

        result["recommendations"].insert(
            0,
            "Sharp pain should not be ignored. Stop if it continues."
        )

    elif symptom_type == "Burning Sensation":

        result["recommendations"].insert(
            0,
            "Reduce intensity and stop if the burning sensation increases."
        )

    elif symptom_type == "Stiffness":

        result["recommendations"].insert(
            0,
            "Use gentle movements and avoid forcing painful positions."
        )

    elif symptom_type == "Muscle Fatigue":

        result["recommendations"].insert(
            0,
            "Take adequate rest and avoid training beyond safe fatigue."
        )

    return result


# ============================================================
# LOAD USER
# ============================================================

user = get_user()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("🛡️ FitQuest AI Safety Coach")

st.write(
    f"Hello **{user['username']}**. "
    "Tell the AI Coach how you feel before continuing your workout."
)


# ============================================================
# SAFETY WARNING
# ============================================================

st.warning(
    "FitQuest AI provides general fitness and safety guidance only. "
    "It does not diagnose injuries or replace professional medical advice."
)


# ============================================================
# PAIN CHECK
# ============================================================

st.divider()

st.subheader(
    "🩺 How Are You Feeling?"
)

pain_area = st.selectbox(
    "Where are you experiencing discomfort?",
    [
        "No Specific Area",
        "Knee",
        "Lower Back",
        "Shoulder",
        "Wrist",
        "Neck"
    ]
)

pain_level = st.select_slider(
    "How strong is the discomfort?",
    options=[
        "None",
        "Mild",
        "Moderate",
        "Severe",
        "Very Severe"
    ],
    value="None"
)

symptom_type = st.selectbox(
    "What does it feel like?",
    [
        "General Discomfort",
        "Muscle Fatigue",
        "Stiffness",
        "Sharp Pain",
        "Burning Sensation"
    ]
)


# ============================================================
# ADDITIONAL INFORMATION
# ============================================================

st.subheader(
    "📝 Additional Information"
)

user_note = st.text_area(
    "Describe what you are feeling (optional)",
    placeholder=(
        "Example: My knee feels uncomfortable during squats."
    )
)


# ============================================================
# ANALYZE BUTTON
# ============================================================

st.divider()

if st.button(
    "🧠 Analyze My Workout Safety",
    type="primary",
    use_container_width=True
):

    if pain_level == "None":

        st.success(
            "✅ No significant discomfort reported. "
            "Continue exercising with good posture and controlled movement."
        )

        st.info(
            "Remember to warm up, stay hydrated and stop "
            "if you begin experiencing unusual pain."
        )

    else:

        guidance = get_safety_guidance(
            pain_area,
            pain_level,
            symptom_type
        )

        st.subheader(
            guidance["title"]
        )

        if guidance["emergency"]:

            st.error(
                guidance["message"]
            )

        else:

            st.warning(
                guidance["message"]
            )

        st.subheader(
            "🤖 AI Coach Recommendations"
        )

        for recommendation in guidance[
            "recommendations"
        ]:

            st.write(
                f"• {recommendation}"
            )

        st.subheader(
            "🔄 Safer Alternative"
        )

        st.info(
            guidance["alternative"]
        )

        if user_note.strip():

            st.caption(
                f"Your note was recorded for this session at "
                f"{datetime.now().strftime('%H:%M')}."
            )


# ============================================================
# SAFETY CHECKLIST
# ============================================================

st.divider()

st.subheader(
    "✅ Quick Safety Checklist"
)

check_col1, check_col2 = st.columns(2)

with check_col1:

    st.write("✓ Warm up before exercising")
    st.write("✓ Use controlled movements")
    st.write("✓ Maintain correct posture")

with check_col2:

    st.write("✓ Stay hydrated")
    st.write("✓ Rest when needed")
    st.write("✓ Do not ignore severe pain")


# ============================================================
# SYSTEM STATUS
# ============================================================

with st.expander(
    "🔧 AI Safety System Status"
):

    if DATABASE_AVAILABLE:

        st.success(
            "FitQuest user system connected successfully."
        )

    else:

        st.error(
            f"Database error: {DATABASE_ERROR}"
        )