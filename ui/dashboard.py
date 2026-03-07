"""Dashboard panel – summary statistics, revenue, monthly breakdown."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
import database as db
from styles import (
    BG_CARD, BG_PANEL, ACCENT, ACCENT2, SUCCESS, WARNING, DANGER,
    INFO, PURPLE, TEXT_PRIMARY, TEXT_SECONDARY, BG_HOVER
)

_MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
           "Jul","Aug","Sep","Oct","Nov","Dec"]


class StatCard(QFrame):
    def __init__(self, label: str, value: str, color: str = ACCENT,
                 icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 22))
        icon_lbl.setStyleSheet(f"color: {color}; background: transparent;")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"font-size: 30px; font-weight: bold; color: {color}; background: transparent;"
        )
        layout.addWidget(self.value_lbl)

        self.label_lbl = QLabel(label)
        self.label_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_SECONDARY}; background: transparent;"
        )
        layout.addWidget(self.label_lbl)

        self.setStyleSheet(
            f"QFrame#card {{ background-color: {BG_CARD}; border: 1px solid #2A2A4A; "
            f"border-radius: 12px; border-left: 4px solid {color}; }}"
        )

    def update_value(self, value: str):
        self.value_lbl.setText(value)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(60_000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("📊 Dashboard")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()
        from datetime import date
        date_lbl = QLabel(date.today().strftime("%A, %d %B %Y"))
        date_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;")
        header.addWidget(date_lbl)
        root.addLayout(header)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #2A2A4A;")
        root.addWidget(line)

        # ── Scroll content ────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(22)

        # ── Seats ─────────────────────────────────────────────────────────────
        vbox.addWidget(self._section_label("SEATS OVERVIEW"))
        seats_grid = QGridLayout()
        seats_grid.setSpacing(14)
        self.card_total     = StatCard("Total Seats",     "–", ACCENT,  "🪑")
        self.card_occupied  = StatCard("Occupied Seats",  "–", DANGER,  "🔴")
        self.card_available = StatCard("Available Seats", "–", SUCCESS, "🟢")
        self.card_reserved  = StatCard("Women Reserved",  "–", PURPLE,  "💜")
        seats_grid.addWidget(self.card_total,     0, 0)
        seats_grid.addWidget(self.card_occupied,  0, 1)
        seats_grid.addWidget(self.card_available, 0, 2)
        seats_grid.addWidget(self.card_reserved,  0, 3)
        vbox.addLayout(seats_grid)

        # ── Students ──────────────────────────────────────────────────────────
        vbox.addWidget(self._section_label("STUDENTS OVERVIEW"))
        stu_grid = QGridLayout()
        stu_grid.setSpacing(14)
        self.card_fulltime   = StatCard("Full-time",       "–", INFO,    "📚")
        self.card_halftime   = StatCard("Half-time",        "–", ACCENT2,"⏰")
        self.card_male       = StatCard("Male Students",    "–", BG_HOVER,"👨")
        self.card_female     = StatCard("Female Students",  "–", PURPLE,  "👩")
        stu_grid.addWidget(self.card_fulltime,  0, 0)
        stu_grid.addWidget(self.card_halftime,  0, 1)
        stu_grid.addWidget(self.card_male,      0, 2)
        stu_grid.addWidget(self.card_female,    0, 3)
        vbox.addLayout(stu_grid)

        # ── Payments ──────────────────────────────────────────────────────────
        vbox.addWidget(self._section_label("PAYMENT STATUS"))
        pay_grid = QGridLayout()
        pay_grid.setSpacing(14)
        self.card_due_today = StatCard("Fees Due Today",    "–", WARNING, "💰")
        self.card_overdue   = StatCard("Overdue Payments",  "–", DANGER,  "⚠️")
        self.card_rev_month = StatCard("Revenue This Month","₹–", SUCCESS, "📈")
        self.card_rev_year  = StatCard("Revenue This Year", "₹–", INFO,   "🗓️")
        pay_grid.addWidget(self.card_due_today,  0, 0)
        pay_grid.addWidget(self.card_overdue,    0, 1)
        pay_grid.addWidget(self.card_rev_month,  0, 2)
        pay_grid.addWidget(self.card_rev_year,   0, 3)
        vbox.addLayout(pay_grid)

        # ── Monthly Revenue Table ─────────────────────────────────────────────
        vbox.addWidget(self._section_label("MONTHLY REVENUE (THIS YEAR)"))
        self._rev_table = QTableWidget()
        self._rev_table.setColumnCount(3)
        self._rev_table.setHorizontalHeaderLabels(["Month", "Payments", "Revenue (₹)"])
        self._rev_table.verticalHeader().setVisible(False)
        self._rev_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._rev_table.setAlternatingRowColors(True)
        self._rev_table.setShowGrid(False)
        self._rev_table.setFixedHeight(240)
        self._rev_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._rev_table.setColumnWidth(1, 100)
        self._rev_table.setColumnWidth(2, 140)
        self._rev_table.setSelectionMode(QAbstractItemView.NoSelection)
        vbox.addWidget(self._rev_table)

        # ── Monthly Stats History ─────────────────────────────────────────────
        vbox.addWidget(self._section_label("STORED MONTHLY SNAPSHOTS"))
        self._snap_table = QTableWidget()
        self._snap_table.setColumnCount(8)
        self._snap_table.setHorizontalHeaderLabels([
            "Month", "Full-time", "Half-time", "Male", "Female", "Other",
            "Revenue (₹)", "Snapshot"
        ])
        self._snap_table.verticalHeader().setVisible(False)
        self._snap_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._snap_table.setAlternatingRowColors(True)
        self._snap_table.setShowGrid(False)
        self._snap_table.setFixedHeight(200)
        self._snap_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._snap_table.setSelectionMode(QAbstractItemView.NoSelection)
        vbox.addWidget(self._snap_table)

        vbox.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size: 11px; letter-spacing: 2px; color: {TEXT_SECONDARY}; "
            f"font-weight: bold; background: transparent;"
        )
        return lbl

    def _refresh(self):
        stats = db.get_dashboard_stats()
        self.card_total.update_value(str(stats["total_seats"]))
        self.card_occupied.update_value(str(stats["occupied_seats"]))
        self.card_available.update_value(str(stats["available_seats"]))
        self.card_reserved.update_value(str(stats["reserved_seats"]))
        self.card_fulltime.update_value(str(stats["fulltime_students"]))
        self.card_halftime.update_value(str(stats["halftime_students"]))
        self.card_male.update_value(str(stats.get("male_students", "–")))
        self.card_female.update_value(str(stats.get("female_students", "–")))
        self.card_due_today.update_value(str(stats["due_today"]))
        self.card_overdue.update_value(str(stats["overdue"]))
        self.card_rev_month.update_value(f"₹{stats.get('revenue_this_month', 0):,.0f}")
        self.card_rev_year.update_value(f"₹{stats.get('revenue_this_year', 0):,.0f}")
        self._load_revenue_table()
        self._load_snapshots_table()

    def _load_revenue_table(self):
        from datetime import date
        rows = db.get_revenue_by_month(date.today().year)
        self._rev_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            ym = row["ym"]  # e.g. "2026-03"
            try:
                parts = ym.split("-")
                month_name = _MONTHS[int(parts[1]) - 1] + " " + parts[0]
            except Exception:
                month_name = ym
            for c, text in enumerate([month_name, str(row["count"]), f"₹{row['total']:,.0f}"]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self._rev_table.setItem(r, c, item)
            self._rev_table.setRowHeight(r, 32)

    def _load_snapshots_table(self):
        snaps = db.get_monthly_stats_history(12)
        self._snap_table.setRowCount(len(snaps))
        for r, s in enumerate(snaps):
            month_name = _MONTHS[s["month"] - 1] + f" {s['year']}"
            for c, text in enumerate([
                month_name,
                str(s["fulltime_count"]), str(s["halftime_count"]),
                str(s["male_count"]), str(s["female_count"]), str(s["other_count"]),
                f"₹{s['revenue_collected']:,.0f}",
                s.get("snapshot_date", "")[:10],
            ]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self._snap_table.setItem(r, c, item)
            self._snap_table.setRowHeight(r, 32)

    def refresh(self):
        self._refresh()
