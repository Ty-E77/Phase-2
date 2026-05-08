"""
Module 8 Student Enrollment backend starter.

This file is intentionally procedural. It has functions and top-level
database code, but no classes yet. Students will first group related behavior
into an EnrollmentManager class, then separate service and database layers.

App idea:
    - a student opens a dashboard
    - the dashboard shows enrolled classes
    - the student enters an enrollment key to join another class
    - the database stores courses and enrollment records
    - a JSON snapshot is exported so students can inspect the seeded data

Focus:
    - student enrollment behavior
    - local SQLite database
    - enrollment keys
    - soft unenroll using status = "unenrolled"

Out of scope:
    - Streamlit UI
    - authentication/session state
    - caching
    - export formatting
    - production health checks

Run with:
    enrollment_starter.py
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional


DB_PATH = Path(__file__).with_name("student_enrollment_practice.db")
SNAPSHOT_PATH = Path(__file__).with_name("student_enrollment_snapshot.json")

CURRENT_STUDENT = {
    "user_id": "u100",
    "name": "Maya Patel",
    "email": "maya.patel@example.edu",
}

STATUS_ENROLLED = "enrolled"
STATUS_UNENROLLED = "unenrolled"

AVAILABLE_COURSE_KEYS = [
    {
        "course_id": "MISY350",
        "course_name": "Python for Business Analytics",
        "instructor": "Dr. Rivera",
        "enrollment_key": "MISY350-SPRING",
    },
    {
        "course_id": "DATA210",
        "course_name": "Data Storytelling",
        "instructor": "Prof. Morgan",
        "enrollment_key": "DATA210-SPRING",
    },
    {
        "course_id": "WEB220",
        "course_name": "Web Apps With Streamlit",
        "instructor": "Dr. Chen",
        "enrollment_key": "WEB220-SPRING",
    },
]

SAMPLE_ENROLLMENTS = [
    ("u100", "maya.patel@example.edu", "MISY350", STATUS_ENROLLED),
    ("u100", "maya.patel@example.edu", "DATA210", STATUS_UNENROLLED),
    ("u101", "alex@example.edu", "MISY350", STATUS_ENROLLED),
    ("u102", "blair@example.edu", "WEB220", STATUS_ENROLLED),
]


class EnrollmentDatabase:
    """SQLite database wrapper focused on queries and row results."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS courses (
                    course_id TEXT PRIMARY KEY,
                    course_name TEXT NOT NULL,
                    instructor TEXT NOT NULL,
                    enrollment_key TEXT NOT NULL UNIQUE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS enrollments (
                    enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    course_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'enrolled',
                    enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, course_id),
                    FOREIGN KEY(course_id) REFERENCES courses(course_id)
                )
                """
            )

    def seed_sample_data(self) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR IGNORE INTO courses (
                    course_id, course_name, instructor, enrollment_key
                )
                VALUES (?, ?, ?, ?)
                """,
                [
                    (
                        course["course_id"],
                        course["course_name"],
                        course["instructor"],
                        course["enrollment_key"],
                    )
                    for course in AVAILABLE_COURSE_KEYS
                ],
            )
            connection.executemany(
                """
                INSERT OR IGNORE INTO enrollments (user_id, email, course_id, status)
                VALUES (?, ?, ?, ?)
                """,
                SAMPLE_ENROLLMENTS,
            )

    @staticmethod
    def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]

    def get_available_course_keys(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT course_id, course_name, instructor, enrollment_key
                FROM courses
                ORDER BY course_id
                """
            ).fetchall()

        return self.rows_to_dicts(rows)

    def get_course_by_key(self, enrollment_key: str) -> Optional[dict[str, Any]]:
        if not enrollment_key:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT course_id, course_name, instructor, enrollment_key
                FROM courses
                WHERE enrollment_key = ?
                """,
                (enrollment_key,),
            ).fetchone()

        return dict(row) if row else None

    def get_student_enrollments(self, user_id: str, status: str) -> list[dict[str, Any]]:
        if not user_id:
            return []

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.enrollment_id,
                    e.user_id,
                    e.email,
                    e.course_id,
                    c.course_name,
                    c.instructor,
                    e.status,
                    e.enrolled_at
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                WHERE e.user_id = ? AND e.status = ?
                ORDER BY c.course_id
                """,
                (user_id, status),
            ).fetchall()

        return self.rows_to_dicts(rows)

    def get_student_enrollment_history(self, user_id: str) -> list[dict[str, Any]]:
        if not user_id:
            return []

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.enrollment_id,
                    e.user_id,
                    e.email,
                    e.course_id,
                    c.course_name,
                    c.instructor,
                    e.status,
                    e.enrolled_at
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                WHERE e.user_id = ?
                ORDER BY c.course_id
                """,
                (user_id,),
            ).fetchall()

        return self.rows_to_dicts(rows)

    def get_student_course_record(self, user_id: str, course_id: str) -> Optional[dict[str, Any]]:
        if not user_id or not course_id:
            return None

        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT enrollment_id, user_id, email, course_id, status, enrolled_at
                FROM enrollments
                WHERE user_id = ? AND course_id = ?
                """,
                (user_id, course_id),
            ).fetchone()

        return dict(row) if row else None

    def insert_or_update_enrollment(self, user_id: str, email: str, course_id: str, status: str) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO enrollments (user_id, email, course_id, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, course_id)
                DO UPDATE SET
                    email = excluded.email,
                    status = excluded.status,
                    enrolled_at = CURRENT_TIMESTAMP
                """,
                (user_id, email, course_id, status),
            )

    def update_enrollment_status(self, user_id: str, course_id: str, status: str) -> bool:
        if not user_id or not course_id:
            return False

        with self.connect() as connection:
            cursor = connection.execute(
                """
                UPDATE enrollments
                SET status = ?
                WHERE user_id = ? AND course_id = ?
                """,
                (status, user_id, course_id),
            )

        return cursor.rowcount > 0

    def get_all_enrollment_records(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    e.enrollment_id,
                    e.user_id,
                    e.email,
                    e.course_id,
                    c.course_name,
                    c.instructor,
                    e.status,
                    e.enrolled_at
                FROM enrollments e
                JOIN courses c ON c.course_id = e.course_id
                ORDER BY e.user_id, e.course_id
                """
            ).fetchall()

        return self.rows_to_dicts(rows)


# Business rules live in the service layer


class EnrollmentService:
    """Business rules: validation, enrollment-key handling, summaries, and soft-unenroll."""

    def __init__(
        self,
        db: EnrollmentDatabase,
        current_student: dict[str, Any],
        status_enrolled: str = STATUS_ENROLLED,
        status_unenrolled: str = STATUS_UNENROLLED,
    ) -> None:
        self.db = db
        self.current_student = current_student
        self.status_enrolled = status_enrolled
        self.status_unenrolled = status_unenrolled

    def _normalize_key(self, enrollment_key: str) -> Optional[str]:
        if not enrollment_key:
            return None
        return enrollment_key.strip().upper()

    def enroll_with_key(self, user_id: str, email: str, enrollment_key: str) -> Optional[dict[str, Any]]:
        if not user_id or not email or "@" not in email or not enrollment_key:
            return None

        normalized = self._normalize_key(enrollment_key)
        if not normalized:
            return None

        course = self.db.get_course_by_key(normalized)
        if not course:
            return None

        self.db.insert_or_update_enrollment(user_id, email, course["course_id"], self.status_enrolled)
        return self.db.get_student_course_record(user_id, course["course_id"])

    def soft_unenroll_student(self, user_id: str, course_id: str) -> bool:
        return self.db.update_enrollment_status(user_id, course_id, self.status_unenrolled)

    def get_student_summary(self, user_id: str) -> dict[str, int]:
        summary = {"total_records": 0, self.status_enrolled: 0, self.status_unenrolled: 0}

        for record in self.db.get_student_enrollment_history(user_id):
            summary["total_records"] += 1
            status = record["status"]
            if status in summary:
                summary[status] += 1

        return summary

    # UI-friendly read-only wrappers (service should be the UI's only backend)
    def get_available_course_keys(self) -> list[dict[str, Any]]:
        return self.db.get_available_course_keys()

    def get_enrolled_classes(self, user_id: str) -> list[dict[str, Any]]:
        return self.db.get_student_enrollments(user_id, self.status_enrolled)

    def get_student_course_record(self, user_id: str, course_id: str) -> Optional[dict[str, Any]]:
        return self.db.get_student_course_record(user_id, course_id)


def export_database_snapshot(db: EnrollmentDatabase, path: Path = SNAPSHOT_PATH) -> None:
    snapshot = {
        "current_student": CURRENT_STUDENT,
        "available_course_keys": db.get_available_course_keys(),
        "enrollment_table": db.get_all_enrollment_records(),
    }
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def main() -> None:
    """Small terminal runner for checking behavior before the UI exists."""
    db = EnrollmentDatabase()
    db.create_tables()
    db.seed_sample_data()

    service = EnrollmentService(db, CURRENT_STUDENT)

    user_id = CURRENT_STUDENT["user_id"]
    email = CURRENT_STUDENT["email"]

    print("Current student:")
    print(CURRENT_STUDENT)

    print("\nAvailable enrollment keys:")
    print(db.get_available_course_keys())

    print("\nInitial enrolled classes:")
    print(db.get_student_enrollments(user_id, STATUS_ENROLLED))

    print("\nStudent enters key DATA210-SPRING:")
    print(service.enroll_with_key(user_id, email, "DATA210-SPRING"))

    print("\nUpdated enrolled classes:")
    print(db.get_student_enrollments(user_id, STATUS_ENROLLED))

    print("\nStudent summary:")
    print(service.get_student_summary(user_id))

    export_database_snapshot(db)
    print(f"\nDatabase snapshot written to: {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
