from pathlib import Path
import sys
import math
import time
import threading

import av
import cv2
import mediapipe as mp
import streamlit as st

from streamlit_webrtc import (
    VideoProcessorBase,
    WebRtcMode,
    webrtc_streamer,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Workout | FitQuest AI",
    page_icon="🏋️",
    layout="wide",
)


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from utils.database import get_user
from utils.gamification import complete_workout
from utils.auth import (
    initialize_auth,
    get_current_user_id,
    is_logged_in,
)


# ============================================================
# INITIALIZE AUTHENTICATION
# ============================================================

initialize_auth()


# ============================================================
# LOGIN CHECK
# ============================================================

if not is_logged_in():

    st.title("🏋️ AI Workout Arena")

    st.warning(
        "Please log in before starting an AI workout."
    )

    st.stop()


# ============================================================
# CURRENT USER
# ============================================================

current_user_id = get_current_user_id()


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


# ============================================================
# SESSION STATE
# ============================================================

if "last_workout_result" not in st.session_state:
    st.session_state.last_workout_result = None


if "saved_workout_key" not in st.session_state:
    st.session_state.saved_workout_key = None


# ============================================================
# CALCULATE ANGLE
# ============================================================

def calculate_angle(
    point_a,
    point_b,
    point_c,
):

    ax, ay = point_a
    bx, by = point_b
    cx, cy = point_c

    radians = (
        math.atan2(
            cy - by,
            cx - bx,
        )
        -
        math.atan2(
            ay - by,
            ax - bx,
        )
    )

    angle = abs(
        math.degrees(
            radians
        )
    )

    if angle > 180:
        angle = 360 - angle

    return float(angle)


# ============================================================
# GET BEST VISIBLE ARM
# ============================================================

def get_best_arm(
    landmarks,
    image_width,
    image_height,
):

    right_shoulder = landmarks[
        mp_pose.PoseLandmark.RIGHT_SHOULDER
    ]

    right_elbow = landmarks[
        mp_pose.PoseLandmark.RIGHT_ELBOW
    ]

    right_wrist = landmarks[
        mp_pose.PoseLandmark.RIGHT_WRIST
    ]


    left_shoulder = landmarks[
        mp_pose.PoseLandmark.LEFT_SHOULDER
    ]

    left_elbow = landmarks[
        mp_pose.PoseLandmark.LEFT_ELBOW
    ]

    left_wrist = landmarks[
        mp_pose.PoseLandmark.LEFT_WRIST
    ]


    right_score = (
        right_shoulder.visibility
        +
        right_elbow.visibility
        +
        right_wrist.visibility
    )


    left_score = (
        left_shoulder.visibility
        +
        left_elbow.visibility
        +
        left_wrist.visibility
    )


    if right_score >= left_score:

        shoulder = right_shoulder
        elbow = right_elbow
        wrist = right_wrist
        side = "Right"

    else:

        shoulder = left_shoulder
        elbow = left_elbow
        wrist = left_wrist
        side = "Left"


    minimum_visibility = min(
        shoulder.visibility,
        elbow.visibility,
        wrist.visibility,
    )


    if minimum_visibility < 0.20:
        return None


    shoulder_point = (
        shoulder.x * image_width,
        shoulder.y * image_height,
    )

    elbow_point = (
        elbow.x * image_width,
        elbow.y * image_height,
    )

    wrist_point = (
        wrist.x * image_width,
        wrist.y * image_height,
    )


    return {

        "shoulder": shoulder,
        "elbow": elbow,
        "wrist": wrist,

        "shoulder_point": shoulder_point,
        "elbow_point": elbow_point,
        "wrist_point": wrist_point,

        "side": side,
    }


# ============================================================
# VIDEO PROCESSOR
# ============================================================

class PoseVideoProcessor(VideoProcessorBase):


    # ========================================================
    # INITIALIZE
    # ========================================================

    def __init__(self):

        self.lock = threading.Lock()


        # ----------------------------------------------------
        # EXERCISE
        # ----------------------------------------------------

        self.exercise_name = "Bicep Curl"


        # ----------------------------------------------------
        # MEDIAPIPE
        # FASTEST MODEL FOR REAL-TIME CAMERA
        # ----------------------------------------------------

        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.35,
            min_tracking_confidence=0.35,
        )


        # ----------------------------------------------------
        # LIVE VALUES
        # ----------------------------------------------------

        self.reps = 0

        self.current_angle = 0

        self.current_score = 0

        self.current_status = "Camera Starting"

        self.current_feedback = (
            "Waiting for camera..."
        )

        self.current_side = "Unknown"

        self.stage = "waiting"


        # ----------------------------------------------------
        # ANGLE SMOOTHING
        # ----------------------------------------------------

        self.angle_history = []


        # ----------------------------------------------------
        # REP CONTROL
        # ----------------------------------------------------

        self.last_rep_time = 0.0

        self.minimum_rep_interval = 0.5


        # ----------------------------------------------------
        # WORKOUT DATA
        # ----------------------------------------------------

        self.total_score = 0

        self.score_samples = 0

        self.start_time = time.time()


        # ----------------------------------------------------
        # FRAME DATA
        # ----------------------------------------------------

        self.frame_count = 0


    # ========================================================
    # SMOOTH ANGLE
    # ========================================================

    def smooth_angle(
        self,
        angle,
    ):

        self.angle_history.append(
            angle
        )

        if len(self.angle_history) > 3:

            self.angle_history.pop(0)

        return (
            sum(self.angle_history)
            /
            len(self.angle_history)
        )


    # ========================================================
    # REGISTER REP
    # ========================================================

    def register_rep(
        self,
        score,
    ):

        current_time = time.time()

        if (
            current_time
            -
            self.last_rep_time
            <
            self.minimum_rep_interval
        ):

            return False


        self.reps += 1

        self.last_rep_time = current_time

        self.total_score += score

        self.score_samples += 1

        return True


    # ========================================================
    # BICEP CURL SCORE
    # ========================================================

    def calculate_bicep_score(
        self,
        angle,
    ):

        if angle <= 65:
            return 100

        if angle <= 80:
            return 95

        if angle <= 100:
            return 85

        return 75


    # ========================================================
    # PUSH-UP SCORE
    # ========================================================

    def calculate_pushup_score(
        self,
        angle,
    ):

        if angle <= 95:
            return 100

        if angle <= 110:
            return 95

        if angle <= 130:
            return 85

        return 75


    # ========================================================
    # BICEP CURL COUNTER
    # ========================================================

    def count_bicep_curl(
        self,
        angle,
    ):

        EXTENDED = 120
        CONTRACTED = 85


        # ----------------------------------------------------
        # WAITING
        # ----------------------------------------------------

        if self.stage == "waiting":

            self.current_status = "Get Ready"

            self.current_feedback = (
                "Extend your arm comfortably."
            )

            if angle >= EXTENDED:

                self.stage = "ready"

                self.current_status = "Ready"

                self.current_feedback = (
                    "Good! Curl your arm upward."
                )

            return


        # ----------------------------------------------------
        # READY
        # ----------------------------------------------------

        if self.stage == "ready":

            self.current_status = "Ready"

            self.current_feedback = (
                "Curl your arm upward."
            )

            if angle <= 110:

                self.stage = "curling"

            return


        # ----------------------------------------------------
        # CURLING
        # ----------------------------------------------------

        if self.stage == "curling":

            self.current_status = "Curling"

            self.current_feedback = (
                "Continue upward."
            )

            if angle <= CONTRACTED:

                self.stage = "top"

                self.current_status = "Top Reached"

                self.current_feedback = (
                    "Great! Lower your arm."
                )

            return


        # ----------------------------------------------------
        # TOP
        # ----------------------------------------------------

        if self.stage == "top":

            self.current_status = "Lowering"

            self.current_feedback = (
                "Extend your arm back down."
            )

            if angle >= 105:

                self.stage = "returning"

            return


        # ----------------------------------------------------
        # RETURNING
        # ----------------------------------------------------

        if self.stage == "returning":

            self.current_status = "Returning"

            self.current_feedback = (
                "Almost there. Extend your arm."
            )

            if angle >= EXTENDED:

                score = self.calculate_bicep_score(
                    angle
                )

                if self.register_rep(score):

                    self.stage = "ready"

                    self.current_status = (
                        "Rep Counted"
                    )

                    self.current_feedback = (
                        f"Excellent! Rep {self.reps} counted."
                    )

            return


    # ========================================================
    # PUSH-UP COUNTER
    # ========================================================

    def count_push_up(
        self,
        angle,
    ):

        UP_POSITION = 135
        DOWN_POSITION = 100


        if self.stage == "waiting":

            self.current_status = "Get Ready"

            self.current_feedback = (
                "Start in the upper push-up position."
            )

            if angle >= UP_POSITION:

                self.stage = "ready"

                self.current_status = "Ready"

                self.current_feedback = (
                    "Good! Lower your body."
                )

            return


        if self.stage == "ready":

            self.current_status = "Lowering"

            self.current_feedback = (
                "Lower your body."
            )

            if angle <= 125:

                self.stage = "lowering"

            return


        if self.stage == "lowering":

            self.current_status = "Lowering"

            self.current_feedback = (
                "Continue lowering."
            )

            if angle <= DOWN_POSITION:

                self.stage = "bottom"

                self.current_status = (
                    "Bottom Reached"
                )

                self.current_feedback = (
                    "Great! Push upward."
                )

            return


        if self.stage == "bottom":

            self.current_status = "Pushing Up"

            self.current_feedback = (
                "Push your body upward."
            )

            if angle >= UP_POSITION:

                score = self.calculate_pushup_score(
                    angle
                )

                if self.register_rep(score):

                    self.stage = "ready"

                    self.current_status = (
                        "Rep Counted"
                    )

                    self.current_feedback = (
                        f"Excellent! Rep {self.reps} counted."
                    )

            return


    # ========================================================
    # PROCESS VIDEO FRAME
    # ========================================================

    def recv(
        self,
        frame,
    ):

        # ----------------------------------------------------
        # ALWAYS GET FRAME FIRST
        # THIS PREVENTS THE CAMERA FROM GETTING STUCK
        # ----------------------------------------------------

        image = frame.to_ndarray(
            format="bgr24"
        )


        # ----------------------------------------------------
        # MIRROR CAMERA
        # ----------------------------------------------------

        image = cv2.flip(
            image,
            1,
        )


        self.frame_count += 1


        try:

            image_height, image_width, _ = (
                image.shape
            )


            # ------------------------------------------------
            # CONVERT IMAGE
            # ------------------------------------------------

            rgb_image = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2RGB,
            )


            # ------------------------------------------------
            # MEDIAPIPE PROCESS
            # ------------------------------------------------

            results = self.pose.process(
                rgb_image
            )


            # ------------------------------------------------
            # POSE FOUND
            # ------------------------------------------------

            if (
                results is not None
                and results.pose_landmarks is not None
            ):

                landmarks = (
                    results.pose_landmarks.landmark
                )


                arm_data = get_best_arm(
                    landmarks,
                    image_width,
                    image_height,
                )


                # --------------------------------------------
                # ARM FOUND
                # --------------------------------------------

                if arm_data is not None:

                    shoulder_point = (
                        arm_data["shoulder_point"]
                    )

                    elbow_point = (
                        arm_data["elbow_point"]
                    )

                    wrist_point = (
                        arm_data["wrist_point"]
                    )


                    raw_angle = calculate_angle(
                        shoulder_point,
                        elbow_point,
                        wrist_point,
                    )


                    angle = self.smooth_angle(
                        raw_angle
                    )


                    with self.lock:

                        self.current_angle = int(
                            angle
                        )

                        self.current_side = (
                            arm_data["side"]
                        )


                        if (
                            self.exercise_name
                            ==
                            "Bicep Curl"
                        ):

                            self.count_bicep_curl(
                                angle
                            )

                            self.current_score = (
                                self.calculate_bicep_score(
                                    angle
                                )
                            )


                        elif (
                            self.exercise_name
                            ==
                            "Push Up"
                        ):

                            self.count_push_up(
                                angle
                            )

                            self.current_score = (
                                self.calculate_pushup_score(
                                    angle
                                )
                            )


                    # ----------------------------------------
                    # DRAW ANGLE
                    # ----------------------------------------

                    elbow_x = int(
                        arm_data["elbow"].x
                        *
                        image_width
                    )

                    elbow_y = int(
                        arm_data["elbow"].y
                        *
                        image_height
                    )


                    cv2.putText(
                        image,
                        f"{int(angle)} deg",
                        (
                            elbow_x + 10,
                            elbow_y - 10,
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2,
                    )


                # --------------------------------------------
                # ARM NOT CLEAR
                # --------------------------------------------

                else:

                    with self.lock:

                        self.current_status = (
                            "Arm Not Clear"
                        )

                        self.current_feedback = (
                            "Keep shoulder, elbow and wrist visible."
                        )


                # --------------------------------------------
                # DRAW POSE
                # --------------------------------------------

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
            # NO POSE
            # ------------------------------------------------

            else:

                with self.lock:

                    self.current_status = (
                        "Looking for You"
                    )

                    self.current_feedback = (
                        "Move your upper body into the camera."
                    )


        # ----------------------------------------------------
        # PROCESSING ERROR
        # CAMERA FRAME STILL CONTINUES
        # ----------------------------------------------------

        except Exception as error:

            with self.lock:

                self.current_status = (
                    "Camera Active"
                )

                self.current_feedback = (
                    "Camera is working. Adjust your position."
                )


        # ====================================================
        # LIVE OVERLAY
        # ====================================================

        with self.lock:

            reps = self.reps

            angle = self.current_angle

            score = self.current_score

            stage = self.stage

            side = self.current_side


        cv2.rectangle(
            image,
            (10, 10),
            (460, 225),
            (0, 0, 0),
            -1,
        )


        cv2.putText(
            image,
            f"REPS: {reps}",
            (25, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 0),
            2,
        )


        cv2.putText(
            image,
            f"ANGLE: {angle}",
            (25, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            image,
            f"STAGE: {stage.upper()}",
            (25, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            image,
            f"SCORE: {score}",
            (25, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )


        cv2.putText(
            image,
            f"ARM: {side}",
            (25, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
        )


        # ----------------------------------------------------
        # MOST IMPORTANT:
        # ALWAYS RETURN VIDEO FRAME
        # ----------------------------------------------------

        return av.VideoFrame.from_ndarray(
            image,
            format="bgr24",
        )


# ============================================================
# LOAD USER
# ============================================================

try:

    user = get_user(
        current_user_id
    )

except Exception as error:

    st.error(
        f"Could not load user data: {error}"
    )

    st.stop()


if user is None:

    st.error(
        "User account not found."
    )

    st.stop()


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "🏋️ AI Workout Arena"
)

st.write(
    f"Welcome, **{user.get('username', 'FitQuest Player')}**! "
    "Start your camera and let FitQuest AI track your movement."
)


# ============================================================
# USER STATS
# ============================================================

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "⭐ XP",
        user.get("xp", 0),
    )


with col2:

    st.metric(
        "🏆 Level",
        user.get("level", 1),
    )


with col3:

    st.metric(
        "🔥 Streak",
        f"{user.get('streak', 0)} Days",
    )


with col4:

    st.metric(
        "💪 Workouts",
        user.get("total_workouts", 0),
    )


st.divider()


# ============================================================
# EXERCISE SELECTION
# ============================================================

st.subheader(
    "Select Exercise"
)


selected_exercise = st.selectbox(
    "Choose your exercise",
    [
        "Bicep Curl",
        "Push Up",
    ],
)


# ============================================================
# EXERCISE INSTRUCTIONS
# ============================================================

if selected_exercise == "Bicep Curl":

    st.info(
        "Stand slightly sideways to the camera. Keep your shoulder, "
        "elbow and wrist visible. Start with your arm extended, curl "
        "upward, then extend again."
    )

else:

    st.info(
        "Position the camera sideways. Start at the top position, "
        "lower your body, then push upward."
    )


# ============================================================
# LIVE CAMERA
# ============================================================

st.subheader(
    "📷 Live AI Camera"
)

st.caption(
    "Allow camera permission and press START. The camera should appear "
    "before pose detection begins."
)


webrtc_ctx = webrtc_streamer(
    key="fitquest_ai_camera",
    mode=WebRtcMode.SENDRECV,

    media_stream_constraints={
        "video": {
            "width": {
                "ideal": 640,
            },
            "height": {
                "ideal": 480,
            },
            "frameRate": {
                "ideal": 24,
            },
        },
        "audio": False,
    },

    video_processor_factory=PoseVideoProcessor,

    async_processing=True,
)


# ============================================================
# UPDATE SELECTED EXERCISE
# ============================================================

if (
    webrtc_ctx is not None
    and webrtc_ctx.video_processor is not None
):

    processor = webrtc_ctx.video_processor

    with processor.lock:

        processor.exercise_name = (
            selected_exercise
        )


# ============================================================
# LIVE AI ANALYSIS
# ============================================================

if (
    webrtc_ctx is not None
    and webrtc_ctx.video_processor is not None
):

    processor = webrtc_ctx.video_processor


    with processor.lock:

        live_reps = processor.reps

        live_angle = (
            processor.current_angle
        )

        live_score = (
            processor.current_score
        )

        live_stage = (
            processor.stage
        )

        live_status = (
            processor.current_status
        )

        live_feedback = (
            processor.current_feedback
        )

        live_arm = (
            processor.current_side
        )


    st.divider()

    st.subheader(
        "🤖 Live AI Analysis"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "🔁 Reps",
            live_reps,
        )


    with col2:

        st.metric(
            "📐 Angle",
            f"{live_angle}°",
        )


    with col3:

        st.metric(
            "⭐ Score",
            f"{live_score}/100",
        )


    with col4:

        st.metric(
            "💪 Arm",
            live_arm,
        )


    st.info(
        f"**Stage:** {live_stage.title()}"
    )

    st.success(
        f"**Status:** {live_status}"
    )

    st.write(
        f"**AI Feedback:** {live_feedback}"
    )


# ============================================================
# COMPLETE WORKOUT
# ============================================================

st.divider()

st.subheader(
    "🏁 Complete Workout"
)


if st.button(
    "🏆 Complete and Save Workout",
    use_container_width=True,
):

    if (
        webrtc_ctx is None
        or webrtc_ctx.video_processor is None
    ):

        st.error(
            "Please start the camera first."
        )

    else:

        processor = webrtc_ctx.video_processor


        with processor.lock:

            reps = processor.reps

            total_score = (
                processor.total_score
            )

            score_samples = (
                processor.score_samples
            )

            workout_start_time = (
                processor.start_time
            )


        if reps <= 0:

            st.warning(
                "Complete at least one full repetition before saving."
            )

        else:

            if score_samples > 0:

                form_score = round(
                    total_score
                    /
                    score_samples,
                    1,
                )

            else:

                form_score = 0


            workout_key = (
                f"{current_user_id}_"
                f"{selected_exercise}_"
                f"{workout_start_time}"
            )


            if (
                st.session_state.saved_workout_key
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


                    st.session_state.last_workout_result = (
                        result
                    )

                    st.session_state.saved_workout_key = (
                        workout_key
                    )

                    st.success(
                        "Workout saved successfully!"
                    )


                except Exception as error:

                    st.error(
                        f"Workout could not be saved: {error}"
                    )


# ============================================================
# WORKOUT RESULT
# ============================================================

if st.session_state.last_workout_result:

    result = (
        st.session_state.last_workout_result
    )


    st.divider()

    st.subheader(
        "🎉 Workout Result"
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🔁 Reps",
            result.get(
                "reps",
                0,
            ),
        )


    with col2:

        st.metric(
            "⭐ XP Earned",
            result.get(
                "xp_earned",
                0,
            ),
        )


    with col3:

        st.metric(
            "🏆 Level",
            result.get(
                "level",
                1,
            ),
        )


    st.success(
        f"🔥 Current Streak: "
        f"{result.get('streak', 0)} Days"
    )


# ============================================================
# NAVIGATION
# ============================================================

st.divider()

st.subheader(
    "Continue Your FitQuest Journey"
)


action1, action2, action3 = st.columns(3)


with action1:

    if st.button(
        "📊 Dashboard",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/2_Dashboard.py"
        )


with action2:

    if st.button(
        "🎯 Challenges",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/3_Challenges.py"
        )


with action3:

    if st.button(
        "🏅 Leaderboard",
        use_container_width=True,
    ):

        st.switch_page(
            "pages/6_Leaderboard.py"
        )