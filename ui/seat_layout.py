"""Visual seat grid with color-coding, filters, and assignment actions."""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QMessageBox, QDialog,
    QComboBox, QSizePolicy, QButtonGroup
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QFont, QCursor
import database as db
from styles import (
    SEAT_AVAILABLE, SEAT_OCCUPIED, SEAT_WOMEN, SEAT_SELECTED,
    TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD, BG_PANEL, BG_HOVER,
    ACCENT, SUCCESS, DANGER, PURPLE, WARNING
)

# Filter constants
FILTER_ALL       = "all"
FILTER_AVAILABLE = "available"
FILTER_OCCUPIED  = "occupied"
FILTER_WOMEN     = "women"


class SeatButton(QPushButton):
    clicked_with_info = pyqtSignal(dict)

    def __init__(self, seat_info: dict, parent=None):
        super().__init__(parent)
        self.seat_info = seat_info
        self.setFixedSize(56, 56)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._update_style()
        self.clicked.connect(lambda: self.clicked_with_info.emit(self.seat_info))

    def _update_style(self):
        sn = self.seat_info["seat_number"]
        occupied = self.seat_info["student_id"] is not None
        reserved = self.seat_info["is_reserved_women"]

        if occupied:
            bg, border = SEAT_OCCUPIED, "#A93226"
        elif reserved:
            bg, border = SEAT_WOMEN, "#6C3483"
        else:
            bg, border = SEAT_AVAILABLE, "#1E8449"

        self.setText(str(sn))
        name = self.seat_info.get("student_name") or ""
        tooltip = f"Seat {sn}"
        if occupied:
            tooltip += f"\n👤 {name}\n📚 {self.seat_info.get('student_type','')}"
        elif reserved:
            tooltip += "\n💜 Reserved for Women"
        else:
            tooltip += "\n✅ Available"
        self.setToolTip(tooltip)

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid {border};
                border-radius: 8px;
            }}
            QPushButton:hover {{
                border: 2px solid white;
            }}
        """)

    def update_info(self, seat_info: dict):
        self.seat_info = seat_info
        self._update_style()


class SeatLayoutWidget(QWidget):
    seat_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._seat_buttons = {}
        self._all_seats = []
        self._current_filter = FILTER_ALL
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        # ── Header ─────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("🪑 Seat Layout")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        # stat chips
        self._stat_chip = QLabel()
        self._stat_chip.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        header.addWidget(self._stat_chip)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setObjectName("btn_primary")
        refresh_btn.setFixedWidth(100)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        # ── Legend + Filter bar ───────────────────────────────────────────────
        legend_filter = QHBoxLayout()
        legend_filter.setSpacing(16)

        for color, label in [
            (SEAT_AVAILABLE, "Available"),
            (SEAT_OCCUPIED,  "Occupied"),
            (SEAT_WOMEN,     "Women Reserved"),
        ]:
            dot = QFrame()
            dot.setFixedSize(12, 12)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;")
            legend_filter.addWidget(dot)
            legend_filter.addWidget(lbl)

        legend_filter.addStretch()

        # Filter toggle buttons
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        legend_filter.addWidget(filter_label)

        self._filter_btns = {}
        for key, label in [
            (FILTER_ALL,       "All"),
            (FILTER_AVAILABLE, "Available"),
            (FILTER_OCCUPIED,  "Occupied"),
            (FILTER_WOMEN,     "Women"),
        ]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedSize(86, 30)
            btn.clicked.connect(lambda _, k=key: self._apply_filter(k))
            self._filter_btns[key] = btn
            legend_filter.addWidget(btn)

        self._filter_btns[FILTER_ALL].setChecked(True)
        self._update_filter_btn_styles()
        root.addLayout(legend_filter)

        # ── Grid scroll area ─────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._grid_container = QWidget()
        self._grid_container.setStyleSheet("background: transparent;")
        self._grid_layout = QGridLayout(self._grid_container)
        self._grid_layout.setSpacing(8)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)

        scroll.setWidget(self._grid_container)
        root.addWidget(scroll)

        # ── Action panel ──────────────────────────────────────────────────────
        action_frame = QFrame()
        action_frame.setObjectName("card")
        action_frame.setFixedHeight(70)
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(16, 10, 16, 10)

        self._selected_lbl = QLabel("Click a seat to select it")
        self._selected_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent;"
        )
        action_layout.addWidget(self._selected_lbl)
        action_layout.addStretch()

        self._assign_btn = QPushButton("📌 Assign Student")
        self._assign_btn.setObjectName("btn_success")
        self._assign_btn.setEnabled(False)
        self._assign_btn.clicked.connect(self._assign_seat)
        action_layout.addWidget(self._assign_btn)

        self._free_btn = QPushButton("🔓 Free Seat")
        self._free_btn.setObjectName("btn_danger")
        self._free_btn.setEnabled(False)
        self._free_btn.clicked.connect(self._free_seat)
        action_layout.addWidget(self._free_btn)

        root.addWidget(action_frame)

        self._selected_seat = None

    def _update_filter_btn_styles(self):
        for key, btn in self._filter_btns.items():
            if btn.isChecked():
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {ACCENT}; color: white; "
                    f"border-radius: 6px; border: none; font-weight: bold; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {BG_HOVER}; color: {TEXT_SECONDARY}; "
                    f"border-radius: 6px; border: none; }}"
                    f"QPushButton:hover {{ background-color: {ACCENT}; color: white; }}"
                )

    def _apply_filter(self, key: str):
        self._current_filter = key
        for k, btn in self._filter_btns.items():
            btn.setChecked(k == key)
        self._update_filter_btn_styles()
        self._render_grid()

    def refresh(self):
        self._all_seats = db.get_all_seats()
        self._render_grid()
        self._update_stat_chip()
        self._selected_seat = None
        self._selected_lbl.setText("Click a seat to select it")
        self._assign_btn.setEnabled(False)
        self._free_btn.setEnabled(False)

    def _filtered_seats(self):
        f = self._current_filter
        if f == FILTER_AVAILABLE:
            return [s for s in self._all_seats if s["student_id"] is None]
        if f == FILTER_OCCUPIED:
            return [s for s in self._all_seats if s["student_id"] is not None]
        if f == FILTER_WOMEN:
            return [s for s in self._all_seats if s["is_reserved_women"]]
        return self._all_seats

    def _render_grid(self):
        for i in reversed(range(self._grid_layout.count())):
            w = self._grid_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self._seat_buttons.clear()

        seats = self._filtered_seats()
        cols = 10
        for idx, seat in enumerate(seats):
            row = idx // cols
            col = idx % cols
            btn = SeatButton(seat)
            btn.clicked_with_info.connect(self._on_seat_clicked)
            self._grid_layout.addWidget(btn, row, col)
            self._seat_buttons[seat["seat_number"]] = btn

    def _update_stat_chip(self):
        total     = len(self._all_seats)
        occupied  = sum(1 for s in self._all_seats if s["student_id"] is not None)
        available = total - occupied
        women     = sum(1 for s in self._all_seats if s["is_reserved_women"])
        self._stat_chip.setText(
            f"Total: {total}  |  Occupied: {occupied}  |  "
            f"Available: {available}  |  Women: {women}"
        )

    def _on_seat_clicked(self, seat_info: dict):
        self._selected_seat = seat_info
        sn = seat_info["seat_number"]
        occupied = seat_info["student_id"] is not None
        name = seat_info.get("student_name") or ""

        if occupied:
            self._selected_lbl.setText(
                f"Selected: Seat {sn}  |  👤 {name} ({seat_info.get('student_type','')})"
            )
            self._assign_btn.setEnabled(False)
            self._free_btn.setEnabled(True)
        else:
            reserved_txt = " (Women Reserved)" if seat_info["is_reserved_women"] else ""
            self._selected_lbl.setText(
                f"Selected: Seat {sn}{reserved_txt}  |  ✅ Available"
            )
            self._assign_btn.setEnabled(True)
            self._free_btn.setEnabled(False)

    def _assign_seat(self):
        if not self._selected_seat:
            return
        sn = self._selected_seat["seat_number"]

        # Conflict protection: re-check in real time
        if db.is_seat_taken(sn):
            QMessageBox.warning(
                self, "Seat Conflict",
                f"Seat {sn} is already occupied.\nPlease refresh and try again."
            )
            self.refresh()
            return

        students = db.get_all_students()
        candidates = [
            s for s in students
            if s["student_type"] == "Full-time" and (
                s["seat_number"] is None or s["seat_number"] == sn
            )
        ]
        if not candidates:
            QMessageBox.information(
                self, "No Students",
                "No full-time students without a seat assignment found.\n"
                "Add a full-time student first."
            )
            return

        dlg = AssignSeatDialog(sn, candidates, self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_id:
            # Final conflict check before writing
            if db.is_seat_taken(sn, exclude_student_id=dlg.selected_id):
                QMessageBox.warning(
                    self, "Seat Conflict",
                    f"Seat {sn} was just taken by someone else. Please select another seat."
                )
                self.refresh()
                return
            db.assign_seat(sn, dlg.selected_id)
            self.refresh()
            self.seat_updated.emit()

    def _free_seat(self):
        if not self._selected_seat or self._selected_seat["student_id"] is None:
            return
        sn = self._selected_seat["seat_number"]
        name = self._selected_seat.get("student_name", "")
        reply = QMessageBox.question(
            self, "Free Seat",
            f"Free seat {sn} currently occupied by {name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.free_seat(sn)
            from database import get_connection
            conn = get_connection()
            conn.execute(
                "UPDATE students SET seat_number = NULL WHERE seat_number = ?", (sn,)
            )
            conn.commit()
            conn.close()
            self.refresh()
            self.seat_updated.emit()


class AssignSeatDialog(QDialog):
    def __init__(self, seat_number: int, students: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Assign Seat {seat_number}")
        self.setMinimumWidth(380)
        self.selected_id = None

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(f"Select student for Seat {seat_number}:"))

        self._combo = QComboBox()
        for s in students:
            code = s.get("student_code") or ""
            self._combo.addItem(f"[{code}]  {s['name']}  ({s['phone']})", s["id"])
        layout.addWidget(self._combo)

        btn_row = QHBoxLayout()
        confirm = QPushButton("Assign")
        confirm.setObjectName("btn_success")
        confirm.clicked.connect(self._confirm)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(confirm)
        btn_row.addWidget(cancel)
        layout.addLayout(btn_row)

    def _confirm(self):
        self.selected_id = self._combo.currentData()
        self.accept()

