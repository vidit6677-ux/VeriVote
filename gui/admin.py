import tkinter as tk
from tkinter import messagebox

from database import get_all_voters, get_vote_count
from services.integrity_service import verify_integrity


class AdminScreen:

    def __init__(self, root):

        self.root = root

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.white = "#FFFFFF"
        self.green = "#15803D"
        self.orange = "#B45309"
        self.border = "#D9E2EC"

        self.frame = tk.Frame(
            root,
            bg=self.bg
        )

        # HEADER

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
            text="ADMINISTRATOR DASHBOARD",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(side="right", padx=30)

        # TITLE

        tk.Label(
            self.frame,
            text="Polling Centre Dashboard",
            font=("Arial", 24, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(pady=(28, 3))

        tk.Label(
            self.frame,
            text="Monitor demo voter participation and ledger integrity",
            font=("Arial", 11),
            fg=self.muted,
            bg=self.bg
        ).pack()

        # STAT CARDS

        cards = tk.Frame(
            self.frame,
            bg=self.bg
        )
        cards.pack(
            fill="x",
            padx=45,
            pady=25
        )

        self.total_value = self.create_stat_card(
            cards,
            "DEMO VOTERS",
            "0"
        )

        self.votes_value = self.create_stat_card(
            cards,
            "VOTES CAST",
            "0"
        )

        self.remaining_value = self.create_stat_card(
            cards,
            "REMAINING",
            "0"
        )

        self.turnout_value = self.create_stat_card(
            cards,
            "TURNOUT",
            "0%"
        )

        # VOTER TABLE AREA

        table_card = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        table_card.pack(
            fill="both",
            expand=True,
            padx=45,
            pady=(0, 15)
        )

        tk.Label(
            table_card,
            text="VOTER STATUS",
            font=("Arial", 13, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(
            anchor="w",
            padx=20,
            pady=(15, 10)
        )

        # Table header

        header_row = tk.Frame(
            table_card,
            bg="#EAF2FF"
        )
        header_row.pack(
            fill="x",
            padx=15
        )

        headers = [
            ("VOTER", 0.30),
            ("CONSTITUENCY", 0.30),
            ("STATUS", 0.25)
        ]

        for text, width in headers:

            tk.Label(
                header_row,
                text=text,
                font=("Arial", 9, "bold"),
                fg=self.primary,
                bg="#EAF2FF",
                anchor="w"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=10,
                pady=8
            )

        self.voter_rows = tk.Frame(
            table_card,
            bg=self.white
        )

        self.voter_rows.pack(
            fill="both",
            expand=True,
            padx=15
        )

        # BUTTONS

        button_frame = tk.Frame(
            self.frame,
            bg=self.bg
        )
        button_frame.pack(
            pady=(0, 20)
        )

        tk.Button(
            button_frame,
            text="VERIFY LEDGER INTEGRITY",
            command=self.verify_ledger,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=9
        ).pack(side="left", padx=5)

        tk.Button(
            button_frame,
            text="REFRESH DATA",
            command=self.refresh,
            bg=self.white,
            fg=self.primary,
            activebackground="#EAF2FF",
            font=("Arial", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=20,
            pady=8
        ).pack(side="left", padx=5)

        self.refresh()

    def create_stat_card(self, parent, title, value):

        card = tk.Frame(
            parent,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )

        tk.Label(
            card,
            text=title,
            font=("Arial", 9, "bold"),
            fg=self.muted,
            bg=self.white
        ).pack(pady=(12, 2))

        label = tk.Label(
            card,
            text=value,
            font=("Arial", 22, "bold"),
            fg=self.primary,
            bg=self.white
        )

        label.pack(pady=(0, 12))

        return label

    def show(self):

        self.frame.pack(
            fill="both",
            expand=True
        )

        self.refresh()

    def hide(self):

        self.frame.pack_forget()

    def refresh(self):

        voters = get_all_voters()
        votes = get_vote_count()

        total_voters = len(voters)

        voted = sum(
            1 for voter in voters
            if voter[5] == 1
        )

        remaining = total_voters - voted

        if total_voters > 0:
            turnout = (voted / total_voters) * 100
        else:
            turnout = 0

        self.total_value.config(
            text=str(total_voters)
        )

        self.votes_value.config(
            text=str(votes)
        )

        self.remaining_value.config(
            text=str(remaining)
        )

        self.turnout_value.config(
            text=f"{turnout:.0f}%"
        )

        # Clear old rows

        for widget in self.voter_rows.winfo_children():
            widget.destroy()

        # Add voter rows

        for voter in voters:

            identity = voter[1]
            name = voter[2]
            constituency = voter[3]
            has_voted = voter[5]

            row = tk.Frame(
                self.voter_rows,
                bg=self.white
            )

            row.pack(
                fill="x",
                pady=1
            )

            tk.Label(
                row,
                text=name,
                font=("Arial", 10),
                fg=self.text,
                bg=self.white,
                anchor="w"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=10,
                pady=7
            )

            tk.Label(
                row,
                text=constituency,
                font=("Arial", 10),
                fg=self.muted,
                bg=self.white,
                anchor="w"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=10,
                pady=7
            )

            status_text = "✓ VOTED" if has_voted else "○ NOT VOTED"
            status_color = self.green if has_voted else self.orange

            tk.Label(
                row,
                text=status_text,
                font=("Arial", 9, "bold"),
                fg=status_color,
                bg=self.white,
                anchor="w"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=10,
                pady=7
            )

    def verify_ledger(self):

        success, message = verify_integrity()

        if success:

            messagebox.showinfo(
                "Ledger Integrity",
                "✓ INTEGRITY VERIFIED\n\n"
                + message
            )

        else:

            messagebox.showerror(
                "Integrity Violation",
                "⚠ INTEGRITY VIOLATION DETECTED\n\n"
                + message
            )