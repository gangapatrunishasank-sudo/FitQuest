"""
FitQuest AI - AI Workout Arena
Stable WebRTC camera + MediaPipe pose detection.

Supported exercises:
- Bicep Curl
- Push Up

Designed for:
- Python 3.11
- MediaPipe 0.10.18
- Streamlit
- streamlit-webrtc
"""

import math
import threading
import time

import av
import cv2
import mediapipe as mp
import streamlit as st
from streamlit_webrtc import (
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)

from utils.auth import (
    initialize_auth,
    get_current_user_id,
    is_logged_in,
)
from utils.database import get_user
from utils.gamification import complete_workout
from utils.ui import apply_fitquest_theme


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Workout | FitQuest AI",
    page_icon="🏋️",
    layout="wide",
)

apply_fitquest_theme()
initialize_auth()


# ============================================================
# LOGIN CHECK
# ============================================================

if not is_logged_in():

    st.title("🏋️ AI Workout Arena")

    st.warning(
        "🔐 Please log in before using the AI workout."
    )

    st.info(
        "Go back to the FitQuest home page and log in first."
    )

    st.stop()


# ============================================================
# LOAD CURRENT USER
# ============================================================

current_user_id = get_current_user_id()

user = get_user(current_user_id)

if user is None:

    st.error(
        "Your account could not be loaded from the database."
    )

    st.info(
        "Please log out, log in again, and reopen AI Workout."
    )

    st.stop()


# ============================================================
# MEDIAPIPE
# ============================================================

try:

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles

except AttributeError:

    st.error(
        "MediaPipe is installed, but the installed version "
        "does not support the AI Workout code."
    )

    st.code(
        '.\\.venv\\Scripts\\python.exe '
        '-m pip install "mediapipe==0.10.18"',
        language="powershell",
    )

    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "selected_ai_exercise" not in st.session_state:

    st.session_state.selected_ai_exercise = "Bicep Curl"


if "last_ai_result" not in st.session_state:

    st.session_state.last_ai_result = None


if "saved_ai_workout" not in st.session_state:

    st.session_state.saved_ai_workout = None


# ============================================================
# ANGLE CALCULATION
# ============================================================

def calculate_angle(a, b, c):
    """
    Calculate angle ABC.

    a, b and c are (x, y) coordinates.
    """

    ab = (
        a[0] - b[0],
        a[1] - b[1],
    )

    cb = (
        c[0] - b[0],
        c[1] - b[1],
    )

    denominator = (
        math.hypot(*ab)
        *
        math.hypot(*cb)
    )

    if denominator <= 0.000001:

        return 0.0

    cosine = (
        (ab[0] * cb[0])
        +
        (ab[1] * cb[1])
    ) / denominator

    cosine = max(
        -1.0,
        min(1.0, cosine),
    )

    return math.degrees(
        math.acos(cosine)
    )


# ============================================================
# BICEP ANALYSIS
# ============================================================

def analyze_bicep(angle):

    if angle <= 70:

        return (
            100,
            "Strong Curl",
            "Excellent contraction. Now extend your arm.",
        )

    if angle <= 100:

        return (
            96,
            "Curling",
            "Good movement. Keep curling smoothly.",
        )

    if angle <= 125:

        return (
            90,
            "Mid Movement",
            "Continue the curl.",
        )

    if angle <= 155:

        return (
            88,
            "Returning",
            "Keep extending your arm.",
        )

    return (
        92,
        "Ready",
        "Good starting position. Curl upward.",
    )


# ============================================================
# PUSH-UP ANALYSIS
# ============================================================

def analyze_pushup(angle):

    if angle <= 95:

        return (
            100,
            "Bottom Position",
            "Good depth. Push upward.",
        )

    if angle <= 120:

        return (
            94,
            "Lowering",
            "Good. Continue smoothly.",
        )

    if angle <= 145:

        return (
            88,
            "Moving",
            "Continue the movement.",
        )

    return (
        92,
        "Top Position",
        "Good position. Lower yourself.",
    )


# ============================================================
# AI VIDEO PROCESSOR
# ============================================================

class PoseVideoProcessor(VideoProcessorBase):

    def __init__(self, exercise):

        self.exercise = exercise

        # Lightweight MediaPipe configuration.
        # This is intentionally model_complexity=0
        # to make the application smoother.

        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.35,
            min_tracking_confidence=0.35,
        )

        # ----------------------------------------------------
        # Workout state
        # ----------------------------------------------------

        self.reps = 0

        self.current_angle = 0.0

        self.current_score = 0.0

        self.current_status = "Starting Camera"

        self.current_feedback = (
            "Allow camera access and stand in view."
        )

        self.landmarks_detected = False

        # ----------------------------------------------------
        # Rep state
        # ----------------------------------------------------

        self.stage = "waiting"

        self.last_rep_time = 0.0

        self.minimum_rep_interval = 0.60

        # ----------------------------------------------------
        # Smoothing
        # ----------------------------------------------------

        self.angle_history = []

        # ----------------------------------------------------
        # Workout score
        # ----------------------------------------------------

        self.total_score = 0.0

        self.score_samples = 0

        self.start_time = time.time()

        # ----------------------------------------------------
        # Thread safety
        # ----------------------------------------------------

        self.state_lock = threading.Lock()


    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        try:

            self.pose.close()

        except Exception:

            pass


    # ========================================================
    # SMOOTH ANGLE
    # ========================================================

    def smooth_angle(self, angle):

        self.angle_history.append(
            float(angle)
        )

        if len(self.angle_history) > 3:

            self.angle_history.pop(0)

        return (
            sum(self.angle_history)
            /
            len(self.angle_history)
        )


    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(self):

        with self.state_lock:

            return {

                "reps": int(self.reps),

                "current_angle": round(
                    float(self.current_angle),
                    1,
                ),

                "current_score": round(
                    float(self.current_score),
                    1,
                ),

                "current_status":
                    self.current_status,

                "current_feedback":
                    self.current_feedback,

                "landmarks_detected":
                    bool(self.landmarks_detected),

                "stage":
                    self.stage,

                "total_score":
                    float(self.total_score),

                "score_samples":
                    int(self.score_samples),

                "start_time":
                    float(self.start_time),
            }


    # ========================================================
    # REGISTER REP
    # ========================================================

    def register_rep(self):

        now = time.time()

        if (
            now - self.last_rep_time
            <
            self.minimum_rep_interval
        ):

            return False

        self.reps += 1

        self.last_rep_time = now

        self.total_score += (
            self.current_score
        )

        self.score_samples += 1

        return True


    # ========================================================
    # BICEP CURL COUNTING
    # ========================================================

    def count_bicep_curl(self, angle):

        # Starting position
        if self.stage == "waiting":

            if angle >= 125:

                self.stage = "ready"

                self.current_status = (
                    "Ready for Curl"
                )

                self.current_feedback = (
                    "Now curl your arm."
                )

            else:

                self.current_status = (
                    "Get Ready"
                )

                self.current_feedback = (
                    "Start with your arm mostly straight."
                )

            return


        # Begin curl
        if self.stage == "ready":

            if angle <= 115:

                self.stage = "curling"

                self.current_status = (
                    "Curling"
                )

                self.current_feedback = (
                    "Good. Keep curling."
                )

            return


        # Reach top
        if self.stage == "curling":

            if angle <= 100:

                self.stage = "top"

                self.current_status = (
                    "Top Position"
                )

                self.current_feedback = (
                    "Great. Now lower your arm."
                )

            return


        # Start returning
        if self.stage == "top":

            if angle >= 115:

                self.stage = "returning"

                self.current_status = (
                    "Returning"
                )

                self.current_feedback = (
                    "Extend your arm."
                )

            return


        # Complete repetition
        if self.stage == "returning":

            if angle >= 125:

                if self.register_rep():

                    self.stage = "ready"

                    self.current_status = (
                        "REP COUNTED"
                    )

                    self.current_feedback = (
                        "Excellent! Repetition counted."
                    )


    # ========================================================
    # PUSH-UP COUNTING
    # ========================================================

    def count_push_up(self, angle):

        # Starting position
        if self.stage == "waiting":

            if angle >= 145:

                self.stage = "ready"

                self.current_status = (
                    "Ready for Push Up"
                )

                self.current_feedback = (
                    "Lower yourself."
                )

            else:

                self.current_status = (
                    "Get Ready"
                )

                self.current_feedback = (
                    "Start in a straighter position."
                )

            return


        # Start lowering
        if self.stage == "ready":

            if angle <= 130:

                self.stage = "lowering"

                self.current_status = (
                    "Lowering"
                )

                self.current_feedback = (
                    "Good. Keep going."
                )

            return


        # Bottom
        if self.stage == "lowering":

            if angle <= 110:

                self.stage = "bottom"

                self.current_status = (
                    "Bottom Position"
                )

                self.current_feedback = (
                    "Good depth. Push upward."
                )

            return


        # Push upward
        if self.stage == "bottom":

            if angle >= 130:

                self.stage = "pushing"

                self.current_status = (
                    "Pushing Up"
                )

                self.current_feedback = (
                    "Push back up."
                )

            return


        # Complete
        if self.stage == "pushing":

            if angle >= 145:

                if self.register_rep():

                    self.stage = "ready"

                    self.current_status = (
                        "REP COUNTED"
                    )

                    self.current_feedback = (
                        "Excellent! Repetition counted."
                    )


    # ========================================================
    # RECEIVE CAMERA FRAME
    # ========================================================

    def recv(self, frame):

        # Always create an image first.
        # This prevents an exception from killing the track.

        image = frame.to_ndarray(
            format="bgr24"
        )

        try:

            # Mirror camera.
            image = cv2.flip(
                image,
                1,
            )

            # Convert BGR -> RGB.
            rgb = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2RGB,
            )

            # MediaPipe pose detection.
            results = self.pose.process(
                rgb
            )

            with self.state_lock:

                self.landmarks_detected = False


            # ------------------------------------------------
            # Pose found
            # ------------------------------------------------

            if results.pose_landmarks:

                landmarks = (
                    results.pose_landmarks.landmark
                )

                # Right arm
                right_ids = [

                    mp_pose.PoseLandmark.RIGHT_SHOULDER,

                    mp_pose.PoseLandmark.RIGHT_ELBOW,

                    mp_pose.PoseLandmark.RIGHT_WRIST,

                ]

                # Left arm
                left_ids = [

                    mp_pose.PoseLandmark.LEFT_SHOULDER,

                    mp_pose.PoseLandmark.LEFT_ELBOW,

                    mp_pose.PoseLandmark.LEFT_WRIST,

                ]

                right_points = [

                    landmarks[index.value]

                    for index in right_ids

                ]

                left_points = [

                    landmarks[index.value]

                    for index in left_ids

                ]

                right_visibility = min(

                    float(point.visibility)

                    for point in right_points

                )

                left_visibility = min(

                    float(point.visibility)

                    for point in left_points

                )

                # Use the side that is more visible.
                if (
                    right_visibility
                    >=
                    left_visibility
                ):

                    points = right_points

                    visibility = right_visibility

                else:

                    points = left_points

                    visibility = left_visibility


                # ------------------------------------------------
                # Calculate angle
                # ------------------------------------------------

                if visibility >= 0.25:

                    height, width = image.shape[:2]

                    shoulder, elbow, wrist = points

                    shoulder_point = (

                        shoulder.x * width,

                        shoulder.y * height,

                    )

                    elbow_point = (

                        elbow.x * width,

                        elbow.y * height,

                    )

                    wrist_point = (

                        wrist.x * width,

                        wrist.y * height,

                    )

                    raw_angle = calculate_angle(

                        shoulder_point,

                        elbow_point,

                        wrist_point,

                    )

                    angle = self.smooth_angle(
                        raw_angle
                    )


                    # ------------------------------------------------
                    # AI scoring
                    # ------------------------------------------------

                    if self.exercise == "Bicep Curl":

                        score, status, feedback = (
                            analyze_bicep(angle)
                        )

                    else:

                        score, status, feedback = (
                            analyze_pushup(angle)
                        )


                    # ------------------------------------------------
                    # Update state
                    # ------------------------------------------------

                    with self.state_lock:

                        self.landmarks_detected = True

                        self.current_angle = angle

                        self.current_score = score

                        self.current_status = status

                        self.current_feedback = feedback


                        if (
                            self.exercise
                            ==
                            "Bicep Curl"
                        ):

                            self.count_bicep_curl(
                                angle
                            )

                        else:

                            self.count_push_up(
                                angle
                            )


                    # Angle label
                    cv2.putText(

                        image,

                        f"Angle: {int(angle)}",

                        (
                            int(elbow.x * width) + 10,
                            int(elbow.y * height) - 10,
                        ),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.75,

                        (0, 255, 0),

                        2,

                    )


                else:

                    with self.state_lock:

                        self.current_status = (
                            "Pose Not Clear"
                        )

                        self.current_feedback = (
                            "Move closer and keep "
                            "your shoulder, elbow and "
                            "wrist visible."
                        )


                # Draw MediaPipe landmarks.
                mp_drawing.draw_landmarks(

                    image,

                    results.pose_landmarks,

                    mp_pose.POSE_CONNECTIONS,

                    landmark_drawing_spec=(
                        mp_drawing_styles
                        .get_default_pose_landmarks_style()
                    ),

                )


            # ------------------------------------------------
            # No pose
            # ------------------------------------------------

            else:

                with self.state_lock:

                    self.current_status = (
                        "No Pose Detected"
                    )

                    self.current_feedback = (
                        "Stand in front of the camera "
                        "with your upper body visible."
                    )


            # ------------------------------------------------
            # Camera overlay
            # ------------------------------------------------

            snapshot = self.snapshot()

            cv2.rectangle(

                image,

                (10, 10),

                (380, 205),

                (0, 0, 0),

                -1,

            )

            cv2.putText(

                image,

                f"REPS: {snapshot['reps']}",

                (25, 50),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.9,

                (0, 255, 0),

                2,

            )

            cv2.putText(

                image,

                f"ANGLE: {int(snapshot['current_angle'])}",

                (25, 90),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.72,

                (255, 255, 255),

                2,

            )

            cv2.putText(

                image,

                f"STAGE: {snapshot['stage']}",

                (25, 130),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.68,

                (255, 255, 255),

                2,

            )

            cv2.putText(

                image,

                f"SCORE: {int(snapshot['current_score'])}",

                (25, 170),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.68,

                (255, 255, 255),

                2,

            )


        except Exception:

            # Keep the camera alive even if one frame fails.
            with self.state_lock:

                self.current_status = (
                    "AI Frame Error"
                )

                self.current_feedback = (
                    "Camera is connected. "
                    "AI is recovering..."
                )


        return av.VideoFrame.from_ndarray(
            image,
            format="bgr24",
        )


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "🏋️ AI Workout Arena"
)

st.write(
    f"Welcome, **{user.get('username', 'FitQuest Player')}**. "
    "Use your camera to count repetitions and check your movement."
)


# ============================================================
# USER STATS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "⭐ XP",
    user.get("xp", 0),
)

col2.metric(
    "🏆 Level",
    user.get("level", 1),
)

col3.metric(
    "🔥 Streak",
    f"{user.get('streak', 0)} Days",
)

col4.metric(
    "💪 Workouts",
    user.get("total_workouts", 0),
)


st.divider()


# ============================================================
# EXERCISE SELECTION
# ============================================================

selected_exercise = st.selectbox(

    "Choose exercise",

    [
        "Bicep Curl",
        "Push Up",
    ],

    index=(
        0
        if st.session_state.selected_ai_exercise
        ==
        "Bicep Curl"
        else
        1
    ),

)


st.session_state.selected_ai_exercise = (
    selected_exercise
)


# ============================================================
# INSTRUCTIONS
# ============================================================

if selected_exercise == "Bicep Curl":

    st.info(
        "📷 Stand side-on to the camera. "
        "Keep your shoulder, elbow and wrist visible. "
        "Start with your arm mostly straight, curl upward, "
        "then return to the starting position."
    )

else:

    st.info(
        "📷 For push-ups, position the camera side-on. "
        "Keep your shoulder, elbow and wrist visible. "
        "Start straight, lower yourself, then push upward."
    )


# ============================================================
# CAMERA
# ============================================================

st.subheader(
    "📷 Live AI Camera"
)

st.caption(
    "Click START inside the camera box. "
    "When Chrome asks for camera permission, choose Allow."
)


# ------------------------------------------------------------
# IMPORTANT:
# Keep ICE configuration simple.
# ------------------------------------------------------------

ICE_SERVERS = [

    {
        "urls":
        ["stun:stun.l.google.com:19302"]
    },

    {
        "urls":
        ["stun:stun.cloudflare.com:3478"]
    },

]


exercise_key = (
    selected_exercise
    .lower()
    .replace(" ", "-")
)


# ------------------------------------------------------------
# WebRTC
# ------------------------------------------------------------

webrtc_ctx = webrtc_streamer(

    key=(
        "fitquest-ai-camera-"
        + exercise_key
    ),

    mode=WebRtcMode.SENDRECV,

    media_stream_constraints={

        "video": {

            "width": {
                "ideal": 640
            },

            "height": {
                "ideal": 480
            },

            "frameRate": {
                "ideal": 20,
                "max": 24,
            },

            "facingMode": "user",

        },

        "audio": False,

    },

    video_processor_factory=lambda:
        PoseVideoProcessor(
            selected_exercise
        ),

    async_processing=True,

    rtc_configuration={
        "iceServers":
        ICE_SERVERS
    },

)


# ============================================================
# CAMERA STATUS
# ============================================================

if webrtc_ctx.state.playing:

    st.success(
        "🟢 Camera connected. "
        "AI is analyzing your movement."
    )

elif webrtc_ctx.state.signalling:

    st.info(
        "🔄 Connecting to camera..."
    )

else:

    st.info(
        "Press START above the camera to begin."
    )


# ============================================================
# LIVE AI ANALYSIS
# ============================================================

if webrtc_ctx.video_processor:

    live = (
        webrtc_ctx
        .video_processor
        .snapshot()
    )

    st.divider()

    st.subheader(
        "🤖 Live AI Analysis"
    )

    a, b, c, d = st.columns(4)

    a.metric(
        "🔁 Reps",
        live["reps"],
    )

    b.metric(
        "📐 Angle",
        f"{live['current_angle']}°",
    )

    c.metric(
        "⭐ Form",
        f"{live['current_score']:.0f}/100",
    )

    d.metric(
        "🔄 Stage",
        live["stage"].title(),
    )

    st.info(
        f"**Status:** "
        f"{live['current_status']} — "
        f"{live['current_feedback']}"
    )

    if live["landmarks_detected"]:

        st.success(
            "✅ Body landmarks detected."
        )

    else:

        st.warning(
            "⚠️ Waiting for a clear pose."
        )


# ============================================================
# SAVE WORKOUT
# ============================================================

st.divider()

st.subheader(
    "🏁 Complete Workout"
)

st.write(
    "After at least one repetition is counted, "
    "save the workout to your FitQuest account."
)


if st.button(
    "🏆 Complete and Save Workout",
    use_container_width=True,
):

    if not webrtc_ctx.video_processor:

        st.error(
            "Please start the camera first."
        )

    else:

        workout_state = (
            webrtc_ctx
            .video_processor
            .snapshot()
        )

        reps = int(
            workout_state["reps"]
        )


        if reps <= 0:

            st.warning(
                "No repetition has been counted yet. "
                "Complete at least one full repetition."
            )

        else:

            if (
                workout_state["score_samples"]
                > 0
            ):

                form_score = round(

                    workout_state[
                        "total_score"
                    ]
                    /
                    workout_state[
                        "score_samples"
                    ],

                    1,

                )

            else:

                form_score = round(

                    workout_state[
                        "current_score"
                    ],

                    1,

                )


            workout_key = (

                f"{current_user_id}-"
                f"{selected_exercise}-"
                f"{workout_state['start_time']}-"
                f"{reps}"

            )


            if (
                st.session_state.saved_ai_workout
                ==
                workout_key
            ):

                st.warning(
                    "This workout has already been saved."
                )

            else:

                try:

                    result = complete_workout(

                        user_id=current_user_id,

                        exercise_name=selected_exercise,

                        reps=reps,

                        form_score=form_score,

                    )

                    st.session_state.saved_ai_workout = (
                        workout_key
                    )

                    st.session_state.last_ai_result = (
                        result
                    )

                    st.success(
                        "🎉 Workout saved successfully!"
                    )

                except Exception as error:

                    st.error(
                        f"Could not save workout: {error}"
                    )


# ============================================================
# WORKOUT RESULT
# ============================================================

if st.session_state.last_ai_result:

    result = (
        st.session_state.last_ai_result
    )

    st.divider()

    st.subheader(
        "🎉 Workout Result"
    )

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "🔁 Reps",
        result.get("reps", 0),
    )

    r2.metric(
        "⭐ XP Earned",
        result.get("xp_earned", 0),
    )

    r3.metric(
        "🏆 Level",
        result.get("level", 1),
    )

    st.success(
        f"🔥 Streak: "
        f"{result.get('streak', 0)} Days"
    )

    st.success(
        f"⭐ Total XP: "
        f"{result.get('total_xp', 0)}"
    )