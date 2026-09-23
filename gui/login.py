import tkinter as tk
from tkinter import messagebox

from config import DEMO_CENTRE_ID


class LoginScreen:

    def __init__(self, root, on_success):

        self.root = root
        self.on_success = on_success

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.border = "#D9E2EC"
        self.white = "#FFFFFF"

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
            height=82
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="VERIVOTE",
            font=("Arial", 25, "bold"),
            fg="white",
            bg=self.primary
        ).pack(side="left", padx=35, pady=22)

        tk.Label(
            header,
            text="POLLING CENTRE TERMINAL",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(side="right", padx=35)

        # =========================
        # CENTER CARD
        # =========================

        outer = tk.Frame(
            self.frame,
            bg=self.bg
        )
        outer.pack(
            fill="both",
            expand=True
        )

        card = tk.Frame(
            outer,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        card.place(
            relx=0.5,
            rely=0.48,
            anchor="center",
            width=470,
            height=440
        )

        # Icon
        tk.Label(
            card,
            text="🔐",
            font=("Arial", 38),
            bg=self.white
        ).pack(pady=(28, 5))

        tk.Label(
            card,
            text="Polling Centre Login",
            font=("Arial", 22, "bold"),
            fg=self.text,
            bg=self.white
        ).pack()

        tk.Label(
            card,
            text="Authenticate the polling centre terminal",
            font=("Arial", 11),
            fg=self.muted,
            bg=self.white
        ).pack(pady=(5, 25))

        # Centre ID
        tk.Label(
            card,
            text="CENTRE ID",
            font=("Arial", 10, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(anchor="w", padx=55)

        self.centre_entry = tk.Entry(
            card,
            width=32,
            font=("Arial", 12),
            relief="solid",
            bd=1
        )
        self.centre_entry.pack(
            padx=55,
            pady=(6, 16),
            ipady=7
        )

        # Password
        tk.Label(
            card,
            text="PASSWORD",
            font=("Arial", 10, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(anchor="w", padx=55)

        self.password_entry = tk.Entry(
            card,
            width=32,
            show="●",
            font=("Arial", 12),
            relief="solid",
            bd=1
        )
        self.password_entry.pack(
            padx=55,
            pady=(6, 20),
            ipady=7
        )

        # Login
        tk.Button(
            card,
            text="LOGIN TO POLLING TERMINAL",
            command=self.login,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0
        ).pack(
            fill="x",
            padx=55,
            ipady=10
        )

        # Demo indicator
        tk.Label(
            card,
            text="● DEMONSTRATION ENVIRONMENT",
            font=("Arial", 9, "bold"),
            fg="#B45309",
            bg=self.white
        ).pack(pady=(18, 3))

        tk.Label(
            card,
            text="College project prototype",
            font=("Arial", 9),
            fg=self.muted,
            bg=self.white
        ).pack()

        self.centre_entry.focus_set()

        self.password_entry.bind(
            "<Return>",
            lambda event: self.login()
        )

    def show(self):
        self.frame.pack(fill="both", expand=True)

    def hide(self):
        self.frame.pack_forget()

    def login(self):

        centre = self.centre_entry.get().strip()
        password = self.password_entry.get().strip()

        if centre == DEMO_CENTRE_ID and password == "admin123":

            self.hide()
            self.on_success()

        else:

            messagebox.showerror(
                "Login Failed",
                "Invalid polling centre credentials.\n\n"
                "Demo Centre ID: PC-001\n"
                "Demo Password: admin123"
            )