from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-auth-unit-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import (
    SignupRequest,
    authenticate_user,
    create_access_token,
    create_user,
    decode_jwt,
    encode_jwt,
    get_or_create_demo_user,
    hash_password,
    normalize_email,
    verify_password,
)
from app.models import Base, Student, Teacher


class AuthTest(TestCase):
    def setUp(self) -> None:
        os.environ["JWT_SECRET"] = "test-secret-for-auth-unit-tests"
        os.environ["AUTH_COOKIE_SECURE"] = "0"
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.db: Session = self.session_factory()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_password_hash_round_trip(self) -> None:
        password_hash = hash_password("correct horse battery staple")

        self.assertTrue(verify_password("correct horse battery staple", password_hash))
        self.assertFalse(verify_password("wrong password", password_hash))

    def test_jwt_round_trip_and_expiry(self) -> None:
        token = encode_jwt({"sub": "123", "role": "admin", "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp())})
        payload = decode_jwt(token)

        self.assertEqual(payload["sub"], "123")
        self.assertEqual(payload["role"], "admin")

        expired = encode_jwt({"sub": "123", "role": "admin", "exp": int((datetime.now(UTC) - timedelta(minutes=5)).timestamp())})
        with self.assertRaises(HTTPException):
            decode_jwt(expired)

    def test_create_teacher_student_and_admin_users(self) -> None:
        teacher = create_user(
            self.db,
            SignupRequest(email="Teacher@Example.com", password="password123", role="teacher", name="Teacher One"),
        )
        student = create_user(
            self.db,
            SignupRequest(email="student@example.com", password="password123", role="student", name="Student One"),
        )
        admin = create_user(
            self.db,
            SignupRequest(email="admin@example.com", password="password123", role="admin", name="Admin One"),
        )

        self.assertEqual(teacher.email, "teacher@example.com")
        self.assertEqual(teacher.role, "teacher")
        self.assertIsNotNone(teacher.teacher_id)
        self.assertIsNone(teacher.student_id)
        self.assertEqual(student.role, "student")
        self.assertIsNotNone(student.student_id)
        self.assertIsNone(student.teacher_id)
        self.assertEqual(admin.role, "admin")
        self.assertIsNone(admin.teacher_id)
        self.assertIsNone(admin.student_id)

    def test_duplicate_email_is_rejected(self) -> None:
        payload = SignupRequest(email="dupe@example.com", password="password123", role="admin", name="Admin One")
        create_user(self.db, payload)

        with self.assertRaises(HTTPException):
            create_user(self.db, payload)

    def test_authenticate_user(self) -> None:
        create_user(self.db, SignupRequest(email="admin@example.com", password="password123", role="admin", name="Admin One"))

        self.assertIsNotNone(authenticate_user(self.db, "admin@example.com", "password123"))
        self.assertIsNone(authenticate_user(self.db, "admin@example.com", "badpassword"))

    def test_demo_users_link_to_seed_profiles(self) -> None:
        teacher = Teacher(name="Seed Teacher")
        student = Student(name="Seed Student")
        self.db.add_all([teacher, student])
        self.db.commit()

        demo_teacher = get_or_create_demo_user(self.db, "teacher")
        demo_student = get_or_create_demo_user(self.db, "student")

        self.assertEqual(demo_teacher.email, "demo.teacher@confusionlayer.local")
        self.assertEqual(demo_teacher.teacher_id, teacher.id)
        self.assertEqual(demo_student.email, "demo.student@confusionlayer.local")
        self.assertEqual(demo_student.student_id, student.id)

    def test_normalize_email(self) -> None:
        self.assertEqual(normalize_email("  USER@Example.COM "), "user@example.com")
