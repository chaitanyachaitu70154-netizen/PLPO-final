"""
Database package for PLPO Phase 4.
Supports PostgreSQL with pgvector for production deployments and SQLite for local development.
"""

from core.db.session import get_db_session, get_engine, init_database
from core.db.models import (
    Base,
    StudentProfileModel,
    TopicMasteryModel,
    AssessmentAttemptModel,
    MisconceptionStateModel,
    LearningPathModel,
    StateChangeAuditModel,
    CurriculumEmbeddingModel
)
from core.db.repository import (
    StudentRepository,
    KnowledgeStateRepository,
    AssessmentRepository,
    AuditRepository,
    CurriculumEmbeddingRepository
)

__all__ = [
    "get_db_session",
    "get_engine",
    "init_database",
    "Base",
    "StudentProfileModel",
    "TopicMasteryModel",
    "AssessmentAttemptModel",
    "MisconceptionStateModel",
    "LearningPathModel",
    "StateChangeAuditModel",
    "CurriculumEmbeddingModel",
    "StudentRepository",
    "KnowledgeStateRepository",
    "AssessmentRepository",
    "AuditRepository",
    "CurriculumEmbeddingRepository"
]
