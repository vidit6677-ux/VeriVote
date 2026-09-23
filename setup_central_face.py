"""
One-time demo utility for registering the Central administrator face.

Run from the VeriVote project folder:

    python setup_central_face.py

This stores the reference image at:

    face_data/central_admin.jpg

This is a classroom-project enrollment utility,
not production biometric enrollment.
"""

import os
import cv2

from services.biometric_service import extract_face


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

FACE_DIR = os.path.join(
    BASE_DIR,
    "face_data"
)

OUTPUT = os.path.join(
    FACE_DIR,
    "central_admin.jpg"
)


# =========================================================
# CREATE FACE DATA DIRECTORY
# =========================================================

os.makedirs(
    FACE_DIR,
    exist_ok=True
)


# =========================================================
# OPEN CAMERA
# =========================================================

camera = cv2.VideoCapture(
    0,
    cv2.CAP_DSHOW
)

if not camera.isOpened():

    camera.release()

    camera = cv2.VideoCapture(
        0
    )


if not camera.isOpened():

    raise RuntimeError(
        "Could not open the laptop camera."
    )


print(
    "Central face enrollment started."
)

print(
    "Look directly at the camera."
)

print(
    "Press SPACE to capture or ESC to cancel."
)


# =========================================================
# CAPTURE LOOP
# =========================================================

captured = None

while True:

    ok, frame = camera.read()

    if not ok:
        continue

    preview = frame.copy()

    face = extract_face(
        frame
    )

    if face is not None:

        cv2.putText(
            preview,
            "FACE DETECTED - press SPACE",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 220, 0),
            2
        )

    else:

        cv2.putText(
            preview,
            "NO FACE DETECTED",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

    cv2.imshow(
        "VeriVote - Central Face Enrollment",
        preview
    )

    key = cv2.waitKey(1) & 0xFF

    # ESC
    if key == 27:
        break

    # SPACE
    if key == 32 and face is not None:

        captured = frame.copy()
        break


# =========================================================
# RELEASE CAMERA
# =========================================================

camera.release()

cv2.destroyAllWindows()


# =========================================================
# CANCELLED
# =========================================================

if captured is None:

    print(
        "Enrollment cancelled."
    )

    raise SystemExit(0)


# =========================================================
# SAVE CENTRAL FACE
# =========================================================

if not cv2.imwrite(
    OUTPUT,
    captured
):

    raise RuntimeError(
        f"Could not save reference face to {OUTPUT}"
    )


print(
    f"Central face reference saved to: {OUTPUT}"
)

print(
    "Restart VeriVote and use the CENTRAL account "
    "in the Admin Security Portal."
)