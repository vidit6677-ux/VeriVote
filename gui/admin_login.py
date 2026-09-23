import tkinter as tk
from tkinter import messagebox

from config import ADMIN_LEVEL_LABELS, ADMIN_LEVELS
from services.admin_security import authenticate_admin


class AdminLoginScreen:

    def __init__(
        self,
        root,
        on_success,
        on_back
    ):

        self.root = root
        self.on_success = on_success
        self.on_back = on_back

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.border = "#D9E2EC"
        self.white = "#FFFFFF"
        self.error = "#B42318"

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
            height=82
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Label(
            header,
            text="VERIVOTE",
            font=("Arial", 25, "bold"),
            fg="white",
            bg=self.primary
        ).pack(
            side="left",
            padx=35
        )

        tk.Label(
            header,
            text="ADMIN SECURITY PORTAL",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(
            side="right",
            padx=35
        )

        # -------------------------------------------------
        # MAIN CARD
        # -------------------------------------------------

        card = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        card.place(
            relx=0.5,
            rely=0.48,
            anchor="center",
            width=520,
            height=590
        )

        tk.Label(
            card,
            text="🔐",
            font=("Arial", 38),
            bg=self.white
        ).pack(
            pady=(20, 4)
        )

        tk.Label(
            card,
            text="Administrator Login",
            font=("Arial", 22, "bold"),
            fg=self.text,
            bg=self.white
        ).pack()

        tk.Label(
            card,
            text="Select your administrative level and authenticate",
            font=("Arial", 10),
            fg=self.muted,
            bg=self.white
        ).pack(
            pady=(5, 24)
        )

        # -------------------------------------------------
        # ROLE
        # -------------------------------------------------

        tk.Label(
            card,
            text="ADMINISTRATIVE LEVEL",
            font=("Arial", 10, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(
            anchor="w",
            padx=55
        )

        self.role_var = tk.StringVar(
            value="BOOTH"
        )

        self.role_menu = tk.OptionMenu(
            card,
            self.role_var,
            *ADMIN_LEVELS
        )

        self.role_menu.config(
            font=("Arial", 11),
            bg=self.white,
            fg=self.text,
            activebackground="#EAF2FF",
            relief="solid",
            bd=1,
            width=30
        )

        self.role_menu["menu"].config(
            font=("Arial", 10)
        )

        self.role_menu.pack(
            padx=55,
            pady=(6, 15),
            fill="x"
        )

        # -------------------------------------------------
        # USERNAME
        # -------------------------------------------------

        tk.Label(
            card,
            text="USERNAME",
            font=("Arial", 10, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(
            anchor="w",
            padx=55
        )

        self.username_entry = tk.Entry(
            card,
            font=("Arial", 12),
            relief="solid",
            bd=1
        )

        self.username_entry.pack(
            padx=55,
            pady=(6, 15),
            fill="x",
            ipady=7
        )

        # -------------------------------------------------
        # PASSWORD
        # -------------------------------------------------

        tk.Label(
            card,
            text="PASSWORD",
            font=("Arial", 10, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(
            anchor="w",
            padx=55
        )

        self.password_entry = tk.Entry(
            card,
            show="●",
            font=("Arial", 12),
            relief="solid",
            bd=1
        )

        self.password_entry.pack(
            padx=55,
            pady=(6, 22),
            fill="x",
            ipady=7
        )

        # -------------------------------------------------
        # LOGIN BUTTON
        # -------------------------------------------------

        tk.Button(
            card,
            text="AUTHENTICATE",
            command=self.login,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            pady=11
        ).pack(
            fill="x",
            padx=55
        )

        # -------------------------------------------------
        # BACK BUTTON
        # -------------------------------------------------

        tk.Button(
            card,
            text="BACK TO POLLING CENTRE LOGIN",
            command=self.on_back,
            bg=self.white,
            fg=self.primary,
            activebackground="#EAF2FF",
            activeforeground=self.primary_dark,
            font=("Arial", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            pady=8
        ).pack(
            fill="x",
            padx=55,
            pady=(10, 12)
        )

        # -------------------------------------------------
        # SECURITY NOTE
        # -------------------------------------------------

        tk.Label(
            card,
            text=(
                "BOOTH • ZONAL • DEPUTY • CENTRAL\n"
                "Role-based access control is enforced."
            ),
            font=("Arial", 9),
            fg=self.muted,
            bg=self.white,
            justify="center"
        ).pack()

        self.username_entry.focus_set()

        self.password_entry.bind(
            "<Return>",
            lambda _event: self.login()
        )

    # =====================================================
    # SHOW
    # =====================================================

    def show(self):

        self.frame.pack(
            fill="both",
            expand=True
        )

        self.username_entry.focus_set()

    # =====================================================
    # HIDE
    # =====================================================

    def hide(self):

        self.frame.pack_forget()

    # =====================================================
    # LOGIN
    # =====================================================

    def login(self):

        username = (
            self.username_entry
            .get()
            .strip()
        )

        password = (
            self.password_entry
            .get()
        )

        role = (
            self.role_var
            .get()
            .strip()
            .upper()
        )

        if not username:

            messagebox.showwarning(
                "Missing Username",
                "Please enter your administrator username."
            )

            return

        if not password:

            messagebox.showwarning(
                "Missing Password",
                "Please enter your administrator password."
            )

            return

        success, account, message = (
            authenticate_admin(
                username,
                password,
                role
            )
        )

        if not success:

            messagebox.showerror(
                "Authentication Failed",
                message
            )

            self.password_entry.delete(
                0,
                tk.END
            )

            return

        self.password_entry.delete(
            0,
            tk.END
        )

        self.on_success(
            account
        )