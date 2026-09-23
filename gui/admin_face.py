import os
import tkinter as tk
from tkinter import messagebox

from config import CENTRAL_FACE_IDENTITY

from services.admin_security import (
    record_central_face_failure,
    record_central_face_success,
)

from services.biometric_service import (
    verify_face_from_camera
)


class AdminFaceVerificationScreen:

    def __init__(
        self,
        root,
        account,
        on_success,
        on_back
    ):

        self.root = root
        self.account = account
        self.on_success = on_success
        self.on_back = on_back

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.white = "#FFFFFF"
        self.red = "#B42318"
        self.border = "#D9E2EC"

        self.frame = tk.Frame(
            root,
            bg=self.bg
        )

        self._build()

    # =====================================================
    # BUILD
    # =====================================================

    def _build(self):

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        header = tk.Frame(
            self.frame,
            bg=self.primary,
            height=78
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Label(
            header,
            text="VERIVOTE",
            font=("Arial", 22, "bold"),
            fg="white",
            bg=self.primary
        ).pack(
            side="left",
            padx=30,
            pady=19
        )

        tk.Label(
            header,
            text="CENTRAL SECURITY • STEP 2",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(
            side="right",
            padx=30
        )

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        tk.Label(
            self.frame,
            text="Central Administrator Face Verification",
            font=("Arial", 23, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(
            pady=(38, 5)
        )

        tk.Label(
            self.frame,
            text=(
                "Password authentication passed. "
                "Complete the biometric factor."
            ),
            font=("Arial", 11),
            fg=self.muted,
            bg=self.bg
        ).pack()

        # -------------------------------------------------
        # ADMIN CARD
        # -------------------------------------------------

        card = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        card.pack(
            padx=150,
            pady=28,
            fill="x"
        )

        tk.Label(
            card,
            text="CENTRAL ADMINISTRATOR",
            font=("Arial", 9, "bold"),
            fg=self.muted,
            bg=self.white
        ).pack(
            pady=(20, 2)
        )

        tk.Label(
            card,
            text=self.account["username"],
            font=("Arial", 18, "bold"),
            fg=self.text,
            bg=self.white
        ).pack()

        tk.Label(
            card,
            text="Biometric identity: central_admin",
            font=("Arial", 10),
            fg=self.primary,
            bg=self.white
        ).pack(
            pady=(3, 18)
        )

        # -------------------------------------------------
        # CAMERA INFORMATION
        # -------------------------------------------------

        tk.Label(
            self.frame,
            text="The laptop camera will open during verification.",
            font=("Arial", 10),
            fg=self.muted,
            bg=self.bg
        ).pack()

        # -------------------------------------------------
        # VERIFY BUTTON
        # -------------------------------------------------

        self.verify_button = tk.Button(
            self.frame,
            text="START CENTRAL FACE VERIFICATION",
            command=self.verify_face,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=25,
            pady=11
        )

        self.verify_button.pack(
            pady=18
        )

        # -------------------------------------------------
        # CANCEL
        # -------------------------------------------------

        tk.Button(
            self.frame,
            text="CANCEL",
            command=self.on_back,
            bg=self.white,
            fg=self.primary,
            font=("Arial", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=24,
            pady=7
        ).pack()

        # -------------------------------------------------
        # CHECK CENTRAL FACE REFERENCE
        # -------------------------------------------------

        face_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            "face_data",
            f"{CENTRAL_FACE_IDENTITY}.jpg"
        )

        self.reference_exists = os.path.isfile(
            face_path
        )

        if not self.reference_exists:

            tk.Label(
                self.frame,
                text=(
                    "Central face reference not found.\n"
                    "Run:\n"
                    "python setup_central_face.py"
                ),
                font=("Arial", 9, "italic"),
                fg=self.red,
                bg=self.bg,
                justify="center"
            ).pack(
                pady=(14, 0)
            )

    # =====================================================
    # SHOW
    # =====================================================

    def show(self):

        self.frame.pack(
            fill="both",
            expand=True
        )

    # =====================================================
    # HIDE
    # =====================================================

    def hide(self):

        self.frame.pack_forget()

    # =====================================================
    # VERIFY FACE
    # =====================================================

    def verify_face(self):

        # -------------------------------------------------
        # MAKE SURE REFERENCE EXISTS
        # -------------------------------------------------

        if not self.reference_exists:

            messagebox.showerror(
                "Central Face Not Registered",
                (
                    "No central administrator reference face "
                    "is registered.\n\n"
                    "Run:\n"
                    "python setup_central_face.py\n\n"
                    "Then return to Central login."
                )
            )

            return

        # -------------------------------------------------
        # DISABLE BUTTON DURING VERIFICATION
        # -------------------------------------------------

        self.verify_button.config(
            state="disabled",
            text="VERIFYING..."
        )

        self.root.update_idletasks()

        try:

            result = verify_face_from_camera(
                CENTRAL_FACE_IDENTITY
            )

        except Exception as error:

            result = {
                "success": False,
                "message": str(error)
            }

        finally:

            self.verify_button.config(
                state="normal",
                text="START CENTRAL FACE VERIFICATION"
            )

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        if result.get("success"):

            record_central_face_success(
                self.account
            )

            messagebox.showinfo(
                "Central Authentication Successful",
                (
                    "✓ CENTRAL FACE VERIFIED\n\n"
                    "Password + face authentication completed."
                )
            )

            self.hide()

            self.on_success(
                self.account
            )

            return

        # -------------------------------------------------
        # FAILURE
        # -------------------------------------------------

        record_central_face_failure(
            self.account
        )

        messagebox.showerror(
            "Central Face Verification Failed",
            (
                "✕ CENTRAL FACE VERIFICATION FAILED\n\n"
                + result.get(
                    "message",
                    "Face could not be verified."
                )
            )
        )