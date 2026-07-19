from __future__ import annotations

import os
from unittest import TestCase

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-curriculum-tests")
os.environ.setdefault("AUTH_COOKIE_SECURE", "0")

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import SignupRequest, create_user
from app.curriculum import DraftChapter, commit_subject_tree, structure_from_headings
from app.main import (
    ChapterCreateRequest,
    ConceptCreateRequest,
    ImportCommitRequest,
    SubjectCreateRequest,
    add_curriculum_chapter,
    add_curriculum_concept,
    commit_curriculum_import,
    create_curriculum_subject,
    get_curriculum_subject,
    list_curriculum_subjects,
)
from app.models import Base, Chapter, ChapterUnlock, Classroom, ClassroomStudent, Concept, Organization, Subject, Teacher, User


class CurriculumStructureTest(TestCase):
    def test_chapter_and_topic_grouping(self) -> None:
        tree = structure_from_headings(["Chapter 1: Matter", "States of matter", "Changes", "Chapter 2: Atoms", "Electrons"])
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0].title, "Chapter 1: Matter")
        self.assertEqual(tree[0].topics, ["States of matter", "Changes"])
        self.assertEqual(tree[1].title, "Chapter 2: Atoms")
        self.assertEqual(tree[1].topics, ["Electrons"])

    def test_numbered_headings_are_chapters(self) -> None:
        tree = structure_from_headings(["1. Acids", "2. Bases", "3. Salts"])
        self.assertEqual([c.title for c in tree], ["1. Acids", "2. Bases", "3. Salts"])
        self.assertTrue(all(not c.topics for c in tree))

    def test_no_chapter_markers_each_heading_is_a_chapter(self) -> None:
        tree = structure_from_headings(["Photosynthesis", "Respiration", "Transport"])
        self.assertEqual([c.title for c in tree], ["Photosynthesis", "Respiration", "Transport"])

    def test_blank_headings_ignored(self) -> None:
        self.assertEqual(structure_from_headings(["", "   ", "Chapter 1"]), structure_from_headings(["Chapter 1"]))


class CurriculumApiTest(TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.db: Session = sessionmaker(bind=self.engine)()
        self.org_a = Organization(name="Org A", slug="org-a", segment="school")
        self.org_b = Organization(name="Org B", slug="org-b", segment="school")
        self.individual_org = Organization(name="Solo", slug="solo", segment="individual")
        self.db.add_all([self.org_a, self.org_b, self.individual_org])
        # a shared (org_id null) subject that should be read-only
        self.shared = Subject(org_id=None, name="Shared Science", board="CBSE", class_level="10")
        self.db.add(self.shared)
        self.db.commit()

        self.owner = create_user(self.db, SignupRequest(email="owner@a.test", password="password123", role="teacher", name="Owner"))
        self.owner.role = "owner"
        self.owner.org_id = self.org_a.id
        self.student = create_user(self.db, SignupRequest(email="s@a.test", password="password123", role="student", name="S"))
        self.student.org_id = self.org_a.id
        self.other_owner = create_user(self.db, SignupRequest(email="owner@b.test", password="password123", role="teacher", name="Other"))
        self.other_owner.role = "owner"
        self.other_owner.org_id = self.org_b.id
        self.individual_student = create_user(self.db, SignupRequest(email="solo@solo.test", password="password123", role="student", name="Solo Learner"))
        self.individual_student.org_id = self.individual_org.id
        self.individual_subject = Subject(org_id=self.individual_org.id, name="Self Seed", board="CBSE", class_level="10")
        self.individual_teacher = Teacher(name="Self Study Coach")
        self.db.add_all([self.individual_subject, self.individual_teacher])
        self.db.flush()
        self.individual_classroom = Classroom(
            org_id=self.individual_org.id,
            name="Self Study Plan",
            teacher_id=self.individual_teacher.id,
            subject_id=self.individual_subject.id,
        )
        self.db.add(self.individual_classroom)
        self.db.flush()
        self.db.add(ClassroomStudent(classroom_id=self.individual_classroom.id, student_id=self.individual_student.student_id))
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def test_manual_authoring_flow(self) -> None:
        subject = create_curriculum_subject(SubjectCreateRequest(name="My Science"), current_user=self.owner, db=self.db)
        self.assertFalse(subject.shared)
        chapter = add_curriculum_chapter(subject.id, ChapterCreateRequest(title="Chemical Reactions"), current_user=self.owner, db=self.db)
        add_curriculum_concept(chapter.id, ConceptCreateRequest(title="Balancing"), current_user=self.owner, db=self.db)

        tree = get_curriculum_subject(subject.id, current_user=self.owner, db=self.db)
        self.assertEqual(tree.chapters[0].title, "Chemical Reactions")
        self.assertEqual(tree.chapters[0].concepts[0].title, "Balancing")

    def test_students_cannot_manage_curriculum(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            create_curriculum_subject(SubjectCreateRequest(name="X"), current_user=self.student, db=self.db)
        self.assertEqual(exc.exception.status_code, 403)

    def test_individual_student_can_manage_own_curriculum(self) -> None:
        subject = create_curriculum_subject(SubjectCreateRequest(name="Self Science"), current_user=self.individual_student, db=self.db)
        self.assertFalse(subject.shared)
        self.db.refresh(self.individual_classroom)
        self.assertEqual(self.individual_classroom.subject_id, subject.id)

        chapter = add_curriculum_chapter(subject.id, ChapterCreateRequest(title="Trigonometry"), current_user=self.individual_student, db=self.db)
        add_curriculum_concept(chapter.id, ConceptCreateRequest(title="Sine and cosine"), current_user=self.individual_student, db=self.db)

        unlock = self.db.scalar(
            select(ChapterUnlock).where(
                ChapterUnlock.classroom_id == self.individual_classroom.id,
                ChapterUnlock.chapter_id == chapter.id,
            )
        )
        self.assertIsNotNone(unlock)
        tree = get_curriculum_subject(subject.id, current_user=self.individual_student, db=self.db)
        self.assertEqual(tree.chapters[0].concepts[0].title, "Sine and cosine")

    def test_cannot_edit_shared_or_other_org_subject(self) -> None:
        with self.assertRaises(HTTPException) as shared_exc:
            add_curriculum_chapter(self.shared.id, ChapterCreateRequest(title="Nope"), current_user=self.owner, db=self.db)
        self.assertEqual(shared_exc.exception.status_code, 403)

        owned = create_curriculum_subject(SubjectCreateRequest(name="A Subject"), current_user=self.owner, db=self.db)
        with self.assertRaises(HTTPException) as cross_exc:
            add_curriculum_chapter(owned.id, ChapterCreateRequest(title="Nope"), current_user=self.other_owner, db=self.db)
        self.assertEqual(cross_exc.exception.status_code, 403)

    def test_list_includes_shared_and_own_not_other_org(self) -> None:
        create_curriculum_subject(SubjectCreateRequest(name="A Owned"), current_user=self.owner, db=self.db)
        create_curriculum_subject(SubjectCreateRequest(name="B Owned"), current_user=self.other_owner, db=self.db)
        names = {s.name for s in list_curriculum_subjects(current_user=self.owner, db=self.db)}
        self.assertIn("Shared Science", names)
        self.assertIn("A Owned", names)
        self.assertNotIn("B Owned", names)

    def test_import_commit_creates_org_scoped_tree(self) -> None:
        response = commit_curriculum_import(
            ImportCommitRequest(
                name="Imported Science",
                chapters=[DraftChapterModel_data("Chapter 1", ["T1", "T2"]), DraftChapterModel_data("Chapter 2", [])],
            ),
            current_user=self.owner,
            db=self.db,
        )
        self.assertEqual(len(response.chapters), 2)
        self.assertEqual(len(response.chapters[0].concepts), 2)
        subject = self.db.scalar(select(Subject).where(Subject.name == "Imported Science"))
        self.assertEqual(subject.org_id, self.org_a.id)

    def test_individual_import_commit_activates_subject_and_unlocks_chapters(self) -> None:
        response = commit_curriculum_import(
            ImportCommitRequest(
                name="Solo Imported",
                chapters=[DraftChapterModel_data("Chapter 1", ["T1"]), DraftChapterModel_data("Chapter 2", [])],
            ),
            current_user=self.individual_student,
            db=self.db,
        )
        self.db.refresh(self.individual_classroom)
        self.assertEqual(self.individual_classroom.subject_id, response.id)
        unlock_count = self.db.scalar(
            select(func.count(ChapterUnlock.id)).where(ChapterUnlock.classroom_id == self.individual_classroom.id)
        )
        self.assertEqual(unlock_count, 2)

    def test_commit_subject_tree_persists(self) -> None:
        subject = commit_subject_tree(self.db, self.org_a.id, "Direct", "CBSE", "10", [DraftChapter("Ch1", ["a"])])
        self.assertEqual(self.db.scalar(select(func.count(Chapter.id)).where(Chapter.subject_id == subject.id)), 1)
        self.assertEqual(self.db.scalar(select(func.count(Concept.id))), 1)


def DraftChapterModel_data(title, topics):
    from app.main import DraftChapterModel

    return DraftChapterModel(title=title, topics=topics)
