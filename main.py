"""
Study Point Library Management System
Main application entry point.
"""
import sys
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QLabel, QPushButton, QFrame,
    QStackedWidget, QSizePolicy, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QColor

import database as db
from styles import APP_STYLESHEET, ACCENT, BG_PANEL, TEXT_PRIMARY, TEXT_SECONDARY, DANGER, WARNING, BG_DARK

from ui.dashboard import DashboardWidget
from ui.seat_layout import SeatLayoutWidget
from ui.student_management import StudentManagementWidget
from ui.payment_management import PaymentManagementWidget
from ui.overdue_payments import OverduePaymentsWidget
from ui.removed_students import RemovedStudentsWidget
from ui.settings_panel import SettingsWidget


NAV_ITEMS = [
    ("📊", "Dashboard",         "dashboard"),
    ("🪑", "Seat Layout",       "seats"),
    ("👥", "Students",          "students"),
    ("💳", "Payments",          "payments"),
    ("⚠️", "Overdue Fees",      "overdue"),
    ("🗂️", "Removed Students",  "removed"),
    ("⚙️", "Settings",          "settings"),
]


class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon}  {label}")
        self.setObjectName("nav_btn")
        self.setCheckable(True)
        self.setFlat(True)
        self.setMinimumHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 13))

    def set_active(self, active: bool):
        self.setObjectName("nav_btn_active" if active else "nav_btn")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(0)

        # Logo / App Title
        logo_frame = QFrame()
        logo_frame.setFixedHeight(72)
        logo_frame.setStyleSheet(f"background: transparent; border-bottom: 1px solid #2A2A4A;")
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(10, 10, 10, 10)

        app_name = QLabel("📚 Study Point")
        app_name.setObjectName("app_title")
        app_name.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {ACCENT}; background: transparent;"
        )
        app_name.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(app_name)

        sub = QLabel("Library Management")
        sub.setStyleSheet(
            f"font-size: 10px; color: {TEXT_SECONDARY}; background: transparent; letter-spacing: 1px;"
        )
        sub.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(sub)

        layout.addWidget(logo_frame)
        layout.addSpacing(10)

        self._nav_buttons = {}
        for icon, label, key in NAV_ITEMS:
            btn = NavButton(icon, label)
            layout.addWidget(btn)
            layout.addSpacing(2)
            self._nav_buttons[key] = btn

        layout.addStretch()

        # Date / time footer
        self._clock = QLabel()
        self._clock.setAlignment(Qt.AlignCenter)
        self._clock.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; background: transparent; padding: 8px;"
        )
        layout.addWidget(self._clock)
        self._update_clock()

        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(30_000)

    def _update_clock(self):
        from datetime import datetime
        now = datetime.now()
        self._clock.setText(now.strftime("%a, %d %b %Y\n%I:%M %p"))

    def get_button(self, key: str) -> NavButton:
        return self._nav_buttons.get(key)

    def set_active(self, active_key: str):
        for key, btn in self._nav_buttons.items():
            btn.set_active(key == active_key)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Point – Library Management System")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        self._build_ui()
        self._navigate("dashboard")
        self._start_daily_reminders()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        main_layout.addWidget(self._sidebar)

        # Stack
        self._stack = QStackedWidget()
        main_layout.addWidget(self._stack)

        # Create all panels
        self._panels = {}

        dash = DashboardWidget()
        self._panels["dashboard"] = dash
        self._stack.addWidget(dash)

        seats = SeatLayoutWidget()
        seats.seat_updated.connect(self._on_data_changed)
        self._panels["seats"] = seats
        self._stack.addWidget(seats)

        students = StudentManagementWidget()
        students.data_changed.connect(self._on_data_changed)
        self._panels["students"] = students
        self._stack.addWidget(students)

        payments = PaymentManagementWidget()
        payments.data_changed.connect(self._on_data_changed)
        self._panels["payments"] = payments
        self._stack.addWidget(payments)

        overdue = OverduePaymentsWidget()
        overdue.data_changed.connect(self._on_data_changed)
        self._panels["overdue"] = overdue
        self._stack.addWidget(overdue)

        removed = RemovedStudentsWidget()
        self._panels["removed"] = removed
        self._stack.addWidget(removed)

        settings = SettingsWidget()
        settings.settings_changed.connect(self._on_settings_changed)
        self._panels["settings"] = settings
        self._stack.addWidget(settings)

        # Connect nav buttons
        for icon, label, key in NAV_ITEMS:
            btn = self._sidebar.get_button(key)
            if btn:
                btn.clicked.connect(lambda _, k=key: self._navigate(k))

    def _navigate(self, key: str):
        panel = self._panels.get(key)
        if panel:
            self._stack.setCurrentWidget(panel)
            self._sidebar.set_active(key)
            # Refresh panels when navigated to
            if hasattr(panel, "refresh"):
                panel.refresh()

    def _on_data_changed(self):
        """Refresh dashboard and overdue whenever data changes."""
        if "dashboard" in self._panels:
            self._panels["dashboard"].refresh()
        if "overdue" in self._panels:
            self._panels["overdue"].refresh()

    def _on_settings_changed(self):
        """Reload seat layout after settings change."""
        self._on_data_changed()
        if "seats" in self._panels:
            self._panels["seats"].refresh()

    def _start_daily_reminders(self):
        """Check for due payments at launch and every hour."""
        self._check_due_reminders()
        self._reminder_timer = QTimer(self)
        self._reminder_timer.timeout.connect(self._check_due_reminders)
        self._reminder_timer.start(3_600_000)  # every hour

    def _check_due_reminders(self):
        """Auto-send WhatsApp reminders: due-today, 3-day advance, 1-day advance."""
        try:
            from utils.whatsapp import (
                send_message, format_reminder_message,
                format_3day_message, format_1day_message
            )

            # ── Due today ────────────────────────────────────────────────────
            tmpl = db.get_setting("whatsapp_reminder_message") or ""
            for s in db.get_due_today_students():
                msg = format_reminder_message(tmpl, s["name"], s.get("next_payment_date") or "")
                send_message(s["phone"], msg, async_send=True)

            # ── 3-day advance ────────────────────────────────────────────────
            if db.get_setting("enable_reminder_3day") == "1":
                tmpl3 = db.get_setting("whatsapp_reminder_3day_message") or ""
                for s in db.get_students_due_in_days(3):
                    msg = format_3day_message(tmpl3, s["name"], s.get("next_payment_date") or "")
                    send_message(s["phone"], msg, async_send=True)

            # ── 1-day advance ────────────────────────────────────────────────
            if db.get_setting("enable_reminder_1day") == "1":
                tmpl1 = db.get_setting("whatsapp_reminder_1day_message") or ""
                for s in db.get_students_due_in_days(1):
                    msg = format_1day_message(tmpl1, s["name"], s.get("next_payment_date") or "")
                    send_message(s["phone"], msg, async_send=True)

        except Exception as e:
            print(f"[Reminder] Error sending reminders: {e}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Study Point LMS")
    app.setApplicationVersion("1.0")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLESHEET)

    # Initialize database
    db.init_db()
    db.store_monthly_snapshot()  # update monthly stats on every launch

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
