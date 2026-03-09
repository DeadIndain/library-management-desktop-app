"""
Application-wide color palette and stylesheet constants.
"""

# ── Palette ───────────────────────────────────────────────────────────────────
BG_DARK      = "#0F0F1A"
BG_PANEL     = "#1A1A2E"
BG_CARD      = "#16213E"
BG_HOVER     = "#0F3460"
ACCENT       = "#E94560"
ACCENT2      = "#533483"
TEXT_PRIMARY = "#EAEAEA"
TEXT_SECONDARY = "#A0A0B0"
TEXT_MUTED   = "#606070"
SUCCESS      = "#27AE60"
WARNING      = "#F39C12"
DANGER       = "#E74C3C"
INFO         = "#3498DB"
PURPLE       = "#9B59B6"

# Seat colors
SEAT_AVAILABLE = "#27AE60"
SEAT_OCCUPIED  = "#E74C3C"
SEAT_WOMEN     = "#8E44AD"
SEAT_SELECTED  = "#F39C12"

APP_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}

QFrame#sidebar {{
    background-color: {BG_PANEL};
    border-right: 2px solid {BG_HOVER};
}}

QPushButton {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}}
QPushButton:hover {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: #C0392B;
}}
QPushButton#btn_primary {{
    background-color: {ACCENT};
    border-color: {ACCENT};
    font-weight: bold;
}}
QPushButton#btn_primary:hover {{
    background-color: #C0392B;
}}
QPushButton#btn_success {{
    background-color: {SUCCESS};
    border-color: {SUCCESS};
    color: white;
    font-weight: bold;
}}
QPushButton#btn_success:hover {{
    background-color: #1E8449;
}}
QPushButton#btn_danger {{
    background-color: {DANGER};
    border-color: {DANGER};
    color: white;
    font-weight: bold;
}}
QPushButton#btn_danger:hover {{
    background-color: #A93226;
}}
QPushButton#btn_warning {{
    background-color: {WARNING};
    border-color: {WARNING};
    color: white;
    font-weight: bold;
}}
QPushButton#btn_warning:hover {{
    background-color: #D68910;
}}
QPushButton#nav_btn {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    color: {TEXT_SECONDARY};
    text-align: left;
    padding: 12px 20px;
    font-size: 14px;
}}
QPushButton#nav_btn:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QPushButton#nav_btn_active {{
    background-color: {ACCENT};
    border: none;
    border-radius: 8px;
    color: white;
    text-align: left;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: bold;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {ACCENT};
}}

QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 13px;
    min-width: 120px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QComboBox:hover {{
    border-color: {ACCENT};
}}
QComboBox:on {{
    border-color: {ACCENT};
}}
QComboBox:!editable, QComboBox::drop-down:editable {{
    background-color: {BG_CARD};
}}
QComboBox:!editable:on, QComboBox::drop-down:editable:on {{
    background-color: {BG_HOVER};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    background-color: transparent;
    subcontrol-origin: padding;
    subcontrol-position: top right;
}}
QComboBox::down-arrow {{
    image: none;
    width: 10px;
    height: 10px;
    background-color: {TEXT_SECONDARY};
    border-radius: 2px;
}}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BG_HOVER};
    outline: none;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QComboBox QAbstractItemView::item {{
    color: {TEXT_PRIMARY};
    background-color: {BG_PANEL};
    padding: 6px 10px;
    min-height: 24px;
    border: none;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {ACCENT};
    color: white;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
/* Explicit styling for Windows dropdown compatibility */
QComboBox QListView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BG_HOVER};
    outline: none;
}}
QComboBox QListView::item {{
    color: {TEXT_PRIMARY};
    background-color: {BG_PANEL};
    padding: 6px 10px;
}}
QComboBox QListView::item:selected {{
    background-color: {ACCENT};
    color: white;
}}
QComboBox QListView::item:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}

QDateEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QDateEdit:focus {{ border-color: {ACCENT}; }}
QDateEdit::drop-down {{
    border: none;
    width: 24px;
    background-color: {BG_HOVER};
    subcontrol-origin: padding;
    subcontrol-position: top right;
}}
QDateEdit::down-arrow {{
    image: none;
    width: 8px;
    height: 8px;
    background-color: {TEXT_SECONDARY};
    border-radius: 2px;
}}
QCalendarWidget {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
}}
QCalendarWidget QWidget {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
}}
QCalendarWidget QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    selection-background-color: {ACCENT};
    selection-color: white;
}}

QLabel {{
    color: {TEXT_PRIMARY};
    background-color: transparent;
}}
QLabel#section_title {{
    font-size: 20px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
}}
QLabel#card_value {{
    font-size: 28px;
    font-weight: bold;
    color: {ACCENT};
}}
QLabel#card_label {{
    font-size: 12px;
    color: {TEXT_SECONDARY};
}}
QLabel#app_title {{
    font-size: 16px;
    font-weight: bold;
    color: {ACCENT};
}}

QTableWidget {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    gridline-color: #2A2A4A;
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    alternate-background-color: {BG_PANEL};
}}
QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid #2A2A4A;
}}
QTableWidget::item:selected {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}
QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {ACCENT};
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
}}
QHeaderView::section:horizontal {{
    border-right: 1px solid #2A2A4A;
}}

QScrollBar:vertical {{
    background-color: {BG_DARK};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background-color: #3A3A5A;
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {BG_DARK};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background-color: #3A3A5A;
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {ACCENT};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QFrame#card {{
    background-color: {BG_CARD};
    border: 1px solid #2A2A4A;
    border-radius: 10px;
}}
QFrame#card_accent {{
    background-color: {BG_CARD};
    border: 1px solid {ACCENT};
    border-radius: 10px;
}}

QGroupBox {{
    color: {TEXT_SECONDARY};
    border: 1px solid #2A2A4A;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {ACCENT};
    background-color: {BG_DARK};
}}

QSpinBox, QDoubleSpinBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {ACCENT}; }}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background-color: {BG_HOVER};
    border: none;
    width: 18px;
    border-top-right-radius: 6px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {BG_HOVER};
    border: none;
    width: 18px;
    border-bottom-right-radius: 6px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {ACCENT};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    width: 6px;
    height: 6px;
    background-color: {TEXT_PRIMARY};
    border-radius: 1px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    width: 6px;
    height: 6px;
    background-color: {TEXT_PRIMARY};
    border-radius: 1px;
}}

QTimeEdit {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: {ACCENT};
    selection-color: white;
}}
QTimeEdit:focus {{ border-color: {ACCENT}; }}
QTimeEdit::up-button {{
    background-color: {BG_HOVER};
    border: none;
    width: 18px;
    border-top-right-radius: 6px;
}}
QTimeEdit::down-button {{
    background-color: {BG_HOVER};
    border: none;
    width: 18px;
    border-bottom-right-radius: 6px;
}}
QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {{
    background-color: {ACCENT};
}}
QTimeEdit::up-arrow {{
    image: none;
    width: 6px;
    height: 6px;
    background-color: {TEXT_PRIMARY};
    border-radius: 1px;
}}
QTimeEdit::down-arrow {{
    image: none;
    width: 6px;
    height: 6px;
    background-color: {TEXT_PRIMARY};
    border-radius: 1px;
}}

QTabWidget::pane {{
    border: 1px solid #2A2A4A;
    border-radius: 6px;
    background-color: {BG_CARD};
    top: -1px;
}}
QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    border: none;
    padding: 10px 20px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {ACCENT};
    color: white;
}}
QTabBar::tab:hover {{
    background-color: {BG_HOVER};
    color: {TEXT_PRIMARY};
}}

QMessageBox {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
}}
QMessageBox QPushButton {{
    min-width: 80px;
}}

QToolTip {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {ACCENT};
    border-radius: 4px;
    padding: 4px 8px;
}}

QCheckBox {{
    color: {TEXT_PRIMARY};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #2A2A4A;
    background-color: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}

QDialog {{
    background-color: {BG_PANEL};
}}

QSplitter::handle {{
    background-color: #2A2A4A;
    width: 2px;
}}
"""
