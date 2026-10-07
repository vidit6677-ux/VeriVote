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
# With one enrolled image per demo identity, a permissive threshold lets a
# different face at an angle look close enough. Keep this deliberately strict
# until enrollment stores multiple pose samples per identity.
FACE_THRESHOLD = 65.0
MAX_AVERAGE_DISTANCE = 55.0
MIN_LIVENESS_MOVEMENT = 18


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


def get_registered_identities():

    """Return identities that have at least one reference image."""

    if not os.path.isdir(FACE_DATA_DIR):

        return []

    identities = set()

    for filename in os.listdir(FACE_DATA_DIR):

        path = os.path.join(FACE_DATA_DIR, filename)

        if os.path.isfile(path):

            identity, extension = os.path.splitext(filename)

            if extension.lower() in (".jpg", ".jpeg", ".png"):

                identities.add(identity)

        elif os.path.isdir(path) and get_reference_images(filename):

            identities.add(filename)

    return sorted(identities)


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

    identity = str(identity)

    reference_files = get_reference_images(identity)

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
    labels = []
    label_to_identity = {}

    registered_identities = get_registered_identities()

    # A recognizer trained only on the requested identity cannot establish
    # identity. It merely measures similarity to that one person's images.
    if len(registered_identities) < 2:

        return None, (
            "Face verification is unavailable until at least two "
            "identities have registered face references."
        )

    # -----------------------------------------------------
    # LOAD REFERENCE IMAGES
    # -----------------------------------------------------

    for label, registered_identity in enumerate(registered_identities, start=1):

        label_to_identity[label] = registered_identity

        for file_path in get_reference_images(registered_identity):

            image = cv2.imread(
                file_path
            )

            if image is None:

                continue

            face = extract_face(
                image
            )

            if face is not None:

                training_faces.append(face)
                labels.append(label)

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
    labels = np.array(labels, dtype=np.int32)

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

    return (recognizer, label_to_identity), None


def is_face_match(expected_identity, predicted_identity, distance):

    """Require both a close match and the expected identity label."""

    return (
        str(predicted_identity) == str(expected_identity)
        and distance <= FACE_THRESHOLD
    )


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

    model, error = build_model(
        identity
    )

    if model is None:

        return {
            "success": False,
            "message": error
        }

    recognizer, label_to_identity = model

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
    match_distances = []
    initial_face_center = None
    maximum_face_movement = 0.0

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

            status_color = (
                0,
                180,
                255
            )

            # A verification session must contain exactly one face. This
            # prevents an unrelated face in the frame from being accepted.
            if len(faces) != 1:

                consecutive_matches = 0
                match_distances = []
                initial_face_center = None
                maximum_face_movement = 0.0

                if len(faces) > 1:

                    cv2.putText(
                        display,
                        "Only one face may be visible",
                        (20, 125),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

            # -------------------------------------------------
            # PROCESS FACES
            # -------------------------------------------------

            for (x, y, w, h) in faces:

                center = (x + (w / 2), y + (h / 2))
                if initial_face_center is None:
                    initial_face_center = center
                else:
                    movement_x = center[0] - initial_face_center[0]
                    movement_y = center[1] - initial_face_center[1]
                    maximum_face_movement = max(
                        maximum_face_movement,
                        (movement_x ** 2 + movement_y ** 2) ** 0.5,
                    )

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

                predicted_identity = label_to_identity.get(label)

                # Track best distance
                if (
                    best_distance is None
                    or distance < best_distance
                ):

                    best_distance = distance

                # -------------------------------------------------
                # MATCH
                # -------------------------------------------------

                if is_face_match(
                    identity,
                    predicted_identity,
                    distance
                ):

                    consecutive_matches += 1
                    match_distances.append(distance)

                    status_color = (
                        0,
                        220,
                        0
                    )

                else:

                    consecutive_matches = 0
                    match_distances = []

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
                "Look at the camera and move your head slightly",
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
                and sum(match_distances) / len(match_distances)
                <= MAX_AVERAGE_DISTANCE
                and maximum_face_movement >= MIN_LIVENESS_MOVEMENT
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
