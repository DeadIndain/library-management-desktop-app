"""Student management: full list, quick-add, edit, remove, search."""
from datetime import date, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QTextEdit, QDateEdit, QMessageBox,
    QHeaderView, QAbstractItemView, QFrame, QSplitter,
    QScrollArea, QGroupBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD, BG_PANEL, ACCENT,
    SUCCESS, DANGER, WARNING, INFO, PURPLE, BG_HOVER, BG_DARK
)

STATUS_COLORS = {
    "paid":      "#27AE60",
    "due_soon":  "#F39C12",
    "due_today": "#E67E22",
    "overdue":   "#E74C3C",
}
STATUS_LABELS = {
    "paid":      "Paid",
    "due_soon":  "Due Soon",
    "due_today": "Due Today",
    "overdue":   "Overdue",
}


def _date_str(d: date) -> str:
    return d.isoformat() if d else ""


def _qdate(s: str) -> QDate:
    if s:
        try:
            parts = s.split("-")
            return QDate(int(parts[0]), int(parts[1]), int(parts[2]))
        except Exception:
            pass
    return QDate.currentDate()


def _add_one_month(d: date) -> date:
    try:
        from dateutil.relativedelta import relativedelta
        return d + relativedelta(months=1)
    except ImportError:
        return d + timedelta(days=30)


def _form_row_visible(form: QFormLayout, widget, visible: bool):
    """Show/hide both label and field of a QFormLayout row."""
    row, _ = form.getWidgetPosition(widget)
    if row < 0:
        return
    for role in (QFormLayout.LabelRole, QFormLayout.FieldRole):
        item = form.itemAt(row, role)
        if item and item.widget():
            item.widget().setVisible(visible)


# ─── Styled button helpers ────────────────────────────────────────────────────

_BTN_STYLES = {
    "edit":   (INFO,    "#1565C0"),
    "pay":    (SUCCESS, "#1B5E20"),
    "chat":   ("#00897B", "#004D40"),
    "remove": (DANGER,  "#B71C1C"),
}

def _action_btn(label: str, kind: str, tooltip: str) -> QPushButton:
    bg, hover = _BTN_STYLES[kind]
    btn = QPushButton(label)
    btn.setToolTip(tooltip)
    btn.setFixedHeight(30)
    btn.setMinimumWidth(62)
    btn.setStyleSheet(
        f"QPushButton {{ background-color: {bg}; color: white; border: none; "
        f"border-radius: 5px; font-size: 11px; font-weight: bold; padding: 0 6px; }}"
        f"QPushButton:hover {{ background-color: {hover}; }}"
        f"QPushButton:pressed {{ background-color: {hover}; }}"
    )
    return btn


# ─── Quick Add Dialog ─────────────────────────────────────────────────────────

class QuickAddStudentDialog(QDialog):
    """Minimal fields for fast enrollment."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Add Student")
        self.setMinimumWidth(460)
        self.setModal(True)
        self._result_data = None
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QDialog {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY}; }}"
            f"QLabel   {{ color: {TEXT_PRIMARY}; background: transparent; }}"
            f"QComboBox {{ background-color: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid #2A2A4A; border-radius: 6px; padding: 8px 10px; }}"
            f"QComboBox:hover {{ border-color: {ACCENT}; }}"
            f"QComboBox QAbstractItemView {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY}; border: 1px solid {BG_HOVER}; }}"
            f"QComboBox QAbstractItemView::item {{ color: {TEXT_PRIMARY}; background-color: {BG_PANEL}; padding: 6px 10px; }}"
            f"QComboBox QAbstractItemView::item:selected {{ background-color: {ACCENT}; color: white; }}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── Title bar ─────────────────────────────────────────────────────────
        title = QLabel("Quick Enroll")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {ACCENT};")
        root.addWidget(title)

        banner = QLabel("Fill in the required fields — defaults are applied automatically.")
        banner.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        banner.setWordWrap(True)
        root.addWidget(banner)

        # ── Form ──────────────────────────────────────────────────────────────
        self._form = QFormLayout()
        self._form.setSpacing(12)
        self._form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Full name")
        self._form.addRow("Name *", self._name)

        self._phone = QLineEdit()
        self._phone.setPlaceholderText("+91 XXXXXXXXXX")
        self._form.addRow("Phone *", self._phone)

        self._gender = QComboBox()
        self._gender.addItems(["Male", "Female", "Other"])
        self._form.addRow("Gender", self._gender)

        self._type = QComboBox()
        self._type.addItems(["Full-time", "Half-time"])
        self._type.currentIndexChanged.connect(self._on_type)
        self._form.addRow("Type *", self._type)

        # Full-time widgets
        avail = db.get_available_seats()
        self._seat = QComboBox()
        self._seat.addItem("-- Select Seat --", None)
        for sn in avail:
            self._seat.addItem(f"Seat {sn}", sn)
        self._form.addRow("Seat Number", self._seat)

        self._fulltime_info = QLabel("Hours: 6:00 AM  –  11:00 PM  (Full Day)")
        self._fulltime_info.setStyleSheet(
            f"color: {SUCCESS}; font-size: 12px; font-style: italic;"
        )
        self._form.addRow("Schedule", self._fulltime_info)

        # Half-time widgets
        self._shift = QComboBox()
        self._shift.addItems(["Morning  (6 AM – 2 PM)", "Evening  (2 PM – 11 PM)"])
        self._form.addRow("Shift", self._shift)

        root.addLayout(self._form)

        # Student ID preview
        code = db.generate_student_code()
        id_lbl = QLabel(f"Auto Student ID will be:  <b style='color:{ACCENT};'>{code}</b>")
        id_lbl.setTextFormat(Qt.RichText)
        id_lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;")
        root.addWidget(id_lbl)

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Enroll Student")
        save_btn.setObjectName("btn_success")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

        self._on_type()

    def _on_type(self):
        is_full = self._type.currentText() == "Full-time"
        _form_row_visible(self._form, self._seat,          is_full)
        _form_row_visible(self._form, self._fulltime_info, is_full)
        _form_row_visible(self._form, self._shift,         not is_full)
        self.adjustSize()

    def _save(self):
        name  = self._name.text().strip()
        phone = self._phone.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Please enter the student's name.")
            self._name.setFocus()
            return
        if not phone:
            QMessageBox.warning(self, "Required", "Please enter the student's phone number.")
            self._phone.setFocus()
            return
        stype = self._type.currentText()
        today = date.today()
        self._result_data = {
            "name":              name,
            "phone":             phone,
            "gender":            self._gender.currentText(),
            "student_type":      stype,
            "shift":             ("Morning" if self._shift.currentIndex() == 0 else "Evening")
                                 if stype == "Half-time" else None,
            "seat_number":       self._seat.currentData() if stype == "Full-time" else None,
            "join_date":         today.isoformat(),
            "last_payment_date": today.isoformat(),
            "next_payment_date": _add_one_month(today).isoformat(),
            "notes":             "",
        }
        self.accept()

    def get_data(self):
        return self._result_data


# ─── Full Student Dialog ──────────────────────────────────────────────────────

class StudentDialog(QDialog):
    """Full add / edit dialog."""

    def __init__(self, student_data: dict = None, parent=None):
        super().__init__(parent)
        self._data = student_data or {}
        self.setWindowTitle("Add New Student" if not student_data else "Edit Student")
        self.setMinimumWidth(540)
        self.setMinimumHeight(640)
        self.setModal(True)
        self._result_data = None
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QDialog {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY}; }}"
            f"QLabel   {{ color: {TEXT_PRIMARY}; background: transparent; }}"
            f"QComboBox {{ background-color: {BG_CARD}; color: {TEXT_PRIMARY}; border: 1px solid #2A2A4A; border-radius: 6px; padding: 8px 10px; }}"
            f"QComboBox:hover {{ border-color: {ACCENT}; }}"
            f"QComboBox QAbstractItemView {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY}; border: 1px solid {BG_HOVER}; }}"
            f"QComboBox QAbstractItemView::item {{ color: {TEXT_PRIMARY}; background-color: {BG_PANEL}; padding: 6px 10px; }}"
            f"QComboBox QAbstractItemView::item:selected {{ background-color: {ACCENT}; color: white; }}"
        )
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Coloured header strip ─────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setFixedHeight(60)
        header_frame.setStyleSheet(f"background-color: {BG_HOVER}; border-radius: 0;")
        hlay = QHBoxLayout(header_frame)
        hlay.setContentsMargins(24, 0, 24, 0)
        htitle = QLabel("Add New Student" if not self._data else f"Edit — {self._data.get('name','')}")
        htitle.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ACCENT};")

        # Student code badge
        code = self._data.get("student_code") or db.generate_student_code()
        self._student_code = code
        code_badge = QLabel(f"  ID: {code}  ")
        code_badge.setStyleSheet(
            f"background: {ACCENT}; color: white; border-radius: 4px; "
            f"font-size: 12px; font-weight: bold; padding: 3px 8px;"
        )
        hlay.addWidget(htitle)
        hlay.addStretch()
        hlay.addWidget(code_badge)
        outer.addWidget(header_frame)

        # ── Scrollable form body ──────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        self._form = QFormLayout(inner)
        self._form.setSpacing(14)
        self._form.setContentsMargins(24, 20, 24, 20)
        self._form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # ── Personal info section ─────────────────────────────────────────────
        sec1 = QLabel("Personal Information")
        sec1.setStyleSheet(
            f"color: {ACCENT}; font-size: 13px; font-weight: bold; "
            f"border-bottom: 1px solid {BG_HOVER}; padding-bottom: 4px;"
        )
        self._form.addRow(sec1)

        self._name = QLineEdit(self._data.get("name", ""))
        self._name.setPlaceholderText("Full name")
        self._form.addRow("Name *", self._name)

        self._phone = QLineEdit(self._data.get("phone", ""))
        self._phone.setPlaceholderText("+91 XXXXXXXXXX")
        self._form.addRow("Phone *", self._phone)

        self._gender = QComboBox()
        self._gender.addItems(["Male", "Female", "Other"])
        g_idx = {"Male": 0, "Female": 1, "Other": 2}.get(
            self._data.get("gender", "Male"), 0
        )
        self._gender.setCurrentIndex(g_idx)
        self._form.addRow("Gender", self._gender)

        # ── Enrollment section ────────────────────────────────────────────────
        sec2 = QLabel("Enrollment Details")
        sec2.setStyleSheet(
            f"color: {ACCENT}; font-size: 13px; font-weight: bold; "
            f"border-bottom: 1px solid {BG_HOVER}; padding-bottom: 4px;"
        )
        self._form.addRow(sec2)

        self._type = QComboBox()
        self._type.addItems(["Full-time", "Half-time"])
        t_idx = 0 if self._data.get("student_type", "Full-time") == "Full-time" else 1
        self._type.setCurrentIndex(t_idx)
        self._type.currentIndexChanged.connect(self._on_type_change)
        self._form.addRow("Type *", self._type)

        # Full-time: seat + schedule label
        avail = db.get_available_seats()
        cur_seat = self._data.get("seat_number")
        if cur_seat and cur_seat not in avail:
            avail.insert(0, cur_seat)
        self._seat = QComboBox()
        self._seat.addItem("-- Select Seat --", None)
        for sn in avail:
            self._seat.addItem(f"Seat {sn}", sn)
        if cur_seat:
            for i in range(self._seat.count()):
                if self._seat.itemData(i) == cur_seat:
                    self._seat.setCurrentIndex(i)
                    break
        self._form.addRow("Seat Number", self._seat)

        self._fulltime_schedule = QLabel("6:00 AM  –  11:00 PM  (Full Day access)")
        self._fulltime_schedule.setStyleSheet(
            f"color: {SUCCESS}; font-size: 12px; font-style: italic;"
        )
        self._form.addRow("Schedule", self._fulltime_schedule)

        # Half-time: shift selector
        self._shift = QComboBox()
        self._shift.addItems(["Morning  (6 AM – 2 PM)", "Evening  (2 PM – 11 PM)"])
        if "Evening" in (self._data.get("shift") or ""):
            self._shift.setCurrentIndex(1)
        self._form.addRow("Shift", self._shift)

        # ── Fee section ───────────────────────────────────────────────────────
        sec3 = QLabel("Fee Configuration")
        sec3.setStyleSheet(
            f"color: {ACCENT}; font-size: 13px; font-weight: bold; "
            f"border-bottom: 1px solid {BG_HOVER}; padding-bottom: 4px;"
        )
        self._form.addRow(sec3)

        fee_row = QHBoxLayout()
        self._use_custom_fee = QCheckBox("Override fee for this student")
        self._use_custom_fee.setChecked(self._data.get("custom_fee") is not None)
        self._use_custom_fee.stateChanged.connect(self._on_fee_toggle)
        self._custom_fee_spin = QDoubleSpinBox()
        self._custom_fee_spin.setRange(0, 100000)
        self._custom_fee_spin.setPrefix("Rs. ")
        self._custom_fee_spin.setDecimals(0)
        self._custom_fee_spin.setFixedWidth(130)
        default_fee = (
            self._data.get("custom_fee") or
            db.get_setting("fulltime_fee" if self._data.get("student_type","Full-time") == "Full-time"
                           else "halftime_fee") or "500"
        )
        self._custom_fee_spin.setValue(float(default_fee))
        fee_row.addWidget(self._use_custom_fee)
        fee_row.addStretch()
        fee_row.addWidget(self._custom_fee_spin)
        self._form.addRow("Monthly Fee", fee_row)
        self._on_fee_toggle()

        # ── Payment dates section ─────────────────────────────────────────────
        sec4 = QLabel("Payment Dates")
        sec4.setStyleSheet(
            f"color: {ACCENT}; font-size: 13px; font-weight: bold; "
            f"border-bottom: 1px solid {BG_HOVER}; padding-bottom: 4px;"
        )
        self._form.addRow(sec4)

        self._join = QDateEdit()
        self._join.setCalendarPopup(True)
        self._join.setDisplayFormat("dd MMM yyyy")
        self._join.setDate(_qdate(self._data.get("join_date", _date_str(date.today()))))
        self._form.addRow("Join Date *", self._join)

        self._last_pay = QDateEdit()
        self._last_pay.setCalendarPopup(True)
        self._last_pay.setDisplayFormat("dd MMM yyyy")
        lp = self._data.get("last_payment_date") or _date_str(date.today())
        self._last_pay.setDate(_qdate(lp))
        self._last_pay.dateChanged.connect(self._update_next_payment)
        self._form.addRow("Last Payment", self._last_pay)

        self._next_pay = QDateEdit()
        self._next_pay.setCalendarPopup(True)
        self._next_pay.setDisplayFormat("dd MMM yyyy")
        if self._data.get("next_payment_date"):
            self._next_pay.setDate(_qdate(self._data["next_payment_date"]))
        else:
            self._update_next_payment()
        self._form.addRow("Next Due Date", self._next_pay)

        # ── Notes ─────────────────────────────────────────────────────────────
        self._notes = QTextEdit(self._data.get("notes", ""))
        self._notes.setPlaceholderText("Optional notes about this student…")
        self._notes.setFixedHeight(72)
        self._form.addRow("Notes", self._notes)

        scroll.setWidget(inner)
        outer.addWidget(scroll)

        # ── Bottom button bar ─────────────────────────────────────────────────
        bar = QFrame()
        bar.setStyleSheet(f"background-color: {BG_CARD}; border-top: 1px solid {BG_HOVER};")
        bar.setFixedHeight(60)
        blay = QHBoxLayout(bar)
        blay.setContentsMargins(24, 0, 24, 0)
        blay.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("  Save Student  ")
        save_btn.setObjectName("btn_success")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._save)
        blay.addWidget(cancel_btn)
        blay.addSpacing(8)
        blay.addWidget(save_btn)
        outer.addWidget(bar)

        # Apply initial type state
        self._on_type_change()

    def _on_type_change(self):
        is_full = self._type.currentText() == "Full-time"
        _form_row_visible(self._form, self._seat,              is_full)
        _form_row_visible(self._form, self._fulltime_schedule, is_full)
        _form_row_visible(self._form, self._shift,             not is_full)

    def _on_fee_toggle(self):
        self._custom_fee_spin.setEnabled(self._use_custom_fee.isChecked())

    def _update_next_payment(self):
        lp = self._last_pay.date().toPyDate()
        np = _add_one_month(lp)
        self._next_pay.setDate(QDate(np.year, np.month, np.day))

    def _save(self):
        name  = self._name.text().strip()
        phone = self._phone.text().strip()
        if not name:
            QMessageBox.warning(self, "Required", "Please enter the student's name.")
            self._name.setFocus()
            return
        if not phone:
            QMessageBox.warning(self, "Required", "Please enter the student's phone number.")
            self._phone.setFocus()
            return

        stype = self._type.currentText()
        shift = seat = None

        if stype == "Half-time":
            shift = "Morning" if self._shift.currentIndex() == 0 else "Evening"
        else:
            seat = self._seat.currentData()
            existing_id = self._data.get("id")
            if seat and db.is_seat_taken(seat, exclude_student_id=existing_id):
                QMessageBox.warning(
                    self, "Seat Already Taken",
                    f"Seat {seat} is already occupied by another student.\n"
                    "Please choose a different seat."
                )
                return

        custom_fee = float(self._custom_fee_spin.value()) if self._use_custom_fee.isChecked() else None

        self._result_data = {
            "student_code":      self._student_code,
            "name":              name,
            "phone":             phone,
            "gender":            self._gender.currentText(),
            "student_type":      stype,
            "shift":             shift,
            "seat_number":       seat,
            "custom_fee":        custom_fee,
            "join_date":         self._join.date().toPyDate().isoformat(),
            "last_payment_date": self._last_pay.date().toPyDate().isoformat(),
            "next_payment_date": self._next_pay.date().toPyDate().isoformat(),
            "notes":             self._notes.toPlainText().strip(),
        }
        self.accept()

    def get_data(self):
        return self._result_data


# ─── Payment Dialog ───────────────────────────────────────────────────────────

class PaymentDialog(QDialog):
    def __init__(self, student: dict, parent=None):
        super().__init__(parent)
        code = student.get("student_code") or ""
        self.setWindowTitle(f"Record Payment  [{student['name']}]")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._student = student
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QDialog {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY}; }}"
            f"QLabel   {{ color: {TEXT_PRIMARY}; background: transparent; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        code = self._student.get("student_code") or "–"
        fee  = db.get_effective_fee(self._student)
        info = QLabel(
            f"<b style='font-size:14px;'>{self._student['name']}</b>"
            f"  <span style='color:{ACCENT};'>[{code}]</span><br>"
            f"<span style='color:{TEXT_SECONDARY};'>"
            f"{self._student['student_type']}  |  "
            f"Effective Fee: Rs. {fee:,.0f}</span>"
        )
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BG_HOVER};")
        layout.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self._amount = QLineEdit(str(int(fee)))
        self._amount.setPlaceholderText("Amount in rupees")
        form.addRow("Amount (Rs.) *", self._amount)

        self._pay_date = QDateEdit()
        self._pay_date.setCalendarPopup(True)
        self._pay_date.setDisplayFormat("dd MMM yyyy")
        # Default to student's next due date if available, otherwise today
        default_date = QDate.currentDate()
        if self._student.get("next_payment_date"):
            default_date = _qdate(self._student["next_payment_date"])
        self._pay_date.setDate(default_date)
        self._pay_date.dateChanged.connect(self._update_next)
        form.addRow("Payment Date", self._pay_date)

        self._next_date = QDateEdit()
        self._next_date.setCalendarPopup(True)
        self._next_date.setDisplayFormat("dd MMM yyyy")
        form.addRow("Next Due Date", self._next_date)
        self._update_next()

        self._note = QLineEdit()
        self._note.setPlaceholderText("e.g. Cash, UPI, etc.")
        form.addRow("Note", self._note)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        confirm_btn = QPushButton("  Confirm Payment  ")
        confirm_btn.setObjectName("btn_success")
        confirm_btn.setFixedHeight(36)
        confirm_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addSpacing(8)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def _update_next(self):
        pd = self._pay_date.date().toPyDate()
        nd = _add_one_month(pd)
        self._next_date.setDate(QDate(nd.year, nd.month, nd.day))

    def _save(self):
        try:
            amount = float(self._amount.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid number.")
            return
        db.record_payment(
            self._student["id"],
            amount,
            self._pay_date.date().toPyDate().isoformat(),
            self._next_date.date().toPyDate().isoformat(),
            self._note.text().strip(),
        )
        self.accept()


# ─── Main Widget ──────────────────────────────────────────────────────────────

class StudentManagementWidget(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)

        # ── Header ─────────────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Student Management")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        quick_btn = QPushButton("  Quick Add  ")
        quick_btn.setObjectName("btn_warning")
        quick_btn.setFixedHeight(38)
        quick_btn.clicked.connect(self._quick_add)
        header.addWidget(quick_btn)

        add_btn = QPushButton("  Add Student  ")
        add_btn.setObjectName("btn_primary")
        add_btn.setFixedHeight(38)
        add_btn.clicked.connect(self._add_student)
        header.addWidget(add_btn)
        root.addLayout(header)

        # ── Search / filter bar ───────────────────────────────────────────────
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name, phone, ID, or seat…")
        self._search.textChanged.connect(self.refresh)
        search_row.addWidget(self._search, 3)

        for lbl, attr, items in [
            ("Type:",   "_filter_type",   ["All Types", "Full-time", "Half-time"]),
            ("Gender:", "_filter_gender", ["All Genders", "Male", "Female", "Other"]),
            ("Status:", "_filter_status", ["All Status", "Paid", "Due Soon", "Due Today", "Overdue"]),
        ]:
            l = QLabel(lbl)
            l.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
            combo = QComboBox()
            combo.addItems(items)
            combo.currentIndexChanged.connect(self.refresh)
            search_row.addWidget(l)
            search_row.addWidget(combo, 1)
            setattr(self, attr, combo)

        root.addLayout(search_row)

        # ── Table ──────────────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(11)
        self._table.setHorizontalHeaderLabels([
            "ID", "Name", "Phone", "Gender", "Type", "Seat / Shift",
            "Fee (Rs.)", "Last Paid", "Next Due", "Status", "Actions"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setColumnWidth(0,  70)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3,  70)
        self._table.setColumnWidth(4,  85)
        self._table.setColumnWidth(5, 110)
        self._table.setColumnWidth(6,  80)
        self._table.setColumnWidth(7, 100)
        self._table.setColumnWidth(8, 100)
        self._table.setColumnWidth(9,  85)
        self._table.setColumnWidth(10, 260)
        root.addWidget(self._table)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        root.addWidget(self._count_lbl)

    # ── refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        search  = self._search.text().strip() if hasattr(self, "_search") else ""
        students = db.get_all_students(search)

        ftype   = self._filter_type.currentText()   if hasattr(self, "_filter_type")   else "All Types"
        fgender = self._filter_gender.currentText() if hasattr(self, "_filter_gender") else "All Genders"
        fstatus = self._filter_status.currentText() if hasattr(self, "_filter_status") else "All Status"

        if ftype != "All Types":
            students = [s for s in students if s["student_type"] == ftype]
        if fgender != "All Genders":
            students = [s for s in students if (s.get("gender") or "Male") == fgender]
        if fstatus not in ("All Status", "All"):
            key_map = {"Paid": "paid", "Due Soon": "due_soon",
                       "Due Today": "due_today", "Overdue": "overdue"}
            target = key_map.get(fstatus)
            if target:
                students = [s for s in students if db.get_payment_status(s) == target]

        self._table.setRowCount(len(students))
        self._count_lbl.setText(f"Showing {len(students)} student(s)")

        for row, s in enumerate(students):
            self._table.setRowHeight(row, 48)
            status       = db.get_payment_status(s)
            status_color = STATUS_COLORS.get(status, SUCCESS)
            status_label = STATUS_LABELS.get(status, "Paid")
            fee  = db.get_effective_fee(s)
            code = s.get("student_code") or "–"

            row_data = [
                code,
                s["name"],
                s["phone"],
                s.get("gender") or "–",
                s["student_type"],
                (f"Shift: {s['shift']}" if s["student_type"] == "Half-time"
                 else (f"Seat {s['seat_number']}" if s["seat_number"] else "No Seat")),
                f"Rs. {fee:,.0f}",
                s.get("last_payment_date") or "–",
                s.get("next_payment_date") or "–",
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                if col == 8:
                    item.setForeground(QColor(status_color))
                self._table.setItem(row, col, item)

            # Status cell
            s_item = QTableWidgetItem(status_label)
            s_item.setForeground(QColor(status_color))
            s_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self._table.setItem(row, 9, s_item)

            # Action buttons
            cell = QWidget()
            cell.setStyleSheet("background: transparent;")
            blay = QHBoxLayout(cell)
            blay.setContentsMargins(4, 6, 4, 6)
            blay.setSpacing(5)

            edit_btn = _action_btn("Edit",   "edit",   "Edit this student")
            pay_btn  = _action_btn("Pay",    "pay",    "Record a payment")
            chat_btn = _action_btn("Chat",   "chat",   "Open WhatsApp chat")
            del_btn  = _action_btn("Remove", "remove", "Remove student")

            sid = s["id"]
            edit_btn.clicked.connect(lambda _, i=sid: self._edit_student(i))
            pay_btn.clicked.connect( lambda _, i=sid: self._record_payment(i))
            chat_btn.clicked.connect(lambda _, i=sid: self._open_whatsapp(i))
            del_btn.clicked.connect( lambda _, i=sid: self._remove_student(i))

            for b in (edit_btn, pay_btn, chat_btn, del_btn):
                blay.addWidget(b)
            blay.addStretch()
            self._table.setCellWidget(row, 10, cell)

    # ── actions ───────────────────────────────────────────────────────────────

    def _quick_add(self):
        dlg = QuickAddStudentDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                db.add_student(data)
                self.refresh()
                self.data_changed.emit()

    def _add_student(self):
        dlg = StudentDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                db.add_student(data)
                self.refresh()
                self.data_changed.emit()

    def _edit_student(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        dlg = StudentDialog(student_data=student, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            if data:
                db.update_student(student_id, data)
                self.refresh()
                self.data_changed.emit()

    def _record_payment(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        dlg = PaymentDialog(student, parent=self)
        if dlg.exec_():
            self.refresh()
            self.data_changed.emit()

    def _open_whatsapp(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        from utils.whatsapp import open_whatsapp_chat, format_reminder_message
        tmpl = db.get_setting("whatsapp_reminder_message") or ""
        msg  = format_reminder_message(tmpl, student["name"],
                                       student.get("next_payment_date") or "")
        open_whatsapp_chat(student["phone"], msg)

    def _remove_student(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        code = student.get("student_code") or "—"
        reply = QMessageBox.question(
            self, "Remove Student",
            f"Are you sure you want to remove <b>{student['name']}</b> [{code}]?<br><br>"
            "The student will be archived (not permanently deleted) in Removed Students, "
            "so payment history is preserved and re-admit is possible.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            phone = db.remove_student(student_id)
            if phone:
                try:
                    from utils.whatsapp import send_message, format_removal_message
                    msg_tmpl = db.get_setting("whatsapp_removal_message") or ""
                    msg = format_removal_message(msg_tmpl, student["name"])
                    send_message(phone, msg)
                except Exception:
                    pass
            QMessageBox.information(
                self, "Removed",
                f"{student['name']} has been archived. You can re-admit from Removed Students anytime."
            )
            self.refresh()
            self.data_changed.emit()
