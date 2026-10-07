import tkinter as tk
from tkinter import messagebox

from services.privacy_service import issue_one_time_ballot, submit_tokenized_ballot


CANDIDATES = {
    "Nanded West": [
        "Aman Sharma",
        "Shankar Rao Gupta",
        "Bhanu Rawat"
    ],

    "Nanded East": [
        "Amar Rajurkar",
        "Dilip Singh",
        "Dimple Nawab"
    ],

    "Old Akola City": [
        "Sagar Baruka",
        "Harish Alimchandani",
        "Dilip Mishra"
    ],

    "Akola": [
        "Sajid Pathan",
        "Amit Taakwale",
        "Sharda Kelkar"
    ]
}


class BallotScreen:

    def __init__(self, parent, voter_data, on_success):

        self.parent = parent
        self.voter_data = voter_data
        self.on_success = on_success

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.white = "#FFFFFF"
        self.border = "#D9E2EC"

        self.frame = tk.Frame(
            parent,
            bg=self.bg
        )

        self.selected_candidate = tk.StringVar(
            value=""
        )

        self.build_ui()

    def build_ui(self):

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
            text="OFFICIAL BALLOT",
            font=("Arial", 10, "bold"),
            fg="#DCEAFF",
            bg=self.primary
        ).pack(side="right", padx=30)

        tk.Label(
            self.frame,
            text="STEP 3 OF 4   QR IDENTITY  ->  FACE  ->  BALLOT  ->  COMPLETE",
            font=("Arial", 9, "bold"),
            fg=self.primary,
            bg="#EAF2FF",
            pady=8,
        ).pack(fill="x")

        # TITLE

        tk.Label(
            self.frame,
            text="Official Ballot",
            font=("Arial", 26, "bold"),
            fg=self.text,
            bg=self.bg
        ).pack(pady=(30, 4))

        tk.Label(
            self.frame,
            text="Select ONE candidate",
            font=("Arial", 12),
            fg=self.muted,
            bg=self.bg
        ).pack()

        # VOTER INFO

        info = tk.Frame(
            self.frame,
            bg="#EAF2FF",
            highlightbackground="#C7D9F2",
            highlightthickness=1
        )
        info.pack(
            pady=20,
            padx=150,
            fill="x"
        )

        tk.Label(
            info,
            text=self.voter_data["name"],
            font=("Arial", 14, "bold"),
            fg=self.text,
            bg="#EAF2FF"
        ).pack(pady=(12, 2))

        tk.Label(
            info,
            text=f"Constituency  |  {self.voter_data['constituency']}",
            font=("Arial", 11, "bold"),
            fg=self.primary,
            bg="#EAF2FF"
        ).pack(pady=(0, 12))

        constituency = self.voter_data["constituency"]
        candidates = CANDIDATES.get(constituency, [])

        # CANDIDATE CARD

        candidate_frame = tk.Frame(
            self.frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1
        )
        candidate_frame.pack(
            padx=150,
            fill="x"
        )

        tk.Label(
            candidate_frame,
            text=f"Candidates | {constituency}",
            font=("Arial", 14, "bold"),
            fg=self.text,
            bg=self.white
        ).pack(
            anchor="w",
            padx=25,
            pady=(18, 12)
        )

        if not candidates:

            tk.Label(
                candidate_frame,
                text="No candidates configured.",
                font=("Arial", 12),
                fg="#B42318",
                bg=self.white
            ).pack(pady=20)

        for candidate in candidates:

            row = tk.Frame(
                candidate_frame,
                bg=self.white
            )
            row.pack(
                fill="x",
                padx=20,
                pady=3
            )

            tk.Radiobutton(
                row,
                text=candidate,
                variable=self.selected_candidate,
                value=candidate,
                font=("Arial", 12),
                bg=self.white,
                activebackground=self.white,
                fg=self.text,
                selectcolor="#EAF2FF",
                anchor="w",
                cursor="hand2"
            ).pack(
                fill="x",
                ipady=7
            )

        # CAST BUTTON

        self.cast_button = tk.Button(
            self.frame,
            text="CAST VOTE",
            command=self.cast,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            cursor="hand2",
            width=25,
            pady=11,
            bd=0
        )
        self.cast_button.pack(pady=(22, 8))

        tk.Label(
            self.frame,
            text="SECURE BALLOT | Review carefully. A cast vote cannot be changed.",
            font=("Arial", 9),
            fg=self.muted,
            bg=self.bg
        ).pack()

    def cast(self):

        candidate = self.selected_candidate.get()

        if not candidate:

            messagebox.showwarning(
                "No Candidate Selected",
                "Please select a candidate before casting your vote."
            )
            return

        confirm = messagebox.askyesno(
            "Confirm Vote",
            f"Selected Candidate:\n\n"
            f"{candidate}\n\n"
            f"Constituency:\n"
            f"{self.voter_data['constituency']}\n\n"
            "Once cast, this vote cannot be changed.\n\n"
            "Do you want to continue?"
        )

        if not confirm:
            return

        self.cast_button.config(
            state="disabled",
            text="RECORDING VOTE..."
        )

        self.parent.update_idletasks()

        try:

            token, issue_message = issue_one_time_ballot(
                self.voter_data["identity"],
                self.voter_data["constituency"],
            )

            if token is None:
                result = {
                    "success": False,
                    "message": issue_message,
                }
            else:
                result = submit_tokenized_ballot(token, candidate)

        except Exception as error:

            self.cast_button.config(
                state="normal",
                text="CAST VOTE"
            )

            messagebox.showerror(
                "Vote Failed",
                f"An unexpected error occurred:\n\n{error}"
            )

            return

        if not result.get("success"):

            self.cast_button.config(
                state="normal",
                text="CAST VOTE"
            )

            messagebox.showerror(
                "Vote Failed",
                result.get(
                    "message",
                    "Unable to record vote."
                )
            )

            return

        self.on_success(result)

    def show(self):

        self.frame.pack(
            fill="both",
            expand=True
        )

    def hide(self):

        self.frame.pack_forget()
