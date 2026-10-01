"""
Repository pattern implementations for Phase 4 database persistence.
Encapsulates data access and coordinates with the domain models (KnowledgeState, Misconception, StudentProfile).
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, select, func, text

from core.student_profile import StudentProfile
from core.knowledge_state import KnowledgeState, TopicMastery, LearningStatus, StateChangeRecord
from core.misconception import Misconception, MisconceptionStatus
from core.optimizer import LearningPath, LearningPathNode, PathNodeStatus, PathNodeType, PathChangeLog
from core.db.session import get_db_session, is_postgres
from core.db.models import (
    StudentProfileModel,
    TopicMasteryModel,
    AssessmentAttemptModel,
    MisconceptionStateModel,
    LearningPathModel,
    StateChangeAuditModel,
    CurriculumEmbeddingModel
)

logger = logging.getLogger("plpo.repository")

class StudentRepository:
    """Manages student profile persistence and retrieval."""

    @staticmethod
    def get_profile(student_id: str) -> Optional[StudentProfile]:
        with get_db_session() as session:
            record = session.query(StudentProfileModel).filter_by(student_id=student_id).first()
            if not record:
                return None
            return StudentProfile(
                student_id=record.student_id,
                name=record.name,
                education_level=record.education_level or "",
                subject=record.subject,
                current_level=record.current_level or "",
                learning_goal=record.learning_goal or "",
                preferred_pace=record.preferred_pace or ""
            )

    @staticmethod
    def save_profile(profile: StudentProfile) -> None:
        with get_db_session() as session:
            record = session.query(StudentProfileModel).filter_by(student_id=profile.student_id).first()
            if not record:
                record = StudentProfileModel(student_id=profile.student_id)
                session.add(record)
            
            record.name = profile.name
            record.education_level = profile.education_level
            record.subject = profile.subject
            record.current_level = profile.current_level
            record.learning_goal = profile.learning_goal
            record.preferred_pace = profile.preferred_pace
            record.updated_at = datetime.utcnow()

class KnowledgeStateRepository:
    """Manages KnowledgeState and granular topic masteries in relational storage."""

    @staticmethod
    def load_knowledge_state(student_id: str, student_name: str = "Demo Student", subject: str = "Python Programming") -> Optional[KnowledgeState]:
        with get_db_session() as session:
            # Check student exists
            prof = session.query(StudentProfileModel).filter_by(student_id=student_id).first()
            if not prof:
                return None

            records = session.query(TopicMasteryModel).filter_by(student_id=student_id).all()
            if not records:
                return None

            ks = KnowledgeState(
                student_id=prof.student_id,
                student_name=prof.name,
                subject=prof.subject
            )

            for rec in records:
                recent_perf = json.loads(rec.recent_performance_json or "[]")
                misc_status = json.loads(rec.misconception_status_json or "{}")
                
                try:
                    status_enum = LearningStatus(rec.learning_status)
                except (ValueError, TypeError):
                    status_enum = LearningStatus.NOT_STARTED

                tm = TopicMastery(
                    topic_name=rec.topic_name,
                    mastery_score=rec.mastery_score,
                    confidence_score=rec.confidence_score,
                    attempts=rec.attempts,
                    correct_attempts=rec.correct_attempts,
                    incorrect_attempts=rec.incorrect_attempts,
                    recent_performance=recent_perf,
                    misconception_status=misc_status,
                    learning_status=status_enum,
                    last_assessed=rec.last_assessed.isoformat() if rec.last_assessed else None
                )
                ks.topics[rec.topic_name] = tm

            return ks

    @staticmethod
    def save_knowledge_state(ks: KnowledgeState) -> None:
        with get_db_session() as session:
            # Ensure student record exists
            prof = session.query(StudentProfileModel).filter_by(student_id=ks.student_id).first()
            if not prof:
                prof = StudentProfileModel(
                    student_id=ks.student_id,
                    name=ks.student_name,
                    subject=ks.subject
                )
                session.add(prof)
                session.flush()

            for topic_name, tm in ks.topics.items():
                record = session.query(TopicMasteryModel).filter_by(
                    student_id=ks.student_id,
                    topic_name=topic_name
                ).first()

                if not record:
                    record = TopicMasteryModel(
                        student_id=ks.student_id,
                        topic_name=topic_name
                    )
                    session.add(record)

                record.mastery_score = float(tm.mastery_score)
                record.confidence_score = float(tm.confidence_score)
                record.attempts = int(tm.attempts)
                record.correct_attempts = int(tm.correct_attempts)
                record.incorrect_attempts = int(tm.incorrect_attempts)
                record.recent_performance_json = json.dumps(tm.recent_performance)
                record.misconception_status_json = json.dumps(tm.misconception_status)
                record.learning_status = tm.learning_status.value
                if tm.last_assessed:
                    try:
                        record.last_assessed = datetime.fromisoformat(tm.last_assessed)
                    except Exception:
                        record.last_assessed = datetime.utcnow()

class AssessmentRepository:
    """Records assessment submissions and provides queryable attempt telemetry."""

    @staticmethod
    def record_attempt(
        student_id: str,
        question_id: str,
        topic: str,
        difficulty: str,
        chosen_option: str,
        is_correct: bool,
        confidence: int,
        response_time_sec: float
    ) -> None:
        with get_db_session() as session:
            attempt = AssessmentAttemptModel(
                student_id=student_id,
                question_id=question_id,
                topic=topic,
                difficulty=difficulty,
                chosen_option=chosen_option,
                is_correct=is_correct,
                confidence=int(confidence),
                response_time_sec=float(response_time_sec),
                created_at=datetime.utcnow()
            )
            session.add(attempt)

    @staticmethod
    def get_attempts(student_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            records = session.query(AssessmentAttemptModel).filter_by(
                student_id=student_id
            ).order_by(desc(AssessmentAttemptModel.created_at)).limit(limit).all()

            return [
                {
                    "id": r.id,
                    "question_id": r.question_id,
                    "topic": r.topic,
                    "difficulty": r.difficulty,
                    "chosen_option": r.chosen_option,
                    "is_correct": r.is_correct,
                    "confidence": r.confidence,
                    "response_time_sec": r.response_time_sec,
                    "timestamp": r.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for r in records
            ]

class MisconceptionRepository:
    """Persists diagnosed and remediated misconception lifecycle states."""

    @staticmethod
    def save_misconception_state(student_id: str, misc: Misconception) -> None:
        with get_db_session() as session:
            record = session.query(MisconceptionStateModel).filter_by(
                student_id=student_id,
                misconception_id=misc.id
            ).first()

            if not record:
                record = MisconceptionStateModel(
                    student_id=student_id,
                    misconception_id=misc.id,
                    title=misc.title,
                    status=misc.status.value,
                    detected_at=datetime.utcnow()
                )
                session.add(record)
            else:
                record.status = misc.status.value
                if misc.status == MisconceptionStatus.REMEDIATED and not record.remediated_at:
                    record.remediated_at = datetime.utcnow()

    @staticmethod
    def get_misconceptions(student_id: str) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            records = session.query(MisconceptionStateModel).filter_by(student_id=student_id).all()
            return [
                {
                    "misconception_id": r.misconception_id,
                    "title": r.title,
                    "status": r.status,
                    "detected_at": r.detected_at.strftime("%Y-%m-%d %H:%M:%S") if r.detected_at else None,
                    "remediated_at": r.remediated_at.strftime("%Y-%m-%d %H:%M:%S") if r.remediated_at else None,
                }
                for r in records
            ]

class AuditRepository:
    """Manages the immutable state change audit trail for analytics."""

    @staticmethod
    def record_change(student_id: str, record: StateChangeRecord) -> None:
        reason_text = getattr(record, "trigger_reason", getattr(record, "reason", "Diagnostic Assessment"))
        with get_db_session() as session:
            audit = StateChangeAuditModel(
                student_id=student_id,
                topic_name=record.topic_name,
                old_mastery=float(record.old_mastery),
                new_mastery=float(record.new_mastery),
                old_confidence=float(record.old_confidence),
                new_confidence=float(record.new_confidence),
                reason=reason_text,
                timestamp=datetime.utcnow()
            )
            session.add(audit)

    @staticmethod
    def get_history(student_id: str, limit: int = 100) -> List[StateChangeRecord]:
        with get_db_session() as session:
            records = session.query(StateChangeAuditModel).filter_by(
                student_id=student_id
            ).order_by(desc(StateChangeAuditModel.timestamp)).limit(limit).all()

            return [
                StateChangeRecord(
                    topic_name=r.topic_name,
                    old_mastery=r.old_mastery,
                    new_mastery=r.new_mastery,
                    old_confidence=r.old_confidence,
                    new_confidence=r.new_confidence,
                    is_correct=True,
                    confidence_rating=4,
                    trigger_reason=r.reason,
                    timestamp=r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )
                for r in records
            ]

class LearningPathRepository:
    """Persists dynamic learning path snapshots."""

    @staticmethod
    def save_path(student_id: str, path: LearningPath) -> None:
        with get_db_session() as session:
            nodes_data = [
                {
                    "id": node.id,
                    "step_number": node.step_number,
                    "title": node.title,
                    "topic": node.topic,
                    "node_type": node.node_type.value,
                    "status": node.status.value,
                    "estimated_minutes": node.estimated_minutes,
                    "summary": node.summary,
                    "pedagogical_rationale": node.pedagogical_rationale,
                    "learning_objectives": node.learning_objectives,
                    "is_remediated": node.is_remediated,
                    "is_blocking": node.is_blocking
                }
                for node in path.nodes
            ]

            rationale_str = path.change_log.summary_message if path.change_log else ""

            record = session.query(LearningPathModel).filter_by(
                student_id=student_id,
                version=path.version
            ).first()

            if not record:
                record = LearningPathModel(
                    student_id=student_id,
                    version=path.version,
                    generated_at=datetime.utcnow(),
                    milestones_json=json.dumps(nodes_data),
                    rationale=rationale_str
                )
                session.add(record)
            else:
                record.milestones_json = json.dumps(nodes_data)
                record.rationale = rationale_str
                record.generated_at = datetime.utcnow()

    @staticmethod
    def get_latest_path(student_id: str, subject: str = "Python Programming") -> Optional[LearningPath]:
        with get_db_session() as session:
            record = session.query(LearningPathModel).filter_by(
                student_id=student_id
            ).order_by(desc(LearningPathModel.version)).first()

            if not record:
                return None

            raw_nodes = json.loads(record.milestones_json)
            nodes = [
                LearningPathNode(
                    id=n["id"],
                    step_number=n["step_number"],
                    title=n["title"],
                    topic=n["topic"],
                    node_type=PathNodeType(n["node_type"]),
                    status=PathNodeStatus(n["status"]),
                    estimated_minutes=n.get("estimated_minutes", 15),
                    summary=n.get("summary", ""),
                    pedagogical_rationale=n.get("pedagogical_rationale", ""),
                    learning_objectives=n.get("learning_objectives", []),
                    is_remediated=n.get("is_remediated", False),
                    is_blocking=n.get("is_blocking", False)
                )
                for n in raw_nodes
            ]

            change_log = None
            if record.rationale:
                change_log = PathChangeLog(
                    trigger="Loaded from database persistence",
                    summary_message=record.rationale
                )

            return LearningPath(
                student_id=record.student_id,
                subject=subject,
                nodes=nodes,
                change_log=change_log,
                version=record.version
            )

class CurriculumEmbeddingRepository:
    """
    Manages vector embeddings with pgvector similarity search on PostgreSQL
    and cosine distance calculation fallback for local SQLite development.
    """

    @staticmethod
    def store_embedding(
        topic_name: str,
        subtopic_title: str,
        content_text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        with get_db_session() as session:
            record = CurriculumEmbeddingModel(
                topic_name=topic_name,
                subtopic_title=subtopic_title,
                content_text=content_text,
                embedding=embedding,
                embedding_json=json.dumps(embedding),
                metadata_json=json.dumps(metadata or {}),
                created_at=datetime.utcnow()
            )
            session.add(record)

    @staticmethod
    def search_similar(
        query_embedding: List[float],
        top_k: int = 3,
        topic_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic search.
        On PostgreSQL: uses pgvector L2 or cosine distance operator (<=>).
        On SQLite: computes cosine similarity in-memory using python.
        """
        with get_db_session() as session:
            if is_postgres():
                # PostgreSQL with pgvector cosine distance operator
                stmt = select(
                    CurriculumEmbeddingModel,
                    CurriculumEmbeddingModel.embedding.cosine_distance(query_embedding).label("distance")
                )
                if topic_filter:
                    stmt = stmt.filter(CurriculumEmbeddingModel.topic_name == topic_filter)
                stmt = stmt.order_by("distance").limit(top_k)

                results = session.execute(stmt).all()
                return [
                    {
                        "topic": item.CurriculumEmbeddingModel.topic_name,
                        "title": item.CurriculumEmbeddingModel.subtopic_title,
                        "text": item.CurriculumEmbeddingModel.content_text,
                        "similarity": round(1.0 - float(item.distance), 4)
                    }
                    for item in results
                ]
            else:
                # SQLite fallback: manual cosine similarity
                query = session.query(CurriculumEmbeddingModel)
                if topic_filter:
                    query = query.filter_by(topic_name=topic_filter)
                all_items = query.all()

                if not all_items:
                    return []

                # Dot product & magnitude
                import math
                def cosine_sim(a: List[float], b: List[float]) -> float:
                    dot = sum(x * y for x, y in zip(a, b))
                    norm_a = math.sqrt(sum(x * x for x in a))
                    norm_b = math.sqrt(sum(y * y for y in b))
                    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

                scored = []
                for item in all_items:
                    vec = json.loads(item.embedding_json or "[]")
                    sim = cosine_sim(query_embedding, vec) if vec else 0.0
                    scored.append((sim, item))

                scored.sort(key=lambda x: x[0], reverse=True)
                return [
                    {
                        "topic": item.topic_name,
                        "title": item.subtopic_title,
                        "text": item.content_text,
                        "similarity": round(float(sim), 4)
                    }
                    for sim, item in scored[:top_k]
                ]
