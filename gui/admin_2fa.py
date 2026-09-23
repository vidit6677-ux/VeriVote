import tkinter as tk
from tkinter import messagebox

from services.admin_2fa import verify_totp


class Admin2FAScreen:
    """
    Central administrator 2FA screen.

    The screen intentionally never displays the TOTP secret.
    The Central administrator enters the 6-digit code generated
    by their authenticator application.
    """

    def __init__(
        self,
        root,
        account,
        success_callback,
        back_callback,
    ):
        self.root = root
        self.account = account
        self.success_callback = success_callback
        self.back_callback = back_callback

        self.frame = tk.Frame(
            self.root,
            bg="#F4F7FB",
        )

        self.otp_var = tk.StringVar()

        self._build_ui()

    # =====================================================
    # BUILD UI
    # =====================================================

    def _build_ui(self):

        self.frame = tk.Frame(
            self.root,
            bg="#F4F7FB",
        )

        container = tk.Frame(
            self.frame,
            bg="white",
            bd=1,
            relief="solid",
            padx=40,
            pady=35,
        )

        container.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        tk.Label(
            container,
            text="CENTRAL ADMINISTRATOR",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#16213E",
        ).pack(pady=(0, 8))

        tk.Label(
            container,
            text="Two-Factor Authentication",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg="#2C3E50",
        ).pack(pady=(0, 18))

        tk.Label(
            container,
            text=(
                "Enter the 6-digit code from your\n"
                "authenticator application."
            ),
            font=("Segoe UI", 11),
            bg="white",
            fg="#555555",
            justify="center",
        ).pack(pady=(0, 20))

        tk.Label(
            container,
            text=f"Account: {self.account.get('username', '')}",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg="#34495E",
        ).pack(pady=(0, 12))

        self.otp_entry = tk.Entry(
            container,
            textvariable=self.otp_var,
            font=("Segoe UI", 18, "bold"),
            justify="center",
            width=10,
            show="•",
            relief="solid",
            bd=1,
        )

        self.otp_entry.pack(
            pady=(0, 20),
            ipady=6,
        )

        self.otp_entry.bind(
            "<Return>",
            self._verify,
        )

        button_frame = tk.Frame(
            container,
            bg="white",
        )

        button_frame.pack()

        tk.Button(
            button_frame,
            text="VERIFY 2FA",
            font=("Segoe UI", 11, "bold"),
            bg="#1F6FEB",
            fg="white",
            activebackground="#185ABC",
            activeforeground="white",
            width=16,
            command=self._verify,
            relief="flat",
            cursor="hand2",
        ).grid(
            row=0,
            column=0,
            padx=6,
        )

        tk.Button(
            button_frame,
            text="BACK",
            font=("Segoe UI", 11, "bold"),
            bg="#E5E7EB",
            fg="#1F2937",
            activebackground="#D1D5DB",
            width=12,
            command=self._back,
            relief="flat",
            cursor="hand2",
        ).grid(
            row=0,
            column=1,
            padx=6,
        )

        tk.Label(
            container,
            text="Your authenticator code is never stored or displayed here.",
            font=("Segoe UI", 9),
            bg="white",
            fg="#777777",
        ).pack(
            pady=(18, 0),
        )

    # =====================================================
    # VERIFY
    # =====================================================

    def _verify(self, event=None):

        otp = self.otp_var.get().strip()

        if not otp:
            messagebox.showwarning(
                "2FA Required",
                "Enter your 6-digit authenticator code.",
                parent=self.root,
            )
            self.otp_entry.focus_set()
            return

        if len(otp) != 6 or not otp.isdigit():
            messagebox.showerror(
                "Invalid OTP",
                "Enter exactly 6 digits.",
                parent=self.root,
            )
            self.otp_var.set("")
            self.otp_entry.focus_set()
            return

        try:
            success, message = verify_totp(
                self.account["username"],
                otp,
            )

        except Exception:
            success = False
            message = "Central 2FA verification failed."

        if success:

            self.otp_var.set("")

            messagebox.showinfo(
                "2FA Verified",
                "Central administrator authentication successful.",
                parent=self.root,
            )

            self.success_callback(
                self.account
            )

            return

        self.otp_var.set("")
        self.otp_entry.focus_set()

        messagebox.showerror(
            "2FA Failed",
            message,
            parent=self.root,
        )

    # =====================================================
    # BACK
    # =====================================================

    def _back(self):

        self.otp_var.set("")

        self.back_callback()

    # =====================================================
    # SHOW
    # =====================================================

    def show(self):

        self.frame.pack(
            fill="both",
            expand=True,
        )

        self.otp_var.set("")

        self.otp_entry.focus_set()

    # =====================================================
    # HIDE
    # =====================================================

    def hide(self):

        self.frame.pack_forget()
