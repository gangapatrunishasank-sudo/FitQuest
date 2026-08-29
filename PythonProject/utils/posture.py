import cv2
import mediapipe as mp
import numpy as np


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


# ============================================================
# ANGLE CALCULATION
# ============================================================

def calculate_angle(point_a, point_b, point_c):
    """
    Calculate the angle between three body points.
    """

    a = np.array(point_a)
    b = np.array(point_b)
    c = np.array(point_c)

    radians = np.arctan2(
        c[1] - b[1],
        c[0] - b[0]
    ) - np.arctan2(
        a[1] - b[1],
        a[0] - b[0]
    )

    angle = np.abs(
        radians * 180.0 / np.pi
    )

    if angle > 180:
        angle = 360 - angle

    return round(angle, 1)


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_posture(image):
    """
    Detect body landmarks and analyze posture.
    """

    image_array = np.array(image)

    image_bgr = cv2.cvtColor(
        image_array,
        cv2.COLOR_RGB2BGR
    )

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB
    )

    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5
    ) as pose:

        results = pose.process(image_rgb)

        if not results.pose_landmarks:

            return {
                "detected": False,
                "message": "Body not detected. Move farther from the camera.",
                "form_score": 0,
                "angles": {},
                "image": image_array
            }

        landmarks = results.pose_landmarks.landmark

        image_height, image_width, _ = image_array.shape

        # ----------------------------------------------------
        # BODY LANDMARKS
        # ----------------------------------------------------

        left_shoulder = [
            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y
        ]

        left_elbow = [
            landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y
        ]

        left_wrist = [
            landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
        ]

        left_hip = [
            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
        ]

        left_knee = [
            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
        ]

        left_ankle = [
            landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
            landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
        ]

        # ----------------------------------------------------
        # CALCULATE JOINT ANGLES
        # ----------------------------------------------------

        elbow_angle = calculate_angle(
            left_shoulder,
            left_elbow,
            left_wrist
        )

        knee_angle = calculate_angle(
            left_hip,
            left_knee,
            left_ankle
        )

        # ----------------------------------------------------
        # DRAW BODY SKELETON
        # ----------------------------------------------------

        annotated_image = image_bgr.copy()

        mp_drawing.draw_landmarks(
            annotated_image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )

        annotated_image = cv2.cvtColor(
            annotated_image,
            cv2.COLOR_BGR2RGB
        )

        # ----------------------------------------------------
        # RETURN RESULTS
        # ----------------------------------------------------

        return {
            "detected": True,
            "message": "Body detected successfully.",
            "form_score": 80,
            "angles": {
                "elbow": elbow_angle,
                "knee": knee_angle
            },
            "image": annotated_image
        }