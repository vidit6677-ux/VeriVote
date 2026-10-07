import tkinter as tk
from tkinter import messagebox


class ResultScreen:

    def __init__(
        self,
        root,
        vote_data,
        on_finish
    ):

        self.root = root
        self.vote_data = vote_data
        self.on_finish = on_finish

        self.bg = "#F4F7FB"
        self.green = "#15803D"
        self.green_bg = "#ECFDF3"
        self.primary = "#1557A6"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.white = "#FFFFFF"
        self.border = "#D9E2EC"
        self.orange = "#B54708"

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

        header.pack(
            fill="x"
        )

        header.pack_propagate(
            False
        )

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
            text="VOTE CONFIRMATION",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(
            side="right",
            padx=30
        )

        tk.Label(
            self.frame,
            text="STEP 4 OF 4   QR IDENTITY  ->  FACE  ->  BALLOT  ->  COMPLETE",
            font=("Arial", 9, "bold"),
            fg=self.primary,
            bg="#EAF2FF",
            pady=8,
        ).pack(fill="x")

        # =================================================
        # SUCCESS
        # =================================================

        tk.Label(
            self.frame,
            text="[OK]",
            font=("Arial", 52, "bold"),
            fg=self.green,
            bg=self.bg
        ).pack(
            pady=(30, 0)
        )

        tk.Label(
            self.frame,
            text="VOTE RECORDED",
            font=("Arial", 25, "bold"),
            fg=self.green,
            bg=self.bg
        ).pack()

        tk.Label(
            self.frame,
            text=(
                "Your vote has been successfully recorded."
            ),
            font=("Arial", 12),
            fg=self.muted,
            bg=self.bg
        ).pack(
            pady=5
        )

        # =================================================
        # SMS STATUS
        # =================================================

        sms_sent = vote_data.get(
            "sms_sent",
            False
        )

        if sms_sent:

            sms_text = (
                "[OK]  SMS confirmation sent to your "
                "registered mobile number."
            )

            sms_color = self.green
            sms_bg = self.green_bg

        else:

            sms_text = (
                "[WARN]  Vote recorded, but SMS "
                "confirmation could not be sent."
            )

            sms_color = self.orange
            sms_bg = "#FFF7ED"

        tk.Label(
            self.frame,
            text=sms_text,
            font=("Arial", 10, "bold"),
            fg=sms_color,
            bg=sms_bg,
            padx=20,
            pady=10
        ).pack(
            pady=12
        )

        # =================================================
        # STATUS CARD
        # =================================================

        card = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        card.pack(
            padx=170,
            pady=20,
            fill="x"
        )

        # Reference

        tk.Label(
            card,
            text="VOTE REFERENCE",
            font=("Arial", 9, "bold"),
            fg=self.muted,
            bg=self.white
        ).pack(
            pady=(18, 3)
        )

        tk.Label(
            card,
            text=vote_data.get(
                "vote_reference",
                "N/A"
            ),
            font=("Courier", 13, "bold"),
            fg=self.primary,
            bg=self.white
        ).pack()

        # Constituency

        tk.Label(
            card,
            text="CONSTITUENCY",
            font=("Arial", 9, "bold"),
            fg=self.muted,
            bg=self.white
        ).pack(
            pady=(18, 3)
        )

        tk.Label(
            card,
            text=vote_data.get(
                "constituency",
                "N/A"
            ),
            font=("Arial", 12, "bold"),
            fg=self.primary,
            bg=self.white
        ).pack()

        # Integrity

        tk.Label(
            card,
            text="INTEGRITY HASH",
            font=("Arial", 9, "bold"),
            fg=self.muted,
            bg=self.white
        ).pack(
            pady=(18, 3)
        )

        tk.Label(
            card,
            text=vote_data.get(
                "vote_hash",
                "N/A"
            ),
            font=("Courier", 8),
            wraplength=560,
            justify="center",
            fg=self.text,
            bg="#F8FAFC",
            padx=15,
            pady=12
        ).pack(
            padx=20,
            pady=(0, 18),
            fill="x"
        )

        # =================================================
        # PRIVACY
        # =================================================

        tk.Label(
            self.frame,
            text=(
                "SECURE RECEIPT | Your selected candidate is not "
                "included in the SMS confirmation."
            ),
            font=("Arial", 9),
            fg=self.muted,
            bg=self.bg
        ).pack(
            pady=5
        )

        # =================================================
        # NEXT
        # =================================================

        tk.Button(
            self.frame,
            text="NEXT VOTER",
            command=self.on_finish,
            bg=self.primary,
            fg="white",
            activebackground="#0D3F7A",
            activeforeground="white",
            font=("Arial", 11, "bold"),
            relief="flat",
            cursor="hand2",
            width=22,
            pady=10,
            bd=0
        ).pack(
            pady=20
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
