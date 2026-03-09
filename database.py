import sqlite3
import os
import sys
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

# When running as a PyInstaller frozen binary, keep the database next to the
# actual executable so data persists between launches (not in _MEIPASS temp dir).
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(_BASE_DIR, "library.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Settings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Seats table
    c.execute("""
        CREATE TABLE IF NOT EXISTS seats (
            seat_number INTEGER PRIMARY KEY,
            is_reserved_women INTEGER NOT NULL DEFAULT 0,
            student_id INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    # Students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_code TEXT UNIQUE,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT DEFAULT 'Male',
            student_type TEXT NOT NULL CHECK(student_type IN ('Full-time','Half-time')),
            shift TEXT,
            seat_number INTEGER,
            custom_fee REAL,
            join_date TEXT NOT NULL,
            last_payment_date TEXT,
            next_payment_date TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Payments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            next_payment_date TEXT NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    # Removed students table
    c.execute("""
        CREATE TABLE IF NOT EXISTS removed_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_id INTEGER,
            student_code TEXT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            gender TEXT DEFAULT 'Male',
            student_type TEXT NOT NULL,
            shift TEXT,
            seat_number INTEGER,
            custom_fee REAL,
            join_date TEXT,
            last_payment_date TEXT,
            next_payment_date TEXT,
            notes TEXT DEFAULT '',
            removed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            removal_reason TEXT DEFAULT ''
        )
    """)

    # Monthly stats snapshot table
    c.execute("""
        CREATE TABLE IF NOT EXISTS monthly_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            fulltime_count INTEGER DEFAULT 0,
            halftime_count INTEGER DEFAULT 0,
            male_count INTEGER DEFAULT 0,
            female_count INTEGER DEFAULT 0,
            other_count INTEGER DEFAULT 0,
            revenue_collected REAL DEFAULT 0.0,
            snapshot_date TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(year, month)
        )
    """)

    # Insert default settings
    defaults = {
        "monthly_fee": "500",
        "fulltime_fee": "600",
        "halftime_fee": "400",
        "total_seats": "69",
        "women_reserved_seats": "10",
        "opening_time": "06:00",
        "closing_time": "23:00",
        "morning_shift_start": "06:00",
        "morning_shift_end": "14:00",
        "evening_shift_start": "14:00",
        "evening_shift_end": "23:00",
        "enable_reminder_3day": "1",
        "enable_reminder_1day": "1",
        "whatsapp_reminder_message": (
            "Hello {name},\n\nYour study point fee is due today.\n"
            "Please pay your monthly fee to continue using your seat.\n\n"
            "नमस्ते {name},\n\nआज आपकी लाइब्रेरी फीस देय है।\n"
            "कृपया अपनी सीट जारी रखने के लिए आज भुगतान करें।"
        ),
        "whatsapp_reminder_3day_message": (
            "Hello {name},\n\nYour study point fee is due in 3 days ({due_date}).\n"
            "Please arrange your payment soon.\n\n"
            "नमस्ते {name},\n\nआपकी लाइब्रेरी फीस 3 दिनों में ({due_date}) देय है।"
        ),
        "whatsapp_reminder_1day_message": (
            "Hello {name},\n\nYour study point fee is due tomorrow ({due_date}).\n"
            "Please pay to avoid any interruption.\n\n"
            "नमस्ते {name},\n\nकल आपकी लाइब्रेरी फीस ({due_date}) देय है।"
        ),
        "whatsapp_removal_message": (
            "Hello {name},\n\nYour study point membership has ended. "
            "You are no longer registered.\n\n"
            "नमस्ते {name},\n\nआपकी लाइब्रेरी सदस्यता समाप्त हो गई है। "
            "अब आप पंजीकृत नहीं हैं।"
        ),
    }

    for key, value in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()

    # ── Migrate existing DB: add new columns if missing ───────────────────────
    _migrate_columns(conn)

    # Initialize seats if not already done
    total = int(get_setting("total_seats") or "69")
    women_count = int(get_setting("women_reserved_seats") or "10")
    _sync_seats(c, total, women_count)

    conn.commit()
    conn.close()


def _sync_seats(c, total_seats: int, women_reserved: int):
    """Ensure seats table matches total_seats and women_reserved counts."""
    existing = c.execute("SELECT MAX(seat_number) FROM seats").fetchone()[0] or 0

    # Add missing seats
    for i in range(existing + 1, total_seats + 1):
        c.execute("INSERT OR IGNORE INTO seats (seat_number, is_reserved_women) VALUES (?, 0)", (i,))

    # Remove extra seats (only if unoccupied)
    if existing > total_seats:
        c.execute(
            "DELETE FROM seats WHERE seat_number > ? AND student_id IS NULL",
            (total_seats,)
        )

    # Update women reservation: first `women_reserved` seats get flagged
    c.execute("UPDATE seats SET is_reserved_women = 0")
    c.execute(
        "UPDATE seats SET is_reserved_women = 1 WHERE seat_number <= ?",
        (women_reserved,)
    )


def _migrate_columns(conn):
    """Add any missing columns to support upgrades of existing databases."""
    existing = {
        row[1] for row in conn.execute("PRAGMA table_info(students)").fetchall()
    }
    migrations = [
        ("student_code", "TEXT"),
        ("gender",       "TEXT DEFAULT 'Male'"),
        ("custom_fee",   "REAL"),
    ]
    for col, typedef in migrations:
        if col not in existing:
            conn.execute(f"ALTER TABLE students ADD COLUMN {col} {typedef}")

    re_existing = {
        row[1] for row in conn.execute("PRAGMA table_info(removed_students)").fetchall()
    }
    re_migrations = [
        ("student_code", "TEXT"),
        ("gender",       "TEXT DEFAULT 'Male'"),
        ("custom_fee",   "REAL"),
    ]
    for col, typedef in re_migrations:
        if col not in re_existing:
            conn.execute(f"ALTER TABLE removed_students ADD COLUMN {col} {typedef}")

    conn.commit()


# ─── Settings ────────────────────────────────────────────────────────────────

def get_setting(key: str) -> Optional[str]:
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    if key in ("total_seats", "women_reserved_seats"):
        c = conn.cursor()
        total = int(get_setting("total_seats") or "69")
        women = int(get_setting("women_reserved_seats") or "10")
        _sync_seats(c, total, women)
        conn.commit()
    conn.close()


def get_all_settings() -> Dict[str, str]:
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    return {r["key"]: r["value"] for r in rows}


# ─── Seats ───────────────────────────────────────────────────────────────────

def get_all_seats() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.seat_number, s.is_reserved_women, s.student_id,
               st.name as student_name, st.student_type
        FROM seats s
        LEFT JOIN students st ON s.student_id = st.id
        ORDER BY s.seat_number
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def assign_seat(seat_number: int, student_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE seats SET student_id = ? WHERE seat_number = ?",
        (student_id, seat_number)
    )
    conn.execute(
        "UPDATE students SET seat_number = ? WHERE id = ?",
        (seat_number, student_id)
    )
    conn.commit()
    conn.close()


def free_seat(seat_number: int):
    conn = get_connection()
    conn.execute("UPDATE seats SET student_id = NULL WHERE seat_number = ?", (seat_number,))
    conn.commit()
    conn.close()


def get_available_seats() -> List[int]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT seat_number FROM seats WHERE student_id IS NULL ORDER BY seat_number"
    ).fetchall()
    conn.close()
    return [r["seat_number"] for r in rows]


def is_seat_taken(seat_number: int, exclude_student_id: int = None) -> bool:
    """Return True if seat is already assigned to another student."""
    conn = get_connection()
    row = conn.execute("SELECT student_id FROM seats WHERE seat_number = ?", (seat_number,)).fetchone()
    conn.close()
    if not row:
        return False
    sid = row["student_id"]
    if sid is None:
        return False
    if exclude_student_id and sid == exclude_student_id:
        return False
    return True


def generate_student_code() -> str:
    """Generate next sequential code like SP001, SP002 …"""
    conn = get_connection()
    row = conn.execute(
        "SELECT student_code FROM students WHERE student_code IS NOT NULL "
        "ORDER BY student_code DESC LIMIT 1"
    ).fetchone()
    conn.close()
    if row and row["student_code"]:
        try:
            num = int(row["student_code"][2:]) + 1
        except (ValueError, IndexError):
            num = 1
    else:
        num = 1
    return f"SP{num:03d}"


# ─── Students ────────────────────────────────────────────────────────────────

def add_student(data: Dict[str, Any]) -> int:
    conn = get_connection()
    c = conn.cursor()
    code = data.get("student_code") or generate_student_code()
    c.execute("""
        INSERT INTO students
            (student_code, name, phone, gender, student_type, shift, seat_number,
             custom_fee, join_date, last_payment_date, next_payment_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        data["name"], data["phone"],
        data.get("gender", "Male"),
        data["student_type"],
        data.get("shift"), data.get("seat_number"),
        data.get("custom_fee"),
        data["join_date"], data.get("last_payment_date"),
        data.get("next_payment_date"), data.get("notes", "")
    ))
    student_id = c.lastrowid
    if data.get("seat_number") and data["student_type"] == "Full-time":
        c.execute(
            "UPDATE seats SET student_id = ? WHERE seat_number = ?",
            (student_id, data["seat_number"])
        )
    
    # Record initial payment if last_payment_date is provided
    if data.get("last_payment_date") and data.get("next_payment_date"):
        # Calculate effective fee for this student
        fee = data.get("custom_fee")
        if fee is None:
            if data["student_type"] == "Full-time":
                fee = float(get_setting("fulltime_fee") or "600")
            else:
                fee = float(get_setting("halftime_fee") or "400")
        else:
            fee = float(fee)
        
        # Record the initial payment
        c.execute("""
            INSERT INTO payments (student_id, amount, payment_date, next_payment_date, note)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, fee, data["last_payment_date"], data["next_payment_date"], "Initial registration payment"))
    
    conn.commit()
    conn.close()
    return student_id


def update_student(student_id: int, data: Dict[str, Any]):
    conn = get_connection()
    old = conn.execute("SELECT seat_number FROM students WHERE id = ?", (student_id,)).fetchone()
    if old and old["seat_number"] and old["seat_number"] != data.get("seat_number"):
        conn.execute("UPDATE seats SET student_id = NULL WHERE seat_number = ?", (old["seat_number"],))

    conn.execute("""
        UPDATE students SET
            name = ?, phone = ?, gender = ?, student_type = ?, shift = ?,
            seat_number = ?, custom_fee = ?, join_date = ?, last_payment_date = ?,
            next_payment_date = ?, notes = ?
        WHERE id = ?
    """, (
        data["name"], data["phone"],
        data.get("gender", "Male"),
        data["student_type"],
        data.get("shift"), data.get("seat_number"),
        data.get("custom_fee"),
        data["join_date"], data.get("last_payment_date"),
        data.get("next_payment_date"), data.get("notes", ""),
        student_id
    ))
    if data.get("seat_number") and data["student_type"] == "Full-time":
        conn.execute(
            "UPDATE seats SET student_id = ? WHERE seat_number = ?",
            (student_id, data["seat_number"])
        )
    conn.commit()
    conn.close()


def remove_student(student_id: int, reason: str = "") -> Optional[str]:
    """Archive student, free seat, and return phone number."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if not row:
        conn.close()
        return None
    conn.execute("""
        INSERT INTO removed_students
            (original_id, student_code, name, phone, gender, student_type, shift,
             seat_number, custom_fee, join_date, last_payment_date, next_payment_date,
             notes, removal_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        student_id, row["student_code"], row["name"], row["phone"],
        row["gender"] if "gender" in row.keys() else "Male",
        row["student_type"], row["shift"], row["seat_number"],
        row["custom_fee"] if "custom_fee" in row.keys() else None,
        row["join_date"], row["last_payment_date"], row["next_payment_date"],
        row["notes"], reason
    ))
    if row["seat_number"]:
        conn.execute("UPDATE seats SET student_id = NULL WHERE seat_number = ?", (row["seat_number"],))
    conn.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    phone = row["phone"]
    conn.commit()
    conn.close()
    return phone


def get_all_students(search: str = "") -> List[Dict]:
    conn = get_connection()
    if search:
        like = f"%{search}%"
        rows = conn.execute("""
            SELECT * FROM students
            WHERE name LIKE ? OR phone LIKE ? OR CAST(seat_number AS TEXT) LIKE ?
            ORDER BY name
        """, (like, like, like)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student(student_id: int) -> Optional[Dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_overdue_students() -> List[Dict]:
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM students
        WHERE next_payment_date IS NOT NULL AND next_payment_date <= ?
        ORDER BY next_payment_date
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_due_today_students() -> List[Dict]:
    today = date.today().isoformat()
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM students
        WHERE next_payment_date = ?
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Payments ────────────────────────────────────────────────────────────────

def record_payment(student_id: int, amount: float, payment_date: str,
                   next_date: str, note: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO payments (student_id, amount, payment_date, next_payment_date, note)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, amount, payment_date, next_date, note))
    conn.execute("""
        UPDATE students SET last_payment_date = ?, next_payment_date = ?
        WHERE id = ?
    """, (payment_date, next_date, student_id))
    conn.commit()
    conn.close()


def get_payment_history(student_id: int) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM payments WHERE student_id = ?
        ORDER BY payment_date DESC
    """, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_payment(payment_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()


# ─── Removed Students ────────────────────────────────────────────────────────

def get_removed_students(search: str = "") -> List[Dict]:
    conn = get_connection()
    if search:
        like = f"%{search}%"
        rows = conn.execute("""
            SELECT * FROM removed_students
            WHERE name LIKE ? OR phone LIKE ?
            ORDER BY removed_at DESC
        """, (like, like)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM removed_students ORDER BY removed_at DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_removed_student_record(record_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM removed_students WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


# ─── Dashboard Stats ─────────────────────────────────────────────────────────

def get_dashboard_stats() -> Dict[str, Any]:
    conn = get_connection()
    total_seats = int(conn.execute("SELECT COUNT(*) FROM seats").fetchone()[0])
    occupied = int(conn.execute("SELECT COUNT(*) FROM seats WHERE student_id IS NOT NULL").fetchone()[0])
    reserved = int(conn.execute("SELECT COUNT(*) FROM seats WHERE is_reserved_women = 1").fetchone()[0])
    available = total_seats - occupied
    fulltime_count = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE student_type = 'Full-time'"
    ).fetchone()[0])
    halftime_count = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE student_type = 'Half-time'"
    ).fetchone()[0])
    male_count = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE gender = 'Male'"
    ).fetchone()[0])
    female_count = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE gender = 'Female'"
    ).fetchone()[0])
    today = date.today().isoformat()
    due_today = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE next_payment_date = ?", (today,)
    ).fetchone()[0])
    overdue = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE next_payment_date < ?", (today,)
    ).fetchone()[0])

    # Revenue: current month
    first_of_month = date.today().replace(day=1).isoformat()
    rev_row = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_date >= ?",
        (first_of_month,)
    ).fetchone()
    revenue_this_month = float(rev_row[0])

    # Revenue: current year
    first_of_year = date.today().replace(month=1, day=1).isoformat()
    rev_year = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_date >= ?",
        (first_of_year,)
    ).fetchone()
    revenue_this_year = float(rev_year[0])

    # Outstanding: sum of fees for all students who are overdue (estimate)
    overdue_students = conn.execute(
        "SELECT COUNT(*) FROM students WHERE next_payment_date < ?", (today,)
    ).fetchone()[0]
    fulltime_fee = float(get_setting("fulltime_fee") or "600")
    halftime_fee = float(get_setting("halftime_fee") or "400")
    # Rough estimate: use average fee
    avg_fee = (fulltime_fee + halftime_fee) / 2
    outstanding_estimate = float(overdue_students) * avg_fee

    conn.close()
    return {
        "total_seats": total_seats,
        "occupied_seats": occupied,
        "available_seats": available,
        "reserved_seats": reserved,
        "fulltime_students": fulltime_count,
        "halftime_students": halftime_count,
        "male_students": male_count,
        "female_students": female_count,
        "due_today": due_today,
        "overdue": overdue,
        "revenue_this_month": revenue_this_month,
        "revenue_this_year": revenue_this_year,
        "outstanding_estimate": outstanding_estimate,
    }


# ─── Student Reminder Queries ─────────────────────────────────────────────────

def get_students_due_in_days(days: int) -> List[Dict]:
    """Return students whose next_payment_date is exactly `days` from today."""
    target = (date.today() + timedelta(days=days)).isoformat()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM students WHERE next_payment_date = ?", (target,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_payment_status(student: Dict) -> str:
    """Return 'paid', 'due_soon', 'due_today', or 'overdue'."""
    npd = student.get("next_payment_date")
    if not npd:
        return "paid"
    today = date.today()
    try:
        nd = date.fromisoformat(npd)
    except ValueError:
        return "paid"
    diff = (nd - today).days
    if diff > 3:
        return "paid"
    if diff > 0:
        return "due_soon"   # 1–3 days away
    if diff == 0:
        return "due_today"
    return "overdue"


def get_effective_fee(student: Dict) -> float:
    """Return the fee to charge this student (custom > type > default)."""
    if student.get("custom_fee") is not None:
        return float(student["custom_fee"])
    if student.get("student_type") == "Full-time":
        return float(get_setting("fulltime_fee") or "600")
    return float(get_setting("halftime_fee") or "400")


# ─── Monthly Stats ────────────────────────────────────────────────────────────

def store_monthly_snapshot():
    """Save a snapshot of the current month's stats (upsert)."""
    today = date.today()
    conn = get_connection()
    ft = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE student_type='Full-time'"
    ).fetchone()[0])
    ht = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE student_type='Half-time'"
    ).fetchone()[0])
    male = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE gender='Male'"
    ).fetchone()[0])
    female = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE gender='Female'"
    ).fetchone()[0])
    other = int(conn.execute(
        "SELECT COUNT(*) FROM students WHERE gender NOT IN ('Male','Female')"
    ).fetchone()[0])
    first_of_month = today.replace(day=1).isoformat()
    rev = float(conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM payments WHERE payment_date >= ?",
        (first_of_month,)
    ).fetchone()[0])
    conn.execute("""
        INSERT INTO monthly_stats
            (year, month, fulltime_count, halftime_count, male_count, female_count,
             other_count, revenue_collected, snapshot_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(year, month) DO UPDATE SET
            fulltime_count = excluded.fulltime_count,
            halftime_count = excluded.halftime_count,
            male_count     = excluded.male_count,
            female_count   = excluded.female_count,
            other_count    = excluded.other_count,
            revenue_collected = excluded.revenue_collected,
            snapshot_date  = excluded.snapshot_date
    """, (today.year, today.month, ft, ht, male, female, other, rev, today.isoformat()))
    conn.commit()
    conn.close()


def get_monthly_stats_history(limit: int = 12) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM monthly_stats ORDER BY year DESC, month DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_revenue_by_month(year: int = None) -> List[Dict]:
    """Return monthly revenue breakdown for a given year."""
    if year is None:
        year = date.today().year
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            SUBSTR(payment_date, 1, 7) as ym,
            COALESCE(SUM(amount), 0) as total,
            COUNT(*) as count
        FROM payments
        WHERE payment_date LIKE ?
        GROUP BY ym ORDER BY ym
    """, (f"{year}-%",)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Export ──────────────────────────────────────────────────────────────────

def export_students_data() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM students ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]

