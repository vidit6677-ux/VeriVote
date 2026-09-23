import tkinter as tk

from database import initialize_database
from data.demo_voters import load_demo_voters

from gui.login import LoginScreen
from gui.voter_verification import VoterVerificationScreen
from gui.biometric import BiometricScreen
from gui.ballot import BallotScreen
from gui.result import ResultScreen
from gui.admin import AdminScreen


class VeriVoteApp:

    def __init__(self, root):

        self.root = root

        # =========================
        # WINDOW
        # =========================

        self.root.title(
            "VeriVote - Secure Polling Centre System"
        )

        self.root.geometry(
            "1000x720"
        )

        self.root.minsize(
            900,
            650
        )

        self.root.configure(
            bg="#F4F7FB"
        )

        # =========================
        # SCREEN REFERENCES
        # =========================

        self.login_screen = None
        self.voter_screen = None
        self.biometric_screen = None
        self.ballot_screen = None
        self.result_screen = None
        self.admin_screen = None

        # =========================
        # CREATE SCREENS
        # =========================

        self.login_screen = LoginScreen(
            root,
            self.show_voter_verification
        )

        self.voter_screen = VoterVerificationScreen(
            root,
            self.show_biometric
        )

        self.admin_screen = AdminScreen(
            root
        )

        # =========================
        # START
        # =========================

        self.login_screen.show()

    # =====================================================
    # HIDE ALL SCREENS
    # =====================================================

    def hide_all(self):

        screens = [
            self.login_screen,
            self.voter_screen,
            self.admin_screen,
            self.biometric_screen,
            self.ballot_screen,
            self.result_screen
        ]

        for screen in screens:

            if screen is not None:

                try:
                    screen.hide()
                except Exception:
                    pass

    # =====================================================
    # VOTER VERIFICATION
    # =====================================================

    def show_voter_verification(self):

        self.hide_all()

        self.voter_screen.show()

    # =====================================================
    # BIOMETRIC
    # =====================================================

    def show_biometric(self, voter_result):

        voter_data = {
            "identity": voter_result["identity"],
            "name": voter_result["name"],
            "constituency": voter_result["constituency"]
        }

        self.biometric_screen = BiometricScreen(
            self.root,
            voter_data,
            self.show_ballot
        )

        self.hide_all()

        self.biometric_screen.show()

    # =====================================================
    # BALLOT
    # =====================================================

    def show_ballot(self, voter_data):

        self.ballot_screen = BallotScreen(
            self.root,
            voter_data,
            self.show_result
        )

        self.hide_all()

        self.ballot_screen.show()

    # =====================================================
    # RESULT
    # =====================================================

    def show_result(self, vote_data):

        self.result_screen = ResultScreen(
            self.root,
            vote_data,
            self.show_next_voter
        )

        self.hide_all()

        self.result_screen.show()

    # =====================================================
    # NEXT VOTER
    # =====================================================

    def show_next_voter(self):

        self.hide_all()

        self.voter_screen.show()

    # =====================================================
    # ADMIN
    # =====================================================

    def show_admin(self):

        self.hide_all()

        self.admin_screen.show()


def main():

    # =========================
    # DATABASE
    # =========================

    initialize_database()

    # =========================
    # DEMO VOTERS
    # =========================

    load_demo_voters()

    # =========================
    # TKINTER
    # =========================

    root = tk.Tk()

    app = VeriVoteApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()