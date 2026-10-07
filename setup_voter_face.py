"""Enroll multiple face samples for a demo voter.

Usage:
    python setup_voter_face.py 647162579350

Press SPACE to capture a sample, then change pose slightly. Press ESC to
cancel. Five samples are recommended for the local prototype.
"""

import os
import sys

import cv2

from services.biometric_service import extract_face


SAMPLE_COUNT = 5
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():

    if len(sys.argv) != 2:
        raise SystemExit("Usage: python setup_voter_face.py <voter_identity>")

    identity = str(sys.argv[1])
    output_dir = os.path.join(BASE_DIR, "face_data", identity)
    os.makedirs(output_dir, exist_ok=True)

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        raise RuntimeError("Could not open the laptop camera.")

    captured = 0

    try:
        while captured < SAMPLE_COUNT:
            ok, frame = camera.read()
            if not ok:
                continue

            preview = frame.copy()
            face = extract_face(frame)
            prompt = (
                f"Sample {captured + 1}/{SAMPLE_COUNT}: "
                "press SPACE to capture, ESC to cancel"
            )
            color = (0, 220, 0) if face is not None else (0, 0, 255)
            cv2.putText(preview, prompt, (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                        0.65, (255, 255, 255), 2)
            cv2.putText(preview, "FACE DETECTED" if face is not None else "NO FACE",
                        (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            cv2.imshow("VeriVote - Voter Face Enrollment", preview)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                return
            if key == 32 and face is not None:
                captured += 1
                path = os.path.join(output_dir, f"{captured}.jpg")
                if not cv2.imwrite(path, frame):
                    raise RuntimeError(f"Could not save face sample: {path}")

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print(f"Saved {captured} face samples for voter {identity} in {output_dir}")


if __name__ == "__main__":
    main()
