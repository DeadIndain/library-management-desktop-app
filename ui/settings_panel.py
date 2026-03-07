"""Admin settings / personalization panel."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFrame, QFormLayout, QGroupBox,
    QScrollArea, QMessageBox, QSpinBox, QDoubleSpinBox,
    QTimeEdit, QDialog, QFileDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QTime, pyqtSignal
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, SUCCESS, DANGER,
    WARNING, BG_CARD, BG_PANEL, BG_DARK
)
import os


class SettingsWidget(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚙️ Admin Settings")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        save_btn = QPushButton("💾 Save All Settings")
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self._save_settings)
        header.addWidget(save_btn)
        root.addLayout(header)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(content)
        vbox.setSpacing(20)
        vbox.setContentsMargins(0, 0, 12, 0)

        # ── Fee & Seats ──────────────────────────────────────────
        group1 = QGroupBox("Fees & Seats Configuration")
        form1 = QFormLayout(group1)
        form1.setSpacing(12)

        self._monthly_fee = QDoubleSpinBox()
        self._monthly_fee.setRange(0, 100000)
        self._monthly_fee.setPrefix("₹ ")
        self._monthly_fee.setDecimals(0)
        form1.addRow("Monthly Fee (default)", self._monthly_fee)

        self._fulltime_fee = QDoubleSpinBox()
        self._fulltime_fee.setRange(0, 100000)
        self._fulltime_fee.setPrefix("₹ ")
        self._fulltime_fee.setDecimals(0)
        form1.addRow("Full-time Monthly Fee", self._fulltime_fee)

        self._halftime_fee = QDoubleSpinBox()
        self._halftime_fee.setRange(0, 100000)
        self._halftime_fee.setPrefix("₹ ")
        self._halftime_fee.setDecimals(0)
        form1.addRow("Half-time Monthly Fee", self._halftime_fee)

        self._total_seats = QSpinBox()
        self._total_seats.setRange(1, 500)
        form1.addRow("Total Seats", self._total_seats)

        self._women_seats = QSpinBox()
        self._women_seats.setRange(0, 500)
        form1.addRow("Women Reserved Seats (first N seats)", self._women_seats)

        vbox.addWidget(group1)

        # ── Timings ──────────────────────────────────────────────
        group2 = QGroupBox("Opening Hours & Shift Timings")
        form2 = QFormLayout(group2)
        form2.setSpacing(12)

        self._open_time = QTimeEdit()
        self._open_time.setDisplayFormat("HH:mm")
        form2.addRow("Opening Time", self._open_time)

        self._close_time = QTimeEdit()
        self._close_time.setDisplayFormat("HH:mm")
        form2.addRow("Closing Time", self._close_time)

        self._morning_start = QTimeEdit()
        self._morning_start.setDisplayFormat("HH:mm")
        form2.addRow("Morning Shift Start", self._morning_start)

        self._morning_end = QTimeEdit()
        self._morning_end.setDisplayFormat("HH:mm")
        form2.addRow("Morning Shift End", self._morning_end)

        self._evening_start = QTimeEdit()
        self._evening_start.setDisplayFormat("HH:mm")
        form2.addRow("Evening Shift Start", self._evening_start)

        self._evening_end = QTimeEdit()
        self._evening_end.setDisplayFormat("HH:mm")
        form2.addRow("Evening Shift End", self._evening_end)

        vbox.addWidget(group2)

        # ── WhatsApp Messages ─────────────────────────────────────
        group3 = QGroupBox("WhatsApp Reminder Message  (use {name} as placeholder)")
        layout3 = QVBoxLayout(group3)
        self._reminder_msg = QTextEdit()
        self._reminder_msg.setMinimumHeight(140)
        self._reminder_msg.setPlaceholderText("Use {name} for student name…")
        layout3.addWidget(self._reminder_msg)
        vbox.addWidget(group3)

        group3b = QGroupBox("WhatsApp 3-Day Advance Reminder  (use {name}, {due_date})")
        layout3b = QVBoxLayout(group3b)
        self._enable_3day = QCheckBox("Enable 3-day advance reminder")
        layout3b.addWidget(self._enable_3day)
        self._reminder_3day_msg = QTextEdit()
        self._reminder_3day_msg.setMinimumHeight(110)
        self._reminder_3day_msg.setPlaceholderText(
            "Hi {name}, your payment is due in 3 days on {due_date}. Please keep it ready."
        )
        layout3b.addWidget(self._reminder_3day_msg)
        vbox.addWidget(group3b)

        group3c = QGroupBox("WhatsApp 1-Day Advance Reminder  (use {name}, {due_date})")
        layout3c = QVBoxLayout(group3c)
        self._enable_1day = QCheckBox("Enable 1-day advance reminder")
        layout3c.addWidget(self._enable_1day)
        self._reminder_1day_msg = QTextEdit()
        self._reminder_1day_msg.setMinimumHeight(110)
        self._reminder_1day_msg.setPlaceholderText(
            "Hi {name}, your payment is due tomorrow on {due_date}. Please arrange payment."
        )
        layout3c.addWidget(self._reminder_1day_msg)
        vbox.addWidget(group3c)

        group4 = QGroupBox("WhatsApp Removal Message  (use {name} as placeholder)")
        layout4 = QVBoxLayout(group4)
        self._removal_msg = QTextEdit()
        self._removal_msg.setMinimumHeight(100)
        self._removal_msg.setPlaceholderText("Use {name} for student name…")
        layout4.addWidget(self._removal_msg)
        vbox.addWidget(group4)

        # ── Backup & Export ───────────────────────────────────────
        group5 = QGroupBox("Data Backup & Export")
        layout5 = QVBoxLayout(group5)
        layout5.setSpacing(10)

        backup_row = QHBoxLayout()
        backup_lbl = QLabel("Create a backup copy of the database:")
        backup_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        backup_row.addWidget(backup_lbl)
        backup_row.addStretch()
        backup_btn = QPushButton("🗄️ Backup Database")
        backup_btn.setObjectName("btn_primary")
        backup_btn.clicked.connect(self._backup_db)
        backup_row.addWidget(backup_btn)
        layout5.addLayout(backup_row)

        export_row = QHBoxLayout()
        export_lbl = QLabel("Export all student data to Excel / CSV:")
        export_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        export_row.addWidget(export_lbl)
        export_row.addStretch()
        export_excel_btn = QPushButton("📊 Export Excel")
        export_excel_btn.setObjectName("btn_success")
        export_excel_btn.clicked.connect(lambda: self._export("xlsx"))
        export_csv_btn = QPushButton("📄 Export CSV")
        export_csv_btn.clicked.connect(lambda: self._export("csv"))
        export_row.addWidget(export_excel_btn)
        export_row.addWidget(export_csv_btn)
        layout5.addLayout(export_row)

        vbox.addWidget(group5)

        # ── About ─────────────────────────────────────────────────
        group6 = QGroupBox("About")
        layout6 = QVBoxLayout(group6)
        about_lbl = QLabel(
            "<b>Study Point Library Management System</b><br>"
            "Version 1.0 &nbsp;|&nbsp; Built with Python + PyQt5<br>"
            "Database: SQLite  &nbsp;|&nbsp; "
            "WhatsApp: pywhatkit"
        )
        about_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent; line-height: 1.6;")
        about_lbl.setTextFormat(Qt.RichText)
        layout6.addWidget(about_lbl)
        vbox.addWidget(group6)

        vbox.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _load_settings(self):
        s = db.get_all_settings()

        def _t(key, default="00:00") -> QTime:
            val = s.get(key, default)
            try:
                h, m = map(int, val.split(":"))
                return QTime(h, m)
            except Exception:
                return QTime(0, 0)

        self._monthly_fee.setValue(float(s.get("monthly_fee", "500")))
        self._fulltime_fee.setValue(float(s.get("fulltime_fee", "600")))
        self._halftime_fee.setValue(float(s.get("halftime_fee", "400")))
        self._total_seats.setValue(int(s.get("total_seats", "69")))
        self._women_seats.setValue(int(s.get("women_reserved_seats", "10")))
        self._open_time.setTime(_t("opening_time", "06:00"))
        self._close_time.setTime(_t("closing_time", "23:00"))
        self._morning_start.setTime(_t("morning_shift_start", "06:00"))
        self._morning_end.setTime(_t("morning_shift_end", "14:00"))
        self._evening_start.setTime(_t("evening_shift_start", "14:00"))
        self._evening_end.setTime(_t("evening_shift_end", "23:00"))
        self._reminder_msg.setPlainText(s.get("whatsapp_reminder_message", ""))
        self._removal_msg.setPlainText(s.get("whatsapp_removal_message", ""))
        self._enable_3day.setChecked(s.get("enable_reminder_3day", "1") == "1")
        self._enable_1day.setChecked(s.get("enable_reminder_1day", "1") == "1")
        self._reminder_3day_msg.setPlainText(s.get("whatsapp_reminder_3day_message", ""))
        self._reminder_1day_msg.setPlainText(s.get("whatsapp_reminder_1day_message", ""))

    def _save_settings(self):
        def _ts(t: QTime) -> str:
            return t.toString("HH:mm")

        settings_map = {
            "monthly_fee": str(int(self._monthly_fee.value())),
            "fulltime_fee": str(int(self._fulltime_fee.value())),
            "halftime_fee": str(int(self._halftime_fee.value())),
            "total_seats": str(self._total_seats.value()),
            "women_reserved_seats": str(self._women_seats.value()),
            "opening_time": _ts(self._open_time.time()),
            "closing_time": _ts(self._close_time.time()),
            "morning_shift_start": _ts(self._morning_start.time()),
            "morning_shift_end": _ts(self._morning_end.time()),
            "evening_shift_start": _ts(self._evening_start.time()),
            "evening_shift_end": _ts(self._evening_end.time()),
            "whatsapp_reminder_message": self._reminder_msg.toPlainText(),
            "whatsapp_removal_message":  self._removal_msg.toPlainText(),
            "enable_reminder_3day":      "1" if self._enable_3day.isChecked() else "0",
            "enable_reminder_1day":      "1" if self._enable_1day.isChecked() else "0",
            "whatsapp_reminder_3day_message": self._reminder_3day_msg.toPlainText(),
            "whatsapp_reminder_1day_message": self._reminder_1day_msg.toPlainText(),
        }
        for key, value in settings_map.items():
            db.set_setting(key, value)

        QMessageBox.information(
            self, "Settings Saved",
            "✅ All settings have been saved successfully.\n"
            "Seat layout and seat counts will update automatically."
        )
        self.settings_changed.emit()

    def _backup_db(self):
        backup_dir = QFileDialog.getExistingDirectory(
            self, "Select Backup Location",
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        if backup_dir:
            try:
                from utils.export import backup_database
                from database import DB_PATH
                path = backup_database(DB_PATH, backup_dir)
                QMessageBox.information(
                    self, "Backup Created",
                    f"✅ Database backup saved to:\n{path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Backup Failed", str(e))

    def _export(self, fmt: str):
        ext = "Excel Files (*.xlsx)" if fmt == "xlsx" else "CSV Files (*.csv)"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Students Data",
            os.path.join(os.path.expanduser("~"), f"students_export.{fmt}"),
            ext
        )
        if not path:
            return
        try:
            data = db.export_students_data()
            if fmt == "xlsx":
                from utils.export import export_to_excel
                export_to_excel(data, path)
            else:
                from utils.export import export_to_csv
                export_to_csv(data, path)
            QMessageBox.information(
                self, "Export Successful",
                f"✅ Data exported to:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", str(e))
