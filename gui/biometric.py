import tkinter as tk
from tkinter import messagebox

from services.biometric_service import verify_face_from_camera


class BiometricScreen:

    def __init__(self, root, voter_data, on_success):

        self.root = root
        self.voter_data = voter_data
        self.on_success = on_success

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.white = "#FFFFFF"
        self.green = "#15803D"
        self.red = "#B42318"
        self.border = "#D9E2EC"

        self.frame = tk.Frame(
            root,
            bg=self.bg
        )

        # =================================================
        # HEADER
        # =================================================

        header = tk.Frame(
            self.frame,
            bg=self.primary,
            height=75
        )

        header.pack(fill="x")
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
            pady=20
        )

        tk.Label(
            header,
            text="FACE VERIFICATION",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(
            side="right",
            padx=30
        )

        # =================================================
        # TITLE
        # =================================================

        tk.Label(
            self.frame,
            text="Face Verification",
            font=("Arial", 25, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(
            pady=(35, 5)
        )

        tk.Label(
            self.frame,
            text="Verify the voter's identity using the polling terminal camera",
            font=("Arial", 12),
            fg=self.muted,
            bg=self.bg
        ).pack()

        # =================================================
        # VOTER CARD
        # =================================================

        voter_card = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        voter_card.pack(
            pady=25,
            padx=120,
            fill="x"
        )

        tk.Label(
            voter_card,
            text="VOTER IDENTIFIED FROM QR",
            font=("Arial", 9, "bold"),
            fg=self.muted,
            bg=self.white
        ).pack(
            pady=(18, 2)
        )

        tk.Label(
            voter_card,
            text=self.voter_data["name"],
            font=("Arial", 18, "bold"),
            fg=self.text,
            bg=self.white
        ).pack()

        tk.Label(
            voter_card,
            text=(
                f"Constituency: "
                f"{self.voter_data['constituency']}"
            ),
            font=("Arial", 11, "bold"),
            fg=self.primary,
            bg=self.white
        ).pack(
            pady=(3, 18)
        )

        # =================================================
        # CAMERA STATUS
        # =================================================

        status = tk.Frame(
            self.frame,
            bg="#EAF2FF",
            padx=25,
            pady=14
        )

        status.pack()

        tk.Label(
            status,
            text="● LAPTOP CAMERA READY",
            font=("Arial", 10, "bold"),
            fg=self.primary,
            bg="#EAF2FF"
        ).pack()

        tk.Label(
            self.frame,
            text="The camera will open when verification starts.",
            font=("Arial", 10),
            fg=self.muted,
            bg=self.bg
        ).pack(
            pady=10
        )

        # =================================================
        # VERIFY BUTTON
        # =================================================

        self.verify_button = tk.Button(
            self.frame,
            text="START FACE VERIFICATION",
            command=self.verify_face,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=12,
            bd=0
        )

        self.verify_button.pack(
            pady=18
        )

        tk.Label(
            self.frame,
            text="Prototype face verification using registered demo voter data",
            font=("Arial", 9, "italic"),
            fg=self.muted,
            bg=self.bg
        ).pack()

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
    # FACE VERIFICATION
    # =====================================================

    def verify_face(self):

        self.verify_button.config(
            state="disabled",
            text="OPENING CAMERA..."
        )

        self.root.update_idletasks()

        try:

            result = verify_face_from_camera(
                self.voter_data["identity"]
            )

        except Exception as error:

            result = {
                "success": False,
                "message": (
                    "Face verification encountered "
                    "an unexpected error.\n\n"
                    f"{error}"
                )
            }

        self.verify_button.config(
            state="normal",
            text="START FACE VERIFICATION"
        )

        # =================================================
        # SUCCESS
        # =================================================

        if result.get("success"):

            messagebox.showinfo(
                "Face Verification Successful",
                "✓ FACE VERIFIED\n\n"
                f"Voter: {self.voter_data['name']}\n"
                f"Constituency: "
                f"{self.voter_data['constituency']}\n\n"
                "Identity verification successful.\n"
                "Proceeding to ballot."
            )

            self.hide()

            self.on_success(
                self.voter_data
            )

            return

        # =================================================
        # FAILURE
        # =================================================

        messagebox.showerror(
            "Face Verification Failed",
            "✕ FACE VERIFICATION FAILED\n\n"
            + result.get(
                "message",
                "The face could not be verified."
            )
        )