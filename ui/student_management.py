"""Student management: full list, quick-add, edit, remove, search."""
from datetime import date, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QTextEdit, QDateEdit, QMessageBox,
    QHeaderView, QAbstractItemView, QFrame, QSplitter,
    QScrollArea, QGroupBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, BG_CARD, BG_PANEL, ACCENT,
    SUCCESS, DANGER, WARNING, INFO, PURPLE, BG_HOVER, BG_DARK
)

# Payment status colors
STATUS_COLORS = {
    "paid":      "#27AE60",
    "due_soon":  "#F39C12",
    "due_today": "#E67E22",
    "overdue":   "#E74C3C",
}
STATUS_LABELS = {
    "paid":      "✅ Paid",
    "due_soon":  "⏳ Due Soon",
    "due_today": "💰 Due Today",
    "overdue":   "🔴 Overdue",
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


# ─── Quick Add Dialog ────────────────────────────────────────────────────────

class QuickAddStudentDialog(QDialog):
    """Minimal fields for fast enrollment."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚡ Quick Add Student")
        self.setMinimumWidth(420)
        self._result_data = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        banner = QLabel("Fill in the required fields. Defaults will be applied automatically.")
        banner.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        banner.setWordWrap(True)
        layout.addWidget(banner)

        form = QFormLayout()
        form.setSpacing(10)

        self._name = QLineEdit()
        self._name.setPlaceholderText("Full name *")
        form.addRow("Name *", self._name)

        self._phone = QLineEdit()
        self._phone.setPlaceholderText("+91 XXXXXXXXXX *")
        form.addRow("Phone *", self._phone)

        self._type = QComboBox()
        self._type.addItems(["Full-time", "Half-time"])
        self._type.currentIndexChanged.connect(self._on_type)
        form.addRow("Type *", self._type)

        self._gender = QComboBox()
        self._gender.addItems(["Male", "Female", "Other"])
        form.addRow("Gender", self._gender)

        # Seat (full-time)
        avail = db.get_available_seats()
        self._seat = QComboBox()
        self._seat.addItem("— No Seat —", None)
        for sn in avail:
            self._seat.addItem(str(sn), sn)
        form.addRow("Seat", self._seat)

        # Shift (half-time)
        self._shift = QComboBox()
        self._shift.addItems(["Morning (6AM–2PM)", "Evening (2PM–11PM)"])
        form.addRow("Shift", self._shift)

        layout.addLayout(form)
        self._on_type()

        # Code preview
        code = db.generate_student_code()
        code_lbl = QLabel(f"Auto Student ID: <b>{code}</b>")
        code_lbl.setStyleSheet(
            f"color: {ACCENT}; background: transparent; font-size: 12px;"
        )
        code_lbl.setTextFormat(Qt.RichText)
        layout.addWidget(code_lbl)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("⚡ Quick Enroll")
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _on_type(self):
        is_full = self._type.currentText() == "Full-time"
        self._seat.setEnabled(is_full)
        self._shift.setEnabled(not is_full)

    def _save(self):
        name = self._name.text().strip()
        phone = self._phone.text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Required", "Name and Phone are required.")
            return
        stype = self._type.currentText()
        today = date.today()
        next_due = _add_one_month(today)
        self._result_data = {
            "name":                name,
            "phone":               phone,
            "gender":              self._gender.currentText(),
            "student_type":        stype,
            "shift":               ("Morning" if self._shift.currentIndex() == 0 else "Evening")
                                   if stype == "Half-time" else None,
            "seat_number":         self._seat.currentData() if stype == "Full-time" else None,
            "join_date":           today.isoformat(),
            "last_payment_date":   today.isoformat(),
            "next_payment_date":   next_due.isoformat(),
            "notes":               "",
        }
        self.accept()

    def get_data(self):
        return self._result_data


# ─── Full Student Dialog ────────────────────────────────────────────────────

class StudentDialog(QDialog):
    """Full add / edit student dialog."""
    def __init__(self, student_data: dict = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Student" if not student_data else "Edit Student")
        self.setMinimumWidth(520)
        self.setMinimumHeight(620)
        self._data = student_data or {}
        self._result_data = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        form = QFormLayout(inner)
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # Student Code (display only)
        code = self._data.get("student_code") or db.generate_student_code()
        code_lbl = QLabel(f"<b style='color:{ACCENT};'>{code}</b>")
        code_lbl.setTextFormat(Qt.RichText)
        code_lbl.setStyleSheet("background: transparent;")
        form.addRow("Student ID", code_lbl)
        self._student_code = code

        self._name = QLineEdit(self._data.get("name", ""))
        self._name.setPlaceholderText("Full name")
        form.addRow("Name *", self._name)

        self._phone = QLineEdit(self._data.get("phone", ""))
        self._phone.setPlaceholderText("+91 XXXXXXXXXX")
        form.addRow("Phone *", self._phone)

        self._gender = QComboBox()
        self._gender.addItems(["Male", "Female", "Other"])
        g = self._data.get("gender", "Male")
        idx = {"Male": 0, "Female": 1, "Other": 2}.get(g, 0)
        self._gender.setCurrentIndex(idx)
        form.addRow("Gender", self._gender)

        self._type = QComboBox()
        self._type.addItems(["Full-time", "Half-time"])
        idx = 0 if self._data.get("student_type", "Full-time") == "Full-time" else 1
        self._type.setCurrentIndex(idx)
        self._type.currentIndexChanged.connect(self._on_type_change)
        form.addRow("Type *", self._type)

        self._shift = QComboBox()
        self._shift.addItems(["Morning (6AM–2PM)", "Evening (2PM–11PM)"])
        if self._data.get("shift") and "Evening" in self._data.get("shift", ""):
            self._shift.setCurrentIndex(1)
        form.addRow("Shift", self._shift)

        avail = db.get_available_seats()
        cur_seat = self._data.get("seat_number")
        if cur_seat and cur_seat not in avail:
            avail.insert(0, cur_seat)
        self._seat = QComboBox()
        self._seat.addItem("— None —", None)
        for sn in avail:
            self._seat.addItem(str(sn), sn)
        if cur_seat:
            for i in range(self._seat.count()):
                if self._seat.itemData(i) == cur_seat:
                    self._seat.setCurrentIndex(i)
                    break
        form.addRow("Seat Number", self._seat)

        # Fee configuration
        fee_row = QHBoxLayout()
        self._use_custom_fee = QCheckBox("Override with custom fee")
        self._use_custom_fee.setChecked(self._data.get("custom_fee") is not None)
        self._use_custom_fee.stateChanged.connect(self._on_fee_toggle)
        fee_row.addWidget(self._use_custom_fee)
        self._custom_fee_spin = QDoubleSpinBox()
        self._custom_fee_spin.setRange(0, 100000)
        self._custom_fee_spin.setPrefix("₹ ")
        self._custom_fee_spin.setDecimals(0)
        self._custom_fee_spin.setValue(
            float(self._data.get("custom_fee") or
                  (db.get_setting("fulltime_fee") if self._data.get("student_type") == "Full-time"
                   else db.get_setting("halftime_fee")) or "500")
        )
        fee_row.addWidget(self._custom_fee_spin)
        form.addRow("Monthly Fee", fee_row)
        self._on_fee_toggle()

        self._join = QDateEdit()
        self._join.setCalendarPopup(True)
        self._join.setDisplayFormat("dd MMM yyyy")
        self._join.setDate(_qdate(self._data.get("join_date", _date_str(date.today()))))
        form.addRow("Join Date *", self._join)

        self._last_pay = QDateEdit()
        self._last_pay.setCalendarPopup(True)
        self._last_pay.setDisplayFormat("dd MMM yyyy")
        lp = self._data.get("last_payment_date") or _date_str(date.today())
        self._last_pay.setDate(_qdate(lp))
        self._last_pay.dateChanged.connect(self._update_next_payment)
        form.addRow("Last Payment", self._last_pay)

        self._next_pay = QDateEdit()
        self._next_pay.setCalendarPopup(True)
        self._next_pay.setDisplayFormat("dd MMM yyyy")
        np_str = self._data.get("next_payment_date")
        if np_str:
            self._next_pay.setDate(_qdate(np_str))
        else:
            self._update_next_payment()
        form.addRow("Next Payment", self._next_pay)

        self._notes = QTextEdit(self._data.get("notes", ""))
        self._notes.setPlaceholderText("Optional notes…")
        self._notes.setFixedHeight(70)
        form.addRow("Notes", self._notes)

        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._on_type_change()

    def _on_type_change(self):
        is_full = self._type.currentText() == "Full-time"
        self._shift.setEnabled(not is_full)
        self._seat.setEnabled(is_full)

    def _on_fee_toggle(self):
        self._custom_fee_spin.setEnabled(self._use_custom_fee.isChecked())

    def _update_next_payment(self):
        lp = self._last_pay.date().toPyDate()
        np = _add_one_month(lp)
        self._next_pay.setDate(QDate(np.year, np.month, np.day))

    def _save(self):
        name = self._name.text().strip()
        phone = self._phone.text().strip()
        if not name or not phone:
            QMessageBox.warning(self, "Validation", "Name and Phone are required.")
            return
        stype = self._type.currentText()
        shift = None
        seat = None
        if stype == "Half-time":
            shift = "Morning" if self._shift.currentIndex() == 0 else "Evening"
        else:
            seat = self._seat.currentData()
            # Conflict protection
            existing_sid = self._data.get("id")
            if seat and db.is_seat_taken(seat, exclude_student_id=existing_sid):
                QMessageBox.warning(
                    self, "Seat Taken",
                    f"Seat {seat} is already assigned to another student.\n"
                    "Please choose a different seat."
                )
                return

        custom_fee = None
        if self._use_custom_fee.isChecked():
            custom_fee = float(self._custom_fee_spin.value())

        self._result_data = {
            "student_code":       self._student_code,
            "name":               name,
            "phone":              phone,
            "gender":             self._gender.currentText(),
            "student_type":       stype,
            "shift":              shift,
            "seat_number":        seat,
            "custom_fee":         custom_fee,
            "join_date":          self._join.date().toPyDate().isoformat(),
            "last_payment_date":  self._last_pay.date().toPyDate().isoformat(),
            "next_payment_date":  self._next_pay.date().toPyDate().isoformat(),
            "notes":              self._notes.toPlainText().strip(),
        }
        self.accept()

    def get_data(self):
        return self._result_data


# ─── Payment Dialog ──────────────────────────────────────────────────────────

class PaymentDialog(QDialog):
    def __init__(self, student: dict, parent=None):
        super().__init__(parent)
        code = student.get("student_code") or ""
        self.setWindowTitle(f"Record Payment – {student['name']} [{code}]")
        self.setMinimumWidth(420)
        self._student = student
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        code = self._student.get("student_code") or "–"
        info = QLabel(
            f"<b>{self._student['name']}</b>  [{code}]  |  {self._student['phone']}<br>"
            f"Type: {self._student['student_type']}  |  "
            f"Effective Fee: ₹{db.get_effective_fee(self._student):,.0f}"
        )
        info.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(10)

        fee = db.get_effective_fee(self._student)
        self._amount = QLineEdit(str(int(fee)))
        self._amount.setPlaceholderText("Amount")
        form.addRow("Amount (₹)", self._amount)

        self._pay_date = QDateEdit()
        self._pay_date.setCalendarPopup(True)
        self._pay_date.setDisplayFormat("dd MMM yyyy")
        self._pay_date.setDate(QDate.currentDate())
        self._pay_date.dateChanged.connect(self._update_next)
        form.addRow("Payment Date", self._pay_date)

        self._next_date = QDateEdit()
        self._next_date.setCalendarPopup(True)
        self._next_date.setDisplayFormat("dd MMM yyyy")
        form.addRow("Next Due Date", self._next_date)
        self._update_next()

        self._note = QLineEdit()
        self._note.setPlaceholderText("Optional note")
        form.addRow("Note", self._note)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("✅ Confirm Payment")
        save_btn.setObjectName("btn_success")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def _update_next(self):
        pd = self._pay_date.date().toPyDate()
        nd = _add_one_month(pd)
        self._next_date.setDate(QDate(nd.year, nd.month, nd.day))

    def _save(self):
        try:
            amount = float(self._amount.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid", "Enter a valid amount.")
            return
        pay_date  = self._pay_date.date().toPyDate().isoformat()
        next_date = self._next_date.date().toPyDate().isoformat()
        note      = self._note.text().strip()
        db.record_payment(self._student["id"], amount, pay_date, next_date, note)
        self.accept()


# ─── Main Widget ─────────────────────────────────────────────────────────────

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
        title = QLabel("👥 Student Management")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        quick_btn = QPushButton("⚡ Quick Add")
        quick_btn.setObjectName("btn_warning")
        quick_btn.clicked.connect(self._quick_add)
        header.addWidget(quick_btn)

        add_btn = QPushButton("➕ Add Student")
        add_btn.setObjectName("btn_primary")
        add_btn.clicked.connect(self._add_student)
        header.addWidget(add_btn)
        root.addLayout(header)

        # ── Search / filter bar ───────────────────────────────────────────────
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Search by name, phone, ID, or seat…")
        self._search.textChanged.connect(self.refresh)
        search_row.addWidget(self._search)

        for lbl, attr, items in [
            ("Type:", "_filter_type", ["All", "Full-time", "Half-time"]),
            ("Gender:", "_filter_gender", ["All", "Male", "Female", "Other"]),
            ("Status:", "_filter_status", ["All", "Paid", "Due Soon", "Due Today", "Overdue"]),
        ]:
            l = QLabel(lbl)
            l.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
            combo = QComboBox()
            combo.addItems(items)
            combo.currentIndexChanged.connect(self.refresh)
            search_row.addWidget(l)
            search_row.addWidget(combo)
            setattr(self, attr, combo)

        root.addLayout(search_row)

        # ── Table ──────────────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(11)
        self._table.setHorizontalHeaderLabels([
            "ID", "Name", "Phone", "Gender", "Type", "Seat/Shift",
            "Fee (₹)", "Last Paid", "Next Due", "Status", "Actions"
        ])
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setColumnWidth(0,  60)
        self._table.setColumnWidth(2, 120)
        self._table.setColumnWidth(3,  75)
        self._table.setColumnWidth(4,  85)
        self._table.setColumnWidth(5, 110)
        self._table.setColumnWidth(6,  75)
        self._table.setColumnWidth(7, 100)
        self._table.setColumnWidth(8, 100)
        self._table.setColumnWidth(9,  95)
        self._table.setColumnWidth(10, 190)
        root.addWidget(self._table)

        # Count bar
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent;"
        )
        root.addWidget(self._count_lbl)

    def refresh(self):
        search = self._search.text().strip() if hasattr(self, "_search") else ""
        students = db.get_all_students(search)

        ftype   = self._filter_type.currentText()   if hasattr(self, "_filter_type")   else "All"
        fgender = self._filter_gender.currentText() if hasattr(self, "_filter_gender") else "All"
        fstatus = self._filter_status.currentText() if hasattr(self, "_filter_status") else "All"

        if ftype != "All":
            students = [s for s in students if s["student_type"] == ftype]
        if fgender != "All":
            students = [s for s in students if (s.get("gender") or "Male") == fgender]
        if fstatus != "All":
            status_key_map = {
                "Paid":      "paid",
                "Due Soon":  "due_soon",
                "Due Today": "due_today",
                "Overdue":   "overdue",
            }
            target = status_key_map.get(fstatus)
            if target:
                students = [s for s in students if db.get_payment_status(s) == target]

        self._table.setRowCount(len(students))
        self._count_lbl.setText(f"Showing {len(students)} student(s)")

        for row, s in enumerate(students):
            self._table.setRowHeight(row, 46)
            status = db.get_payment_status(s)
            status_color = STATUS_COLORS.get(status, SUCCESS)
            status_label = STATUS_LABELS.get(status, "✅ Paid")
            fee = db.get_effective_fee(s)
            code = s.get("student_code") or "–"

            row_data = [
                code,
                s["name"],
                s["phone"],
                s.get("gender") or "–",
                s["student_type"],
                (f"Shift: {s['shift']}" if s["student_type"] == "Half-time"
                 else (f"Seat: {s['seat_number']}" if s["seat_number"] else "No Seat")),
                f"₹{fee:,.0f}",
                s.get("last_payment_date") or "–",
                s.get("next_payment_date") or "–",
            ]
            for col, text in enumerate(row_data):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                # Colour next-due cell by payment status
                if col == 8:
                    item.setForeground(QColor(status_color))
                self._table.setItem(row, col, item)

            # Status badge
            status_item = QTableWidgetItem(status_label)
            status_item.setForeground(QColor(status_color))
            status_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
            self._table.setItem(row, 9, status_item)

            # Action buttons
            cell_widget = QWidget()
            cell_widget.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(cell_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)
            btn_layout.setSpacing(4)

            for icon, tip, color, cb in [
                ("✏️", "Edit",          BG_HOVER, lambda _, sid=s["id"]: self._edit_student(sid)),
                ("💰", "Record payment", BG_HOVER, lambda _, sid=s["id"]: self._record_payment(sid)),
                ("📱", "WhatsApp",       BG_HOVER, lambda _, sid=s["id"]: self._open_whatsapp(sid)),
                ("🗑️", "Remove",         BG_HOVER, lambda _, sid=s["id"]: self._remove_student(sid)),
            ]:
                btn = QPushButton(icon)
                btn.setToolTip(tip)
                btn.setFixedSize(34, 34)
                btn.setStyleSheet(
                    f"background-color: {color}; border-radius: 6px; "
                    f"color: white; font-size: 13px;"
                )
                btn.clicked.connect(cb)
                btn_layout.addWidget(btn)
            btn_layout.addStretch()
            self._table.setCellWidget(row, 10, cell_widget)

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
        msg = format_reminder_message(tmpl, student["name"], student.get("next_payment_date") or "")
        open_whatsapp_chat(student["phone"], msg)

    def _remove_student(self, student_id: int):
        student = db.get_student(student_id)
        if not student:
            return
        reply = QMessageBox.question(
            self, "Remove Student",
            f"Remove <b>{student['name']}</b> [{student.get('student_code','—')}]?<br><br>"
            "Their record will be archived and a WhatsApp message will be sent.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            phone = db.remove_student(student_id)
            if phone:
                try:
                    from utils.whatsapp import send_message, format_removal_message
                    msg_tmpl = db.get_setting("whatsapp_removal_message") or ""
                    msg = format_removal_message(msg_tmpl, student["name"])
                    send_message(phone, msg)
                    QMessageBox.information(
                        self, "Removed",
                        f"{student['name']} has been removed.\n"
                        "WhatsApp removal message queued."
                    )
                except Exception:
                    QMessageBox.information(self, "Removed", f"{student['name']} has been removed.")
            self.refresh()
            self.data_changed.emit()
