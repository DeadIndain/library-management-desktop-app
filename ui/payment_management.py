"""Payment management: view all payment history for students."""
from datetime import date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
    QFrame, QHeaderView, QAbstractItemView, QMessageBox,
    QDialog, QFormLayout, QDateEdit, QSplitter
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor
import database as db
from styles import (
    TEXT_PRIMARY, TEXT_SECONDARY, ACCENT, SUCCESS, DANGER, WARNING,
    INFO, BG_CARD, BG_PANEL, BG_HOVER
)

STATUS_COLORS = {
    "paid":      "#27AE60",
    "due_soon":  "#F39C12",
    "due_today": "#E67E22",
    "overdue":   "#E74C3C",
}


class PaymentManagementWidget(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_student = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("💳 Payment Management")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: bold; color: {TEXT_PRIMARY}; background: transparent;"
        )
        root.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)

        # Left: student list
        left = QFrame()
        left.setObjectName("card")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        left_title = QLabel("Students")
        left_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {TEXT_SECONDARY}; background: transparent;"
        )
        left_layout.addWidget(left_title)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 Search…")
        self._search.textChanged.connect(self._load_students)
        left_layout.addWidget(self._search)

        self._student_table = QTableWidget()
        self._student_table.setColumnCount(3)
        self._student_table.setHorizontalHeaderLabels(["Name", "Phone", "Next Due"])
        self._student_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._student_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._student_table.setAlternatingRowColors(True)
        self._student_table.verticalHeader().setVisible(False)
        self._student_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._student_table.setShowGrid(False)
        self._student_table.itemSelectionChanged.connect(self._on_student_selected)
        left_layout.addWidget(self._student_table)

        # Right: payment history
        right = QFrame()
        right.setObjectName("card")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        right_header = QHBoxLayout()
        self._history_title = QLabel("Select a student to view payment history")
        self._history_title.setStyleSheet(
            f"font-size: 14px; font-weight: bold; color: {TEXT_SECONDARY}; background: transparent;"
        )
        right_header.addWidget(self._history_title)
        right_header.addStretch()

        self._pay_btn = QPushButton("➕ Record Payment")
        self._pay_btn.setObjectName("btn_success")
        self._pay_btn.setEnabled(False)
        self._pay_btn.clicked.connect(self._record_payment)
        right_header.addWidget(self._pay_btn)

        self._wa_chat_btn = QPushButton("💬 Open Chat")
        self._wa_chat_btn.setObjectName("btn_primary")
        self._wa_chat_btn.setEnabled(False)
        self._wa_chat_btn.clicked.connect(self._open_wa_chat)
        right_header.addWidget(self._wa_chat_btn)

        self._wa_btn = QPushButton("📱 Send Reminder")
        self._wa_btn.setObjectName("btn_warning")
        self._wa_btn.setEnabled(False)
        self._wa_btn.clicked.connect(self._send_reminder)
        right_header.addWidget(self._wa_btn)

        right_layout.addLayout(right_header)

        # Student info banner
        self._info_frame = QFrame()
        self._info_frame.setStyleSheet(
            f"background-color: {BG_PANEL}; border-radius: 8px; padding: 4px;"
        )
        info_layout = QHBoxLayout(self._info_frame)
        info_layout.setContentsMargins(12, 8, 12, 8)
        self._info_label = QLabel("")
        self._info_label.setStyleSheet(f"color: {TEXT_SECONDARY}; background: transparent;")
        info_layout.addWidget(self._info_label)
        right_layout.addWidget(self._info_frame)

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels([
            "ID", "Payment Date", "Amount (₹)", "Next Due", "Note"
        ])
        self._history_table.setAlternatingRowColors(True)
        self._history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self._history_table.setShowGrid(False)
        self._history_table.setColumnWidth(0, 40)
        self._history_table.setColumnWidth(1, 130)
        self._history_table.setColumnWidth(2, 110)
        self._history_table.setColumnWidth(3, 130)
        right_layout.addWidget(self._history_table)

        delete_row = QHBoxLayout()
        delete_row.addStretch()
        del_btn = QPushButton("🗑️ Delete Selected Payment")
        del_btn.setObjectName("btn_danger")
        del_btn.clicked.connect(self._delete_payment)
        delete_row.addWidget(del_btn)
        right_layout.addLayout(delete_row)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([340, 660])
        root.addWidget(splitter)

    def refresh(self):
        self._load_students()

    def _load_students(self):
        search = self._search.text().strip() if hasattr(self, "_search") else ""
        students = db.get_all_students(search)
        self._student_table.setRowCount(len(students))
        for row, s in enumerate(students):
            self._student_table.setRowHeight(row, 38)
            status = db.get_payment_status(s)
            status_color = STATUS_COLORS.get(status, SUCCESS)
            code = s.get("student_code") or ""
            label = f"{s['name']}  [{code}]" if code else s["name"]
            for col, text in enumerate([
                label,
                s["phone"],
                s.get("next_payment_date") or "–",
            ]):
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, s["id"])
                # colour every cell in the row based on payment status
                item.setForeground(QColor(status_color))
                self._student_table.setItem(row, col, item)

    def _on_student_selected(self):
        rows = self._student_table.selectedItems()
        if not rows:
            return
        student_id = self._student_table.item(self._student_table.currentRow(), 0).data(Qt.UserRole)
        self._selected_student = db.get_student(student_id)
        if not self._selected_student:
            return
        s = self._selected_student
        self._history_title.setText(f"Payment History – {s['name']}")
        nd = s.get("next_payment_date") or "–"
        fee = db.get_effective_fee(s)
        status = db.get_payment_status(s)
        status_color = STATUS_COLORS.get(status, SUCCESS)
        self._info_label.setText(
            f"📞 {s['phone']}  |  🎓 {s['student_type']}  |  "
            f"Fee: <b>₹{fee:,.0f}</b>  |  "
            f"Last Paid: {s.get('last_payment_date') or '–'}  |  "
            f"<span style='color:{status_color};'>Next Due: {nd}</span>"
        )
        self._pay_btn.setEnabled(True)
        self._wa_chat_btn.setEnabled(True)
        self._wa_btn.setEnabled(True)
        self._load_history()

    def _load_history(self):
        if not self._selected_student:
            return
        history = db.get_payment_history(self._selected_student["id"])
        self._history_table.setRowCount(len(history))
        for row, p in enumerate(history):
            self._history_table.setRowHeight(row, 38)
            for col, text in enumerate([
                str(p["id"]),
                p["payment_date"],
                f"₹ {p['amount']:.0f}",
                p["next_payment_date"],
                p.get("note") or "",
            ]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                self._history_table.setItem(row, col, item)

    def _record_payment(self):
        if not self._selected_student:
            return
        from ui.student_management import PaymentDialog
        dlg = PaymentDialog(self._selected_student, parent=self)
        if dlg.exec_():
            self._selected_student = db.get_student(self._selected_student["id"])
            self._load_history()
            self._load_students()
            self.data_changed.emit()

    def _open_wa_chat(self):
        if not self._selected_student:
            return
        try:
            from utils.whatsapp import open_whatsapp_chat
            open_whatsapp_chat(self._selected_student["phone"])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open chat:\n{e}")

    def _send_reminder(self):
        if not self._selected_student:
            return
        try:
            from utils.whatsapp import send_message, format_reminder_message
            tmpl = db.get_setting("whatsapp_reminder_message") or ""
            msg = format_reminder_message(tmpl, self._selected_student["name"])
            send_message(self._selected_student["phone"], msg)
            QMessageBox.information(
                self, "Reminder",
                f"WhatsApp reminder queued for {self._selected_student['name']}.\n"
                "WhatsApp Web will open shortly."
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not send message:\n{e}")

    def _delete_payment(self):
        row = self._history_table.currentRow()
        if row < 0:
            return
        pay_id = int(self._history_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, "Delete Payment", "Delete this payment record?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            db.delete_payment(pay_id)
            self._load_history()
            self.data_changed.emit()
