import tkinter as tk
from tkinter import messagebox

from services.qr_service import (
    scan_qr_from_camera,
    process_qr
)


class VoterVerificationScreen:

    def __init__(self, root, on_success):

        self.root = root
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

        # =========================
        # HEADER
        # =========================

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
        ).pack(side="left", padx=30, pady=20)

        tk.Label(
            header,
            text="VOTER AUTHENTICATION",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(side="right", padx=30)

        tk.Label(
            self.frame,
            text="STEP 1 OF 4   QR IDENTITY  ->  FACE  ->  BALLOT  ->  COMPLETE",
            font=("Arial", 9, "bold"),
            fg=self.primary,
            bg="#EAF2FF",
            pady=8,
        ).pack(fill="x")

        # =========================
        # MAIN
        # =========================

        tk.Label(
            self.frame,
            text="Verify Voter Identity",
            font=("Arial", 25, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(pady=(35, 5))

        tk.Label(
            self.frame,
            text="Scan the voter's identification QR code",
            font=("Arial", 12),
            fg=self.muted,
            bg=self.bg
        ).pack()

        # =========================
        # SCANNER CARD
        # =========================

        scanner_card = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        scanner_card.pack(
            pady=28,
            padx=80
        )

        scanner_box = tk.Frame(
            scanner_card,
            width=390,
            height=190,
            bg="#F8FAFC",
            highlightbackground="#B8CCE8",
            highlightthickness=2
        )

        scanner_box.pack(
            padx=30,
            pady=25
        )

        scanner_box.pack_propagate(False)

        tk.Label(
            scanner_box,
            text="▣",
            font=("Arial", 42, "bold"),
            fg=self.primary,
            bg="#F8FAFC"
        ).pack(pady=(25, 0))

        tk.Label(
            scanner_box,
            text="QR CAMERA SCANNER",
            font=("Arial", 14, "bold"),
            fg=self.text,
            bg="#F8FAFC"
        ).pack()

        tk.Label(
            scanner_box,
            text="Camera will open when scanning starts",
            font=("Arial", 9),
            fg=self.muted,
            bg="#F8FAFC"
        ).pack(pady=4)

        # =========================
        # STATUS
        # =========================

        status_frame = tk.Frame(
            self.frame,
            bg="#EAF2FF",
            padx=20,
            pady=10
        )
        status_frame.pack()

        self.status_label = tk.Label(
            status_frame,
            text="● Ready to scan",
            font=("Arial", 10, "bold"),
            fg=self.primary,
            bg="#EAF2FF"
        )
        self.status_label.pack()

        # =========================
        # BUTTON
        # =========================

        self.scan_button = tk.Button(
            self.frame,
            text="START QR SCAN",
            command=self.start_scan,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            padx=45,
            pady=12,
            bd=0
        )

        self.scan_button.pack(pady=20)

        tk.Label(
            self.frame,
            text="Secure verification | Demo environment",
            font=("Arial", 9),
            fg=self.muted,
            bg=self.bg
        ).pack()

    def show(self):

        self.frame.pack(
            fill="both",
            expand=True
        )

    def hide(self):

        self.frame.pack_forget()

    def start_scan(self):

        self.scan_button.config(
            state="disabled",
            text="OPENING CAMERA..."
        )

        self.status_label.config(
            text="● Opening camera...",
            fg="#B45309"
        )

        self.root.update()

        try:

            qr_data, message = scan_qr_from_camera()

        except Exception as error:

            self.scan_button.config(
                state="normal",
                text="START QR SCAN"
            )

            self.status_label.config(
                text="● Scanner error",
                fg=self.red
            )

            messagebox.showerror(
                "QR Scanner Error",
                str(error)
            )

            return

        self.scan_button.config(
            state="normal",
            text="START QR SCAN"
        )

        if qr_data is None:

            self.status_label.config(
                text="● Scan cancelled",
                fg=self.muted
            )

            messagebox.showwarning(
                "QR Scanner",
                message
            )

            return

        self.status_label.config(
            text="[SCAN] QR detected - verifying...",
            fg=self.primary
        )

        self.root.update()

        result = process_qr(qr_data)

        if not result["success"]:

            self.status_label.config(
                text="● Authentication failed",
                fg=self.red
            )

            messagebox.showerror(
                "Authentication Failed",
                result["message"]
            )

            return

        self.status_label.config(
            text="● Voter verified successfully",
            fg=self.green
        )

        voter_message = (
            "VOTER VERIFIED [OK]\n\n"
            f"Name: {result['name']}\n"
            f"Demo ID: {result['identity']}\n"
            f"Constituency: {result['constituency']}\n\n"
            "Voter is eligible to proceed."
        )

        messagebox.showinfo(
            "Voter Authentication Successful",
            voter_message
        )

        self.hide()
        self.on_success(result)
