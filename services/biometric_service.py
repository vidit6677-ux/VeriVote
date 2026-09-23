import os
import cv2
import numpy as np


# =========================================================
# VERIVOTE FACE VERIFICATION SERVICE
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# =========================================================
# DIRECTORIES
# =========================================================

FACE_DATA_DIR = os.path.join(
    BASE_DIR,
    "face_data"
)

MODELS_DIR = os.path.join(
    BASE_DIR,
    "models"
)


# =========================================================
# CAMERA
# =========================================================

CAMERA_INDEX = 0


# =========================================================
# FACE MATCH THRESHOLD
# =========================================================
#
# LBPH:
# LOWER DISTANCE = BETTER MATCH
#
# This is only for our college-project prototype.
#
FACE_THRESHOLD = 80.0


# =========================================================
# HAAR CASCADE
# =========================================================

CASCADE_FILE = os.path.join(
    MODELS_DIR,
    "haarcascade_frontalface_default.xml"
)


if not os.path.isfile(CASCADE_FILE):

    raise FileNotFoundError(
        "\n\n"
        "VERIVOTE FACE DETECTOR NOT FOUND\n"
        "=================================\n\n"
        f"Expected file:\n{CASCADE_FILE}\n\n"
        "Make sure the following file exists:\n"
        "models/haarcascade_frontalface_default.xml\n"
    )


FACE_CASCADE = cv2.CascadeClassifier(
    CASCADE_FILE
)


if FACE_CASCADE.empty():

    raise RuntimeError(
        "\n\n"
        "VERIVOTE COULD NOT LOAD FACE DETECTOR\n"
        "=======================================\n\n"
        f"File:\n{CASCADE_FILE}\n"
    )


# =========================================================
# OPENCV FACE MODULE
# =========================================================

if not hasattr(cv2, "face"):

    raise RuntimeError(
        "\n\n"
        "OPENCV FACE MODULE NOT AVAILABLE\n"
        "=================================\n\n"
        "Install opencv-contrib-python.\n"
    )


# =========================================================
# GET REFERENCE IMAGES
# =========================================================

def get_reference_images(identity):

    identity = str(identity)

    files = []

    # -----------------------------------------------------
    # FORMAT 1:
    #
    # face_data/
    #     471099122860.jpg
    #
    # -----------------------------------------------------

    for extension in (
        ".jpg",
        ".jpeg",
        ".png"
    ):

        file_path = os.path.join(
            FACE_DATA_DIR,
            identity + extension
        )

        if os.path.isfile(file_path):

            files.append(
                file_path
            )

    if files:

        return files

    # -----------------------------------------------------
    # FORMAT 2:
    #
    # face_data/
    #     471099122860/
    #         1.jpg
    #         2.jpg
    #         3.jpg
    #
    # -----------------------------------------------------

    voter_folder = os.path.join(
        FACE_DATA_DIR,
        identity
    )

    if os.path.isdir(voter_folder):

        for filename in sorted(
            os.listdir(voter_folder)
        ):

            if filename.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png"
                )
            ):

                files.append(
                    os.path.join(
                        voter_folder,
                        filename
                    )
                )

    return files


# =========================================================
# EXTRACT FACE
# =========================================================

def extract_face(image):

    if image is None:

        return None

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.equalizeHist(
        gray
    )

    faces = FACE_CASCADE.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    if len(faces) == 0:

        return None

    # Choose largest face
    x, y, w, h = max(
        faces,
        key=lambda rect: rect[2] * rect[3]
    )

    face = gray[
        y:y + h,
        x:x + w
    ]

    face = cv2.resize(
        face,
        (200, 200)
    )

    return face


# =========================================================
# BUILD FACE MODEL
# =========================================================

def build_model(identity):

    reference_files = get_reference_images(
        identity
    )

    # -----------------------------------------------------
    # NO REFERENCE IMAGE
    # -----------------------------------------------------

    if not reference_files:

        return None, (
            f"No registered face image found "
            f"for voter {identity}.\n\n"
            f"Expected:\n"
            f"face_data/{identity}.jpg"
        )

    training_faces = []

    # -----------------------------------------------------
    # LOAD REFERENCE IMAGES
    # -----------------------------------------------------

    for file_path in reference_files:

        image = cv2.imread(
            file_path
        )

        if image is None:

            continue

        face = extract_face(
            image
        )

        if face is not None:

            training_faces.append(
                face
            )

    # -----------------------------------------------------
    # NO FACE DETECTED
    # -----------------------------------------------------

    if not training_faces:

        return None, (
            "A reference image was found, "
            "but no face could be detected.\n\n"
            "Please use a clear front-facing "
            "photo containing one person."
        )

    # -----------------------------------------------------
    # CREATE LBPH RECOGNIZER
    # -----------------------------------------------------

    recognizer = (
        cv2.face.LBPHFaceRecognizer_create(
            radius=1,
            neighbors=8,
            grid_x=8,
            grid_y=8
        )
    )

    # =====================================================
    # IMPORTANT FIX
    # =====================================================
    #
    # OpenCV 5 expects labels as a NumPy array.
    #
    labels = np.array(
        [1] * len(training_faces),
        dtype=np.int32
    )

    # Make sure training images are also
    # proper NumPy arrays.
    training_faces = [
        np.asarray(face, dtype=np.uint8)
        for face in training_faces
    ]

    # -----------------------------------------------------
    # TRAIN
    # -----------------------------------------------------

    recognizer.train(
        training_faces,
        labels
    )

    return recognizer, None


# =========================================================
# OPEN CAMERA
# =========================================================

def open_camera():

    # Windows DirectShow
    camera = cv2.VideoCapture(
        CAMERA_INDEX,
        cv2.CAP_DSHOW
    )

    # Fallback
    if not camera.isOpened():

        camera.release()

        camera = cv2.VideoCapture(
            CAMERA_INDEX
        )

    return camera


# =========================================================
# VERIFY FACE USING CAMERA
# =========================================================

def verify_face_from_camera(identity):

    identity = str(identity)

    # -----------------------------------------------------
    # BUILD MODEL
    # -----------------------------------------------------

    recognizer, error = build_model(
        identity
    )

    if recognizer is None:

        return {
            "success": False,
            "message": error
        }

    # -----------------------------------------------------
    # OPEN CAMERA
    # -----------------------------------------------------

    camera = open_camera()

    if not camera.isOpened():

        camera.release()

        return {
            "success": False,
            "message": (
                "Could not open the laptop camera.\n\n"
                "Check Windows camera permissions "
                "and make sure another application "
                "is not using the camera."
            )
        }

    # -----------------------------------------------------
    # MATCH TRACKING
    # -----------------------------------------------------

    best_distance = None

    consecutive_matches = 0

    REQUIRED_MATCHES = 8

    window_name = (
        "VeriVote - Face Verification"
    )

    try:

        while True:

            success, frame = camera.read()

            if not success:

                return {
                    "success": False,
                    "message": (
                        "The camera opened but "
                        "could not capture a frame."
                    )
                }

            display = frame.copy()

            # -------------------------------------------------
            # GRAYSCALE
            # -------------------------------------------------

            gray = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2GRAY
            )

            gray = cv2.equalizeHist(
                gray
            )

            # -------------------------------------------------
            # FACE DETECTION
            # -------------------------------------------------

            faces = FACE_CASCADE.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )

            status = "ALIGN YOUR FACE"

            status_color = (
                0,
                180,
                255
            )

            # No face
            if len(faces) == 0:

                consecutive_matches = 0

            # -------------------------------------------------
            # PROCESS FACES
            # -------------------------------------------------

            for (x, y, w, h) in faces:

                face = gray[
                    y:y + h,
                    x:x + w
                ]

                face = cv2.resize(
                    face,
                    (200, 200)
                )

                face = cv2.equalizeHist(
                    face
                )

                # -------------------------------------------------
                # PREDICT
                # -------------------------------------------------

                label, distance = (
                    recognizer.predict(
                        face
                    )
                )

                # Track best distance
                if (
                    best_distance is None
                    or distance < best_distance
                ):

                    best_distance = distance

                # -------------------------------------------------
                # MATCH
                # -------------------------------------------------

                if distance <= FACE_THRESHOLD:

                    consecutive_matches += 1

                    status = (
                        "FACE MATCHED"
                    )

                    status_color = (
                        0,
                        220,
                        0
                    )

                else:

                    consecutive_matches = 0

                    status = (
                        "FACE DOES NOT MATCH"
                    )

                    status_color = (
                        0,
                        0,
                        255
                    )

                # -------------------------------------------------
                # FACE BOX
                # -------------------------------------------------

                cv2.rectangle(
                    display,
                    (x, y),
                    (x + w, y + h),
                    status_color,
                    3
                )

                # -------------------------------------------------
                # DISTANCE
                # -------------------------------------------------

                cv2.putText(
                    display,
                    f"Distance: {distance:.1f}",
                    (x, y + h + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    status_color,
                    2
                )

            # -------------------------------------------------
            # HEADER
            # -------------------------------------------------

            cv2.rectangle(
                display,
                (0, 0),
                (
                    display.shape[1],
                    95
                ),
                (20, 45, 80),
                -1
            )

            cv2.putText(
                display,
                "VERIVOTE",
                (20, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (255, 255, 255),
                2
            )

            cv2.putText(
                display,
                "FACE VERIFICATION",
                (20, 67),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                status_color,
                2
            )

            # -------------------------------------------------
            # INSTRUCTIONS
            # -------------------------------------------------

            cv2.putText(
                display,
                "Look directly at the camera",
                (
                    20,
                    display.shape[0] - 45
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1
            )

            cv2.putText(
                display,
                "Press Q to cancel",
                (
                    20,
                    display.shape[0] - 20
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1
            )

            # -------------------------------------------------
            # DISPLAY
            # -------------------------------------------------

            cv2.imshow(
                window_name,
                display
            )

            key = (
                cv2.waitKey(1)
                & 0xFF
            )

            # -------------------------------------------------
            # SUCCESS
            # -------------------------------------------------

            if (
                consecutive_matches
                >= REQUIRED_MATCHES
            ):

                cv2.waitKey(
                    800
                )

                return {
                    "success": True,
                    "message": (
                        "Face verification successful."
                    ),
                    "confidence": best_distance
                }

            # -------------------------------------------------
            # CANCEL
            # -------------------------------------------------

            if key == ord("q"):

                return {
                    "success": False,
                    "message": (
                        "Face verification cancelled."
                    )
                }

    finally:

        camera.release()

        cv2.destroyAllWindows()

        cv2.waitKey(1)