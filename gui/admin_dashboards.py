import time
import tkinter as tk
from tkinter import messagebox

from config import (
    ADMIN_LEVEL_LABELS,
    ADMIN_SESSION_TIMEOUT_SECONDS,
    ADMIN_LEVELS,
)

from database import (
    get_all_voters,
    get_vote_count,
)

from services.integrity_service import (
    verify_integrity,
)

from services.four_level_sync import (
    get_four_level_security_summary,
)



# =========================================================
# BASE ADMIN DASHBOARD
# =========================================================

class BaseAdminDashboard:

    ROLE = "BOOTH"

    TITLE = "Administrative Dashboard"

    SUBTITLE = ""

    PERMISSION_TEXT = ""

    def __init__(
        self,
        root,
        account,
        on_logout,
    ):

        self.root = root
        self.account = account
        self.on_logout = on_logout

        self.role = account["role"]

        self.session_started = time.time()

        # -------------------------------------------------
        # COLORS
        # -------------------------------------------------

        self.bg = "#F4F7FB"
        self.primary = "#1557A6"
        self.primary_dark = "#0D3F7A"
        self.text = "#172B4D"
        self.muted = "#667085"
        self.white = "#FFFFFF"
        self.green = "#15803D"
        self.red = "#B42318"
        self.orange = "#B45309"
        self.border = "#D9E2EC"
        self.blue_light = "#EAF2FF"

        # -------------------------------------------------
        # MAIN FRAME
        # -------------------------------------------------

        self.frame = tk.Frame(
            root,
            bg=self.bg,
        )

        self.status_labels = {}

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
            height=78,
        )

        header.pack(
            fill="x"
        )

        header.pack_propagate(False)

        tk.Label(
            header,
            text="VERIVOTE",
            font=("Arial", 21, "bold"),
            fg="white",
            bg=self.primary,
        ).pack(
            side="left",
            padx=(28, 14),
            pady=20,
        )

        tk.Label(
            header,
            text=ADMIN_LEVEL_LABELS[
                self.role
            ].upper(),
            font=("Arial", 9, "bold"),
            fg="#DCEAFF",
            bg=self.primary,
        ).pack(
            side="left",
            pady=22,
        )

        tk.Button(
            header,
            text="LOGOUT",
            command=self.logout,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 9, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=12,
            pady=5,
        ).pack(
            side="right",
            padx=28,
        )

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        tk.Label(
            self.frame,
            text=self.TITLE,
            font=("Arial", 23, "bold"),
            fg=self.text,
            bg=self.bg,
        ).pack(
            pady=(20, 3),
        )

        tk.Label(
            self.frame,
            text=self.SUBTITLE,
            font=("Arial", 10),
            fg=self.muted,
            bg=self.bg,
        ).pack()

        # -------------------------------------------------
        # STATISTICS
        # -------------------------------------------------

        self.stat_frame = tk.Frame(
            self.frame,
            bg=self.bg,
        )

        self.stat_frame.pack(
            fill="x",
            padx=38,
            pady=18,
        )

        self.stat_labels = {}

        self._create_stat(
            "voters",
            "REGISTERED VOTERS",
        )

        self._create_stat(
            "votes",
            "VOTES CAST",
        )

        self._create_stat(
            "remaining",
            "REMAINING",
        )

        self._create_stat(
            "turnout",
            "TURNOUT",
        )

        # -------------------------------------------------
        # CONTENT
        # -------------------------------------------------

        body = tk.Frame(
            self.frame,
            bg=self.bg,
        )

        body.pack(
            fill="both",
            expand=True,
            padx=38,
            pady=(0, 14),
        )

        self.left_card = tk.Frame(
            body,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1,
        )

        self.left_card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 7),
        )

        self.right_card = tk.Frame(
            body,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1,
        )

        self.right_card.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(7, 0),
        )

        self._build_left_card()

        self._build_right_card()

        # -------------------------------------------------
        # CONTROLS
        # -------------------------------------------------

        controls = tk.Frame(
            self.frame,
            bg=self.bg,
        )

        controls.pack(
            pady=(0, 12),
        )

        tk.Button(
            controls,
            text="VERIFY SECURITY",
            command=self.verify_security,
            bg=self.primary,
            fg="white",
            activebackground=self.primary_dark,
            activeforeground="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=9,
        ).pack(
            side="left",
            padx=4,
        )

        tk.Button(
            controls,
            text="REFRESH",
            command=self.refresh,
            bg=self.white,
            fg=self.primary,
            activebackground=self.blue_light,
            font=("Arial", 10, "bold"),
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=18,
            pady=8,
        ).pack(
            side="left",
            padx=4,
        )

    # =====================================================
    # STAT CARD
    # =====================================================

    def _create_stat(
        self,
        key,
        title,
    ):

        card = tk.Frame(
            self.stat_frame,
            bg=self.white,
            highlightbackground=self.border,
            highlightthickness=1,
        )

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=4,
        )

        tk.Label(
            card,
            text=title,
            font=("Arial", 8, "bold"),
            fg=self.muted,
            bg=self.white,
        ).pack(
            pady=(9, 1),
        )

        value = tk.Label(
            card,
            text="0",
            font=("Arial", 20, "bold"),
            fg=self.primary,
            bg=self.white,
        )

        value.pack(
            pady=(0, 9),
        )

        self.stat_labels[key] = value

    # =====================================================
    # LEFT CARD
    # =====================================================

    def _build_left_card(self):

        tk.Label(
            self.left_card,
            text="SECURITY STATUS",
            font=("Arial", 12, "bold"),
            fg=self.text,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4),
        )

        tk.Label(
            self.left_card,
            text=self.PERMISSION_TEXT,
            font=("Arial", 9),
            fg=self.muted,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 14),
        )

        self.status_frame = tk.Frame(
            self.left_card,
            bg=self.white,
        )

        self.status_frame.pack(
            fill="both",
            expand=True,
            padx=15,
        )

        self._add_status_row(
            "Administrative Role",
            self.role,
            self.primary,
            "#EAF2FF",
            "role",
        )

        self._add_status_row(
            "Local Ledger",
            "CHECKING...",
            self.orange,
            "#FFF7ED",
            "ledger",
        )

        self._add_status_row(
            "Four-Level Sync",
            "CHECKING...",
            self.orange,
            "#FFF7ED",
            "sync",
        )

        self._add_status_row(
            "Security Alerts",
            "CHECKING...",
            self.orange,
            "#FFF7ED",
            "alerts",
        )

    # =====================================================
    # RIGHT CARD
    # =====================================================

    def _build_right_card(self):

        tk.Label(
            self.right_card,
            text="SECURITY ALERTS",
            font=("Arial", 12, "bold"),
            fg=self.text,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4),
        )

        tk.Label(
            self.right_card,
            text=(
                "Alerts visible to this administrative level"
            ),
            font=("Arial", 9),
            fg=self.muted,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 10),
        )

        self.alert_frame = tk.Frame(
            self.right_card,
            bg=self.white,
        )

        self.alert_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 12),
        )

    # =====================================================
    # STATUS ROW
    # =====================================================

    def _add_status_row(
        self,
        title,
        value,
        fg,
        bg,
        key,
    ):

        row = tk.Frame(
            self.status_frame,
            bg="#FAFCFF",
        )

        row.pack(
            fill="x",
            pady=4,
        )

        tk.Label(
            row,
            text=title,
            font=("Arial", 9),
            fg=self.text,
            bg="#FAFCFF",
        ).pack(
            side="left",
            padx=10,
            pady=8,
        )

        label = tk.Label(
            row,
            text=value,
            font=("Arial", 9, "bold"),
            fg=fg,
            bg=bg,
            padx=10,
            pady=5,
        )

        label.pack(
            side="right",
            padx=10,
        )

        self.status_labels[key] = label

    # =====================================================
    # SHOW / HIDE
    # =====================================================

    def show(self):

        self.session_started = time.time()

        self.frame.pack(
            fill="both",
            expand=True,
        )

        self.refresh()

        self._session_tick()

    def hide(self):

        self.frame.pack_forget()

    # =====================================================
    # SESSION TIMEOUT
    # =====================================================

    def _session_tick(self):

        if not self.frame.winfo_ismapped():
            return

        if (
            time.time() - self.session_started
            >= ADMIN_SESSION_TIMEOUT_SECONDS
        ):

            messagebox.showwarning(
                "Admin Session Expired",
                "The administrator session has expired for security.",
            )

            self.logout()

            return

        self.root.after(
            60_000,
            self._session_tick,
        )

    # =====================================================
    # REFRESH
    # =====================================================

    def refresh(self):

        voters = get_all_voters()

        votes = get_vote_count()

        total = len(voters)

        voted = sum(
            1
            for voter in voters
            if voter[5] == 1
        )

        remaining = total - voted

        turnout = (
            (voted / total) * 100
            if total
            else 0
        )

        self.stat_labels["voters"].config(
            text=str(total),
        )

        self.stat_labels["votes"].config(
            text=str(votes),
        )

        self.stat_labels["remaining"].config(
            text=str(remaining),
        )

        self.stat_labels["turnout"].config(
            text=f"{turnout:.0f}%",
        )

        # -------------------------------------------------
        # LOCAL LEDGER
        # -------------------------------------------------

        try:

            integrity_ok = verify_integrity()

        except Exception:

            integrity_ok = False

        if integrity_ok:

            self.status_labels["ledger"].config(
                text="VALID",
                fg=self.green,
                bg="#ECFDF3",
            )

        else:

            self.status_labels["ledger"].config(
                text="ALERT",
                fg=self.red,
                bg="#FEF3F2",
            )

        # -------------------------------------------------
        # FOUR-LEVEL SYNC
        # -------------------------------------------------

        try:

            summary = (
                get_four_level_security_summary()
            )

            overall = summary["overall"]

            level_info = summary["levels"].get(
                self.role
            )

            if level_info is None:

                sync_status = "MISSING"

            else:

                sync_status = level_info["status"]

            if (
                overall == "SECURE"
                and sync_status == "SYNCED"
            ):

                self.status_labels["sync"].config(
                    text="SYNCED",
                    fg=self.green,
                    bg="#ECFDF3",
                )

            elif sync_status in (
                "MISMATCH",
                "TAMPERED",
            ):

                self.status_labels["sync"].config(
                    text=sync_status,
                    fg=self.red,
                    bg="#FEF3F2",
                )

            else:

                self.status_labels["sync"].config(
                    text=sync_status,
                    fg=self.orange,
                    bg="#FFF7ED",
                )

        except Exception:

            self.status_labels["sync"].config(
                text="UNAVAILABLE",
                fg=self.red,
                bg="#FEF3F2",
            )

        # -------------------------------------------------
        # SECURITY ALERTS
        # -------------------------------------------------

        try:

            alerts = []

            for observer, observer_alerts in (
                summary.get("alerts", {}).items()
            ):

                for alert in observer_alerts:

                    alerts.append({
                        "source_level": (
                            f"{observer} observes "
                            f"{alert.get('source_level', observer)}"
                        ),
                        "event_type": alert.get(
                            "type",
                            "SECURITY_ALERT"
                        ),
                        "severity": "HIGH",
                        "details": alert.get(
                            "message",
                            "Security verification alert."
                        ),
                        "timestamp": "Current verification",
                    })

            alerts = alerts[:8]
            unread_count = len(alerts)

        except Exception:

            unread_count = 0
            alerts = []

        if unread_count == 0:

            self.status_labels["alerts"].config(
                text="NONE",
                fg=self.green,
                bg="#ECFDF3",
            )

        else:

            self.status_labels["alerts"].config(
                text=f"{unread_count} ALERT"
                + ("S" if unread_count != 1 else ""),
                fg=self.red,
                bg="#FEF3F2",
            )

        self._render_alerts(
            alerts
        )

    # =====================================================
    # RENDER ALERTS
    # =====================================================

    def _render_alerts(
        self,
        alerts
    ):

        for widget in self.alert_frame.winfo_children():

            widget.destroy()

        if not alerts:

            empty = tk.Frame(
                self.alert_frame,
                bg="#ECFDF3",
            )

            empty.pack(
                fill="x",
                pady=4,
            )

            tk.Label(
                empty,
                text="[OK] No visible security alerts",
                font=("Arial", 9, "bold"),
                fg=self.green,
                bg="#ECFDF3",
            ).pack(
                padx=10,
                pady=12,
            )

            return

        for alert in alerts:

            severity = (
                alert["severity"]
                .upper()
            )

            if severity == "CRITICAL":

                bg = "#FDECEC"
                fg = self.red

            elif severity == "HIGH":

                bg = "#FEF3F2"
                fg = self.red

            else:

                bg = "#FFF7ED"
                fg = self.orange

            card = tk.Frame(
                self.alert_frame,
                bg=bg,
                highlightbackground=self.border,
                highlightthickness=1,
            )

            card.pack(
                fill="x",
                pady=3,
            )

            title = (
                f"{alert['source_level']}  ->  "
                f"{alert['event_type']}"
            )

            tk.Label(
                card,
                text=title,
                font=("Arial", 9, "bold"),
                fg=fg,
                bg=bg,
                anchor="w",
            ).pack(
                fill="x",
                padx=10,
                pady=(7, 2),
            )

            tk.Label(
                card,
                text=alert["details"],
                font=("Arial", 8),
                fg=self.text,
                bg=bg,
                anchor="w",
                justify="left",
                wraplength=390,
            ).pack(
                fill="x",
                padx=10,
                pady=(0, 3),
            )

            tk.Label(
                card,
                text=alert["timestamp"],
                font=("Arial", 7),
                fg=self.muted,
                bg=bg,
                anchor="w",
            ).pack(
                fill="x",
                padx=10,
                pady=(0, 7),
            )

    # =====================================================
    # SECURITY VERIFICATION
    # =====================================================

    def verify_security(self):

        try:

            integrity_ok = verify_integrity()

        except Exception as error:

            messagebox.showerror(
                "Integrity Error",
                str(error),
            )

            return

        try:

            sync_summary = (
                get_four_level_security_summary()
            )

            alerts = []

            for observer, observer_alerts in (
                sync_summary.get("alerts", {}).items()
            ):

                for alert in observer_alerts:

                    alerts.append({
                        "source_level": (
                            f"{observer} observes "
                            f"{alert.get('source_level', observer)}"
                        ),
                        "event_type": alert.get(
                            "type",
                            "SECURITY_ALERT"
                        ),
                        "severity": "HIGH",
                        "details": alert.get(
                            "message",
                            "Security verification alert."
                        ),
                        "timestamp": "Current verification",
                    })

            alerts = alerts[:8]

        except Exception as error:

            messagebox.showerror(
                "Security Check Error",
                str(error),
            )

            return

        overall = sync_summary.get(
            "overall",
            "UNAVAILABLE"
        )

        alert_count = len(
            alerts
        )

        ledger_message = (
            "[OK] Ledger integrity verified."
            if integrity_ok
            else
            "[WARN] Ledger integrity check failed."
        )

        sync_message = (
            "[OK] Four-level synchronization is valid."
            if overall == "SECURE"
            else
            f"[WARN] Four-level status: {overall}"
        )

        alert_message = (
            "[OK] No visible security alerts."
            if alert_count == 0
            else
            f"[WARN] {alert_count} visible security alert(s)."
        )

        if (
            integrity_ok
            and overall == "SECURE"
            and alert_count == 0
        ):

            messagebox.showinfo(
                "Security Verification",
                (
                    "SYSTEM SECURITY CHECK\n\n"
                    f"{ledger_message}\n\n"
                    f"{sync_message}\n\n"
                    f"{alert_message}"
                ),
            )

        else:

            messagebox.showwarning(
                "Security Alert",
                (
                    "SYSTEM SECURITY CHECK\n\n"
                    f"{ledger_message}\n\n"
                    f"{sync_message}\n\n"
                    f"{alert_message}"
                ),
            )

        self.refresh()

    # =====================================================
    # LOGOUT
    # =====================================================

    def logout(self):

        self.on_logout()


# =========================================================
# BOOTH
# =========================================================

class BoothDashboard(BaseAdminDashboard):

    ROLE = "BOOTH"

    TITLE = "Booth Operations Dashboard"

    SUBTITLE = (
        "Local voter verification, voting activity, "
        "and booth integrity monitoring"
    )

    PERMISSION_TEXT = (
        "Booth-level operations and local monitoring"
    )

    def capabilities(self):

        return [
            "Voter verification",
            "Face verification",
            "Ballot access",
            "Vote recording",
            "Local ledger verification",
            "Booth activity monitoring",
        ]


# =========================================================
# ZONAL
# =========================================================

class ZonalDashboard(BaseAdminDashboard):

    ROLE = "ZONAL"

    TITLE = "Zonal Monitoring Dashboard"

    SUBTITLE = (
        "Supervise booth-level activity and review "
        "zonal security status"
    )

    PERMISSION_TEXT = (
        "Zonal-level monitoring and booth supervision"
    )

    def capabilities(self):

        return [
            "Monitor assigned booths",
            "Review booth activity",
            "Review voter statistics",
            "Verify ledger integrity",
            "Review booth security status",
            "Review synchronization status",
        ]


# =========================================================
# DEPUTY
# =========================================================

class DeputyDashboard(BaseAdminDashboard):

    ROLE = "DEPUTY"

    TITLE = "Deputy Oversight Dashboard"

    SUBTITLE = (
        "Cross-zone supervision and administrative "
        "integrity monitoring"
    )

    PERMISSION_TEXT = (
        "Deputy-level oversight across zonal operations"
    )

    def capabilities(self):

        return [
            "Monitor assigned zones",
            "Review zonal activity",
            "Review cross-zone statistics",
            "Verify ledger integrity",
            "Review security alerts",
            "Review synchronization status",
        ]


# =========================================================
# CENTRAL
# =========================================================

class CentralDashboard(BaseAdminDashboard):

    ROLE = "CENTRAL"

    TITLE = "Central Security Dashboard"

    SUBTITLE = (
        "Highest-security administrative layer for "
        "system-wide monitoring"
    )

    PERMISSION_TEXT = (
        "Central oversight, security monitoring, "
        "and global administrative control"
    )

    def _build_left_card(self):

        tk.Label(
            self.left_card,
            text="CENTRAL SECURITY STATUS",
            font=("Arial", 12, "bold"),
            fg=self.text,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4),
        )

        tk.Label(
            self.left_card,
            text=(
                "Central is the highest-security "
                "administrative level."
            ),
            font=("Arial", 9),
            fg=self.muted,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 14),
        )

        self.status_frame = tk.Frame(
            self.left_card,
            bg=self.white,
        )

        self.status_frame.pack(
            fill="both",
            expand=True,
            padx=15,
        )

        self._add_status_row(
            "Authentication",
            "PASSWORD + FACE + 2FA",
            self.green,
            "#ECFDF3",
            "auth",
        )

        self._add_status_row(
            "Role Access",
            "CENTRAL",
            self.primary,
            "#EAF2FF",
            "role",
        )

        self._add_status_row(
            "Ledger Integrity",
            "CHECKING...",
            self.orange,
            "#FFF7ED",
            "ledger",
        )

        self._add_status_row(
            "4-Level Sync",
            "CHECKING...",
            self.orange,
            "#FFF7ED",
            "sync",
        )

        self._add_status_row(
            "Security Alerts",
            "CHECKING...",
            self.orange,
            "#FFF7ED",
            "alerts",
        )

    def _build_right_card(self):

        tk.Label(
            self.right_card,
            text="CENTRAL SECURITY MONITOR",
            font=("Arial", 12, "bold"),
            fg=self.text,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(18, 4),
        )

        tk.Label(
            self.right_card,
            text=(
                "System-wide alerts visible to Central"
            ),
            font=("Arial", 9),
            fg=self.muted,
            bg=self.white,
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 10),
        )

        self.alert_frame = tk.Frame(
            self.right_card,
            bg=self.white,
        )

        self.alert_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 12),
        )

