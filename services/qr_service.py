import cv2


def scan_qr_from_camera():

    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        return None, "Camera could not be opened."

    detector = cv2.QRCodeDetector()

    while True:

        success, frame = camera.read()

        if not success:
            break

        # OpenCV detects and decodes the QR code
        data, points, _ = detector.detectAndDecode(frame)

        if data:

            # Draw a box around QR if detected
            if points is not None:
                points = points.astype(int)

                for i in range(4):
                    cv2.line(
                        frame,
                        tuple(points[0][i]),
                        tuple(points[0][(i + 1) % 4]),
                        (0, 255, 0),
                        3
                    )

            cv2.putText(
                frame,
                "QR DETECTED",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "VeriVote - QR Scanner",
                frame
            )

            cv2.waitKey(1000)

            camera.release()
            cv2.destroyAllWindows()

            return data.strip(), "QR detected successfully."

        cv2.putText(
            frame,
            "Show QR code to camera",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            "Press Q to cancel",
            (30, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "VeriVote - QR Scanner",
            frame
        )

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

    return None, "QR scanning cancelled."


def process_qr(identity):

    from services.voter_service import verify_voter

    return verify_voter(identity)