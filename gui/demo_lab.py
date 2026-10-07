import csv
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox

from config import LEVEL_DATABASE_PATHS
from database import get_admin_audit_logs, reset_demo_voters
from services.four_level_sync import (
    establish_initial_trust,
    get_four_level_security_summary,
)
from services.level_database import initialize_all_level_databases
from services.backup_service import create_database_backup


class DemoLab:

    """Safe, visible controls for demonstrating VeriVote security behavior."""

    def __init__(self, parent, on_changed=None):

        self.parent = parent
        self.on_changed = on_changed
        self.window = tk.Toplevel(parent)
        self.window.title("VeriVote Demo Lab")
        self.window.geometry("620x700")
        self.window.minsize(620, 700)
        self.window.configure(bg="#F4F7FB")
        self._build()

    def _build(self):

        tk.Label(
            self.window,
            text="VERIVOTE DEMO LAB",
            font=("Arial", 20, "bold"),
            fg="#172B4D",
            bg="#F4F7FB",
        ).pack(pady=(24, 4))

        tk.Label(
            self.window,
            text="Demonstrate detection, evidence, and recovery controls",
            font=("Arial", 10),
            fg="#667085",
            bg="#F4F7FB",
        ).pack(pady=(0, 18))

        card = tk.Frame(
            self.window,
            bg="white",
            highlightbackground="#D9E2EC",
            highlightthickness=1,
        )
        card.pack(fill="x", padx=36)

        self._button(card, "RUN INTEGRITY VERIFICATION", self.verify)
        self._button(card, "RUN FULL SECURITY DEMO", self.run_full_demo)
        self._button(card, "SIMULATE BOOTH TAMPER", self.simulate_tamper)
        self._button(card, "EXPORT ADMIN AUDIT CSV", self.export_audit)
        self._button(card, "VIEW AUDIT LOG", self.view_audit)
        self._button(card, "BACK UP DATABASES", self.backup_databases)
        self._button(card, "RESET DEMO ELECTION", self.reset_demo)

        self.status = tk.Label(
            self.window,
            text="Ready for a controlled demonstration.",
            font=("Arial", 10, "bold"),
            fg="#1557A6",
            bg="#EAF2FF",
            padx=18,
            pady=14,
        )
        self.status.pack(fill="x", padx=36, pady=22)

    def _button(self, parent, label, command):

        tk.Button(
            parent,
            text=label,
            command=command,
            bg="#1557A6",
            fg="white",
            activebackground="#0D3F7A",
            activeforeground="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=10,
        ).pack(fill="x", padx=22, pady=8)

    def verify(self):

        summary = get_four_level_security_summary()
        overall = summary.get("overall", "UNKNOWN")
        alerts = sum(
            len(items)
            for items in summary.get("alerts", {}).values()
        )
        self.status.config(
            text=f"Integrity result: {overall} | {alerts} alert(s) detected.",
            fg="#B42318" if alerts else "#15803D",
            bg="#FEF3F2" if alerts else "#ECFDF3",
        )

        if self.on_changed:
            self.on_changed()

    def run_full_demo(self):

        """Run the complete local attack-detection presentation flow."""

        self.simulate_tamper()
        self.verify()
        messagebox.showinfo(
            "Full Security Demo",
            "Security walkthrough complete.\n\n"
            "1. Booth tamper injected\n"
            "2. Integrity verification executed\n"
            "3. Central alert displayed\n\n"
            "Use RESET DEMO ELECTION to restore the clean state.",
            parent=self.window,
        )

    def simulate_tamper(self):

        initialize_all_level_databases()
        path = LEVEL_DATABASE_PATHS["BOOTH"]

        connection = sqlite3.connect(path)
        try:
            row = connection.execute(
                "SELECT vote_id FROM votes ORDER BY vote_id DESC LIMIT 1"
            ).fetchone()

            if row:
                connection.execute(
                    "UPDATE votes SET vote_hash = ? WHERE vote_id = ?",
                    ("DEMO-TAMPERED-HASH", row[0]),
                )
            else:
                connection.execute(
                    "UPDATE level_checkpoint SET ledger_hash = ? WHERE id = 1",
                    ("DEMO-TAMPERED-HASH",),
                )

            connection.commit()
        finally:
            connection.close()

        self.status.config(
            text="Booth tamper injected. Run integrity verification to expose it.",
            fg="#B42318",
            bg="#FEF3F2",
        )

        if self.on_changed:
            self.on_changed()

    def export_audit(self):

        destination = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export administrator audit log",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not destination:
            return

        rows = get_admin_audit_logs(limit=1000)

        with open(destination, "w", newline="", encoding="utf-8") as output:
            writer = csv.writer(output)
            writer.writerow([
                "audit_id", "username", "role", "action",
                "details", "status", "timestamp",
            ])
            writer.writerows(rows)

        messagebox.showinfo(
            "Audit Export Complete",
            f"Exported {len(rows)} audit record(s).",
            parent=self.window,
        )

    def reset_demo(self):

        confirmed = messagebox.askyesno(
            "Reset Demo Election",
            "This clears demo votes, alerts, and checkpoints. Continue?",
            parent=self.window,
        )

        if not confirmed:
            return

        reset_demo_voters()

        for path in LEVEL_DATABASE_PATHS.values():
            connection = sqlite3.connect(path)
            try:
                connection.execute("DELETE FROM votes")
                connection.execute("DELETE FROM security_events")
                connection.execute("DELETE FROM peer_checkpoints")
                connection.commit()
            finally:
                connection.close()

        establish_initial_trust()
        self.status.config(
            text="Demo election reset. All four levels are trusted at GENESIS.",
            fg="#15803D",
            bg="#ECFDF3",
        )

        if self.on_changed:
            self.on_changed()

    def view_audit(self):

        window = tk.Toplevel(self.window)
        window.title("Administrator Audit Explorer")
        window.geometry("900x430")
        window.configure(bg="#F4F7FB")

        tk.Label(
            window,
            text="ADMINISTRATOR AUDIT EXPLORER",
            font=("Arial", 16, "bold"),
            fg="#172B4D",
            bg="#F4F7FB",
        ).pack(anchor="w", padx=20, pady=(18, 8))

        text = tk.Text(
            window,
            font=("Consolas", 9),
            bg="white",
            fg="#172B4D",
            wrap="none",
        )
        text.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        text.insert(
            "end",
            "ID | USERNAME | ROLE | ACTION | STATUS | TIMESTAMP\n"
            + "-" * 110
            + "\n",
        )

        for row in get_admin_audit_logs(limit=1000):
            audit_id, username, role, action, details, status, timestamp = row
            text.insert(
                "end",
                f"{audit_id} | {username} | {role} | {action} | "
                f"{status} | {timestamp}\n{details}\n",
            )

        text.config(state="disabled")

    def backup_databases(self):

        destination = filedialog.askdirectory(
            parent=self.window,
            title="Choose backup folder",
        )
        if not destination:
            return

        created = create_database_backup(destination)
        messagebox.showinfo(
            "Backup Complete",
            f"Created {len(created)} consistent database backup(s).",
            parent=self.window,
        )
