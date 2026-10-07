import tkinter as tk
import os

from database import initialize_database
from data.demo_voters import load_demo_voters

from services.admin_security import seed_demo_admin_accounts
from config import LEVEL_DATABASE_PATHS
from services.level_database import initialize_all_level_databases
from services.four_level_sync import establish_initial_trust

from gui.login import LoginScreen
from gui.voter_verification import VoterVerificationScreen
from gui.biometric import BiometricScreen
from gui.ballot import BallotScreen
from gui.result import ResultScreen

from gui.admin_login import AdminLoginScreen
from gui.admin_face import AdminFaceVerificationScreen
from gui.admin_2fa import Admin2FAScreen

from gui.admin_dashboards import (
    BoothDashboard,
    ZonalDashboard,
    DeputyDashboard,
    CentralDashboard,
)


class VeriVoteApp:

    def __init__(self, root):

        self.root = root

        # =================================================
        # WINDOW
        # =================================================

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

        # =================================================
        # SCREEN REFERENCES
        # =================================================

        self.login_screen = None
        self.admin_login_screen = None
        self.admin_face_screen = None
        self.admin_2fa_screen = None

        self.voter_screen = None
        self.biometric_screen = None
        self.ballot_screen = None
        self.result_screen = None

        self.admin_dashboards = {}

        self.current_admin_account = None

        # =================================================
        # CREATE MAIN LOGIN
        # =================================================

        self.login_screen = LoginScreen(
            root,
            self.show_voter_verification,
            self.show_admin_login
        )

        # =================================================
        # CREATE ADMIN LOGIN
        # =================================================

        self.admin_login_screen = AdminLoginScreen(
            root,
            self.handle_admin_password_success,
            self.show_main_login
        )

        # =================================================
        # CREATE VOTER VERIFICATION
        # =================================================

        self.voter_screen = VoterVerificationScreen(
            root,
            self.show_biometric
        )

        # =================================================
        # START
        # =================================================

        self.login_screen.show()

    # =====================================================
    # HIDE ALL SCREENS
    # =====================================================

    def hide_all(self):

        screens = [
            self.login_screen,
            self.admin_login_screen,
            self.admin_face_screen,
            self.admin_2fa_screen,
            self.voter_screen,
            self.biometric_screen,
            self.ballot_screen,
            self.result_screen,
            *self.admin_dashboards.values(),
        ]

        for screen in screens:

            if screen is not None:

                try:
                    screen.hide()

                except Exception:
                    pass

    # =====================================================
    # MAIN LOGIN
    # =====================================================

    def show_main_login(self):

        self.hide_all()

        self.login_screen.show()

    # =====================================================
    # ADMIN LOGIN
    # =====================================================

    def show_admin_login(self):

        self.hide_all()

        self.admin_login_screen.show()

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
            "constituency": voter_result["constituency"],
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
    # ADMIN PASSWORD SUCCESS
    # =====================================================

    def handle_admin_password_success(
        self,
        account
    ):

        self.current_admin_account = account

        # -------------------------------------------------
        # CENTRAL -> FACE VERIFICATION
        # -------------------------------------------------

        if account["role"] == "CENTRAL":

            self.admin_face_screen = (
                AdminFaceVerificationScreen(
                    self.root,
                    account,
                    self.handle_central_face_success,
                    self.show_admin_login
                )
            )

            self.hide_all()

            self.admin_face_screen.show()

            return

        # -------------------------------------------------
        # OTHER LEVELS -> DIRECT DASHBOARD
        # -------------------------------------------------

        self.show_admin_dashboard(
            account
        )

    # =====================================================
    # CENTRAL FACE SUCCESS
    # =====================================================

    def handle_central_face_success(
        self,
        account
    ):

        self.current_admin_account = account

        # -------------------------------------------------
        # CENTRAL -> 2FA
        # -------------------------------------------------

        self.admin_2fa_screen = Admin2FAScreen(
            self.root,
            account,
            self.show_admin_dashboard,
            self.show_admin_login
        )

        self.hide_all()

        self.admin_2fa_screen.show()

    # =====================================================
    # SHOW CORRECT ADMIN DASHBOARD
    # =====================================================

    def show_admin_dashboard(
        self,
        account
    ):

        self.current_admin_account = account

        role = account["role"]

        dashboard_class = {
            "BOOTH": BoothDashboard,
            "ZONAL": ZonalDashboard,
            "DEPUTY": DeputyDashboard,
            "CENTRAL": CentralDashboard,
        }.get(role)

        if dashboard_class is None:

            raise ValueError(
                f"Unsupported admin role: {role}"
            )

        self.admin_dashboards[role] = dashboard_class(
            self.root,
            account,
            self.logout_admin
        )

        self.hide_all()

        self.admin_dashboards[role].show()

    # =====================================================
    # ADMIN LOGOUT
    # =====================================================

    def logout_admin(self):

        self.current_admin_account = None

        self.hide_all()

        self.admin_login_screen.show()


# =========================================================
# MAIN
# =========================================================

def main():

    # =====================================================
    # DATABASE
    # =====================================================

    initialize_database()

    # Fresh copies start with four initialized level databases and a trusted
    # GENESIS checkpoint, so the Central dashboard opens cleanly on first run.
    fresh_level_databases = not all(
        os.path.exists(path)
        for path in LEVEL_DATABASE_PATHS.values()
    )
    initialize_all_level_databases()
    if fresh_level_databases:
        establish_initial_trust()

    # =====================================================
    # ADMIN ACCOUNTS
    # =====================================================

    seed_demo_admin_accounts()

    # =====================================================
    # DEMO VOTERS
    # =====================================================

    load_demo_voters()

    # =====================================================
    # TKINTER
    # =====================================================

    root = tk.Tk()

    VeriVoteApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()
