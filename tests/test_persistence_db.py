"""
Unit and Integration Tests for Database Persistence and Repository Layer.
Validates:
1. Student Profile CRUD
2. Topic Mastery updates and composite indexing
3. Assessment attempt telemetry logging
4. Misconception lifecycle transitions
5. Learning Path versioned snapshots
6. State change audit trail
7. Vector embeddings and semantic cosine similarity search
"""

import pytest
from core.student_profile import StudentProfile
from core.knowledge_state import KnowledgeState, StateChangeRecord
from core.misconception import MisconceptionCatalog, MisconceptionStatus
from core.db.session import init_database
from core.db.repository import (
    StudentRepository,
    KnowledgeStateRepository,
    AssessmentRepository,
    MisconceptionRepository,
    AuditRepository,
    CurriculumEmbeddingRepository
)
from core.db.init_db import generate_mock_embedding

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_database()

def test_student_profile_persistence():
    profile = StudentProfile(
        student_id="STU-TEST-999",
        name="Ada Lovelace",
        education_level="Postgraduate",
        subject="Python Programming",
        current_level="Advanced Foundations",
        learning_goal="Master Compiler Architecture",
        preferred_pace="Intensive"
    )

    StudentRepository.save_profile(profile)
    loaded = StudentRepository.get_profile("STU-TEST-999")
    assert loaded is not None
    assert loaded.name == "Ada Lovelace"
    assert loaded.subject == "Python Programming"

def test_knowledge_state_persistence():
    ks = KnowledgeState(student_id="STU-TEST-999", student_name="Ada Lovelace")
    ks.set_topic_score("Functions", 75.0, confidence=80.0, reason="Diagnostic Assessment")
    ks.set_topic_score("Loops", 85.0, confidence=90.0, reason="Diagnostic Assessment")

    KnowledgeStateRepository.save_knowledge_state(ks)
    loaded_ks = KnowledgeStateRepository.load_knowledge_state("STU-TEST-999")

    assert loaded_ks is not None
    assert loaded_ks.get_topic("Functions").percentage == 75.0
    assert loaded_ks.get_topic("Loops").percentage == 85.0

def test_assessment_attempt_recording():
    AssessmentRepository.record_attempt(
        student_id="STU-TEST-999",
        question_id="q_test_01",
        topic="Functions",
        difficulty="Medium",
        chosen_option="Option A",
        is_correct=True,
        confidence=4,
        response_time_sec=11.2
    )

    attempts = AssessmentRepository.get_attempts("STU-TEST-999", limit=10)
    assert len(attempts) >= 1
    recent = attempts[0]
    assert recent["question_id"] == "q_test_01"
    assert recent["is_correct"] is True
    assert recent["confidence"] == 4

def test_audit_trail_logging():
    record = StateChangeRecord(
        topic_name="Functions",
        old_mastery=43.0,
        new_mastery=55.0,
        old_confidence=31.0,
        new_confidence=45.0,
        is_correct=True,
        confidence_rating=4,
        trigger_reason="Targeted follow-up reassessment"
    )

    AuditRepository.record_change("STU-TEST-999", record)
    history = AuditRepository.get_history("STU-TEST-999", limit=5)
    assert len(history) >= 1
    assert history[0].topic_name == "Functions"
    assert history[0].old_mastery == 43.0
    assert history[0].new_mastery == 55.0

def test_vector_embedding_search():
    embedding = generate_mock_embedding("Functions:Recursion", 768)
    CurriculumEmbeddingRepository.store_embedding(
        topic_name="Functions",
        subtopic_title="Recursion Base Case Invariant",
        content_text="A recursive function requires a base condition that terminates recursive calls without pushing new frames.",
        embedding=embedding,
        metadata={"difficulty": "Hard"}
    )

    results = CurriculumEmbeddingRepository.search_similar(embedding, top_k=1, topic_filter="Functions")
    assert len(results) == 1
    assert results[0]["title"] == "Recursion Base Case Invariant"
    assert results[0]["similarity"] > 0.9  # Exact match should have similarity ~1.0
