"""
SQLAlchemy ORM Data Models for Phase 4.
Implements relational schemas with foreign keys, composite indexes, and pgvector embeddings.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class StudentProfileModel(Base):
    """Stores persistent student biographical and educational profiles."""
    __tablename__ = "student_profiles"

    student_id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    education_level = Column(String(128), nullable=True)
    subject = Column(String(128), nullable=False, default="Python Programming")
    current_level = Column(String(128), nullable=True)
    learning_goal = Column(Text, nullable=True)
    preferred_pace = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    topic_masteries = relationship("TopicMasteryModel", back_populates="student", cascade="all, delete-orphan")
    assessment_attempts = relationship("AssessmentAttemptModel", back_populates="student", cascade="all, delete-orphan")
    misconceptions = relationship("MisconceptionStateModel", back_populates="student", cascade="all, delete-orphan")
    learning_paths = relationship("LearningPathModel", back_populates="student", cascade="all, delete-orphan")
    audit_records = relationship("StateChangeAuditModel", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<StudentProfile(student_id='{self.student_id}', name='{self.name}')>"

class TopicMasteryModel(Base):
    """Tracks granular topic mastery, calibration, and attempt metrics per student."""
    __tablename__ = "topic_masteries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    topic_name = Column(String(128), nullable=False, index=True)
    mastery_score = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.0)
    attempts = Column(Integer, default=0, nullable=False)
    correct_attempts = Column(Integer, default=0, nullable=False)
    incorrect_attempts = Column(Integer, default=0, nullable=False)
    recent_performance_json = Column(Text, default="[]", nullable=False)
    misconception_status_json = Column(Text, default="{}", nullable=False)
    learning_status = Column(String(64), default="in_progress", nullable=False)
    last_assessed = Column(DateTime, nullable=True)

    student = relationship("StudentProfileModel", back_populates="topic_masteries")

    __table_args__ = (
        UniqueConstraint("student_id", "topic_name", name="uq_student_topic"),
        Index("idx_student_topic_status", "student_id", "topic_name", "learning_status"),
    )

class AssessmentAttemptModel(Base):
    """Records diagnostic and follow-up assessment attempts with response times and confidence ratings."""
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(String(64), nullable=False, index=True)
    topic = Column(String(128), nullable=False, index=True)
    difficulty = Column(String(32), default="Medium", nullable=False)
    chosen_option = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    confidence = Column(Integer, nullable=False)  # 1 to 5 scale
    response_time_sec = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    student = relationship("StudentProfileModel", back_populates="assessment_attempts")

    __table_args__ = (
        Index("idx_student_attempt_topic", "student_id", "topic", "created_at"),
    )

class MisconceptionStateModel(Base):
    """Tracks active, detected, and remediated cognitive misconceptions."""
    __tablename__ = "misconception_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    misconception_id = Column(String(64), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(64), default="detected", nullable=False)  # suspected, detected, remediated
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    remediated_at = Column(DateTime, nullable=True)

    student = relationship("StudentProfileModel", back_populates="misconceptions")

    __table_args__ = (
        UniqueConstraint("student_id", "misconception_id", name="uq_student_misconception"),
        Index("idx_student_misc_status", "student_id", "status"),
    )

class LearningPathModel(Base):
    """Persists historical versions and active milestones of the dynamic learning path."""
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    milestones_json = Column(Text, nullable=False)
    rationale = Column(Text, nullable=True)

    student = relationship("StudentProfileModel", back_populates="learning_paths")

    __table_args__ = (
        Index("idx_student_path_version", "student_id", "version"),
    )

class StateChangeAuditModel(Base):
    """Immutable audit trail of all Bayesian knowledge state updates and delta calculations."""
    __tablename__ = "state_change_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), ForeignKey("student_profiles.student_id", ondelete="CASCADE"), nullable=False, index=True)
    topic_name = Column(String(128), nullable=False, index=True)
    old_mastery = Column(Float, nullable=False)
    new_mastery = Column(Float, nullable=False)
    old_confidence = Column(Float, nullable=False)
    new_confidence = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    student = relationship("StudentProfileModel", back_populates="audit_records")

    __table_args__ = (
        Index("idx_audit_student_time", "student_id", "timestamp"),
    )

class CurriculumEmbeddingModel(Base):
    """
    Stores vector embeddings of curriculum chunks, concepts, and diagnostic explanations
    for semantic retrieval (RAG) using PostgreSQL pgvector.
    Dimension: 768 (standard for Google Gemini text-embedding-004).
    """
    __tablename__ = "curriculum_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_name = Column(String(128), nullable=False, index=True)
    subtopic_title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    embedding = Column(Vector(768), nullable=True)
    embedding_json = Column(Text, nullable=True)  # JSON serialized fallback
    metadata_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_embedding_topic", "topic_name"),
    )
