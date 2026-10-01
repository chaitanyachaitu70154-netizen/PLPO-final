"""
Adaptive Learning Service for Phase 4.
Orchestrates the entire closed-loop adaptive cycle:
ASSESS -> ANALYZE -> IDENTIFY GAP -> CHECK PREREQUISITES -> DETECT MISCONCEPTION
-> GENERATE INTERVENTION -> PRACTICE -> REASSESS -> UPDATE KNOWLEDGE STATE -> RECALCULATE LEARNING PATH
Enforces persistence in PostgreSQL/SQLite, Prometheus instrumentation, caching, and security checks.
"""

import time
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

from core.knowledge_state import KnowledgeState, StateChangeRecord
from core.misconception import Misconception, MisconceptionCatalog, MisconceptionStatus
from core.prerequisites import PrerequisiteGraph
from core.optimizer import DynamicLearningPathOptimizer, LearningPath
from core.assessment import AssessmentEngine, DiagnosticQuestion
from core.security import InputValidator, PromptInjectionDetector
from core.telemetry.metrics import METRICS
from core.telemetry.logger import get_logger
from core.cache import GLOBAL_CACHE, cached
from core.db.repository import (
    KnowledgeStateRepository,
    MisconceptionRepository,
    AssessmentRepository,
    AuditRepository,
    LearningPathRepository
)

logger = get_logger("plpo.adaptive_service")

@dataclass
class AdaptiveLoopResult:
    """Outcome payload of an adaptive assessment or reassessment action."""
    is_correct: bool
    confidence: int
    detected_misconception: Optional[Misconception] = None
    intervention_delivered: bool = False
    state_change_record: Optional[StateChangeRecord] = None
    recalculated_path: Optional[LearningPath] = None
    message: str = ""

class AdaptiveService:
    """
    Central business service orchestrating the adaptive learning loop.
    Decoupled from Streamlit UI.
    """

    def __init__(
        self,
        assessment_engine: Optional[AssessmentEngine] = None,
        prereq_graph: Optional[PrerequisiteGraph] = None,
        optimizer: Optional[DynamicLearningPathOptimizer] = None
    ):
        self.assessment_engine = assessment_engine or AssessmentEngine()
        self.prereq_graph = prereq_graph or PrerequisiteGraph()
        self.optimizer = optimizer or DynamicLearningPathOptimizer(self.prereq_graph)

    def load_or_init_knowledge_state(self, student_id: str) -> KnowledgeState:
        """Load knowledge state from database with fallback to baseline demo state."""
        ks = KnowledgeStateRepository.load_knowledge_state(student_id)
        if ks is not None:
            return ks

        # Initialize from baseline
        from data.demo_data import get_demo_knowledge_state
        ks = get_demo_knowledge_state()
        ks.student_id = student_id
        KnowledgeStateRepository.save_knowledge_state(ks)
        logger.info(f"Initialized baseline knowledge state in DB for student [{student_id}]")
        return ks

    def load_or_init_learning_path(
        self,
        student_id: str,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception]
    ) -> LearningPath:
        """Load latest path from DB or dynamically generate and persist."""
        cache_key = f"learning_path:{student_id}"
        cached_path = GLOBAL_CACHE.get(cache_key)
        if cached_path is not None and isinstance(cached_path, LearningPath):
            return cached_path

        path = LearningPathRepository.get_latest_path(student_id)
        if path is not None:
            GLOBAL_CACHE.set(cache_key, path, ttl_seconds=300)
            return path

        # Generate fresh path
        path = self.optimizer.generate_path(knowledge_state, misconceptions)
        LearningPathRepository.save_path(student_id, path)
        GLOBAL_CACHE.set(cache_key, path, ttl_seconds=300)
        return path

    def process_diagnostic_submission(
        self,
        student_id: str,
        question: DiagnosticQuestion,
        chosen_option_index: int,
        confidence_rating: int,
        response_time_sec: float,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception]
    ) -> AdaptiveLoopResult:
        """
        Execute the full adaptive assessment cycle.
        Validates security, detects misconceptions, updates state, and recalculates path.
        """
        # 1. Adversarial & Range Validation
        conf_val = InputValidator.validate_confidence(confidence_rating)
        if not conf_val.is_valid:
            METRICS.record_adversarial_violation("INVALID_CONFIDENCE")
            raise ValueError(conf_val.message)

        confidence = conf_val.sanitized_value
        is_correct = (chosen_option_index == question.correct_answer_index)
        chosen_text = question.options[chosen_option_index] if 0 <= chosen_option_index < len(question.options) else "Unknown"

        # Ensure student profile exists in DB for relational integrity
        from core.db.repository import StudentRepository
        if not StudentRepository.get_profile(student_id):
            from core.services.student_service import StudentService
            StudentService.get_or_create_student(student_id)

        # 2. Record Attempt to DB & Prometheus Telemetry
        AssessmentRepository.record_attempt(
            student_id=student_id,
            question_id=question.id,
            topic=question.topic,
            difficulty=question.difficulty,
            chosen_option=chosen_text,
            is_correct=is_correct,
            confidence=confidence,
            response_time_sec=response_time_sec
        )
        METRICS.record_assessment(question.topic, is_correct, confidence)

        # 3. Detect Misconception vs Knowledge Gap
        detected_misc: Optional[Misconception] = None
        if not is_correct:
            distractor_misc_id = question.distractor_misconceptions.get(chosen_option_index)
            if distractor_misc_id:
                detected_misc = MisconceptionCatalog.get_by_id(distractor_misc_id)
                if detected_misc:
                    detected_misc.register_trigger(high_confidence=(confidence >= 4))
                    MisconceptionRepository.save_misconception_state(student_id, detected_misc)
                    METRICS.record_misconception_detected(detected_misc.id)

                    # Update topic state
                    topic = knowledge_state.get_topic(question.topic)
                    if topic:
                        topic.misconception_status[detected_misc.id] = "detected"

        # 4. Bayesian Evidence Update
        state_record: StateChangeRecord = knowledge_state.update_from_evidence(
            topic_name=question.topic,
            is_correct=is_correct,
            confidence_rating=confidence,
            difficulty=question.difficulty,
            reason=f"Diagnostic Question [{question.id}] - {'Correct' if is_correct else 'Error'}"
        )

        # Persist updated Knowledge State & Audit Trail
        KnowledgeStateRepository.save_knowledge_state(knowledge_state)
        AuditRepository.record_change(student_id, state_record)

        # 5. Dynamic Learning Path Recalculation
        updated_path = self.optimizer.generate_path(
            knowledge_state=knowledge_state,
            misconceptions=misconceptions
        )
        LearningPathRepository.save_path(student_id, updated_path)
        GLOBAL_CACHE.set(f"learning_path:{student_id}", updated_path, ttl_seconds=300)
        METRICS.record_path_recalc("diagnostic_submission")

        logger.info(
            f"Processed diagnostic submission for {student_id} on {question.topic}: "
            f"Correct={is_correct}, Mastery={state_record.new_mastery:.1f}% (+{state_record.new_mastery - state_record.old_mastery:+.1f}%)"
        )

        return AdaptiveLoopResult(
            is_correct=is_correct,
            confidence=confidence,
            detected_misconception=detected_misc,
            intervention_delivered=(detected_misc is not None),
            state_change_record=state_record,
            recalculated_path=updated_path,
            message="Diagnostic assessment processed and learning path optimized."
        )

    def process_remediation_success(
        self,
        student_id: str,
        topic_name: str,
        misconception: Misconception,
        confidence_rating: int,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception]
    ) -> AdaptiveLoopResult:
        """
        Execute state update upon successful remediation follow-up.
        """
        # Validate confidence
        conf_val = InputValidator.validate_confidence(confidence_rating)
        confidence = conf_val.sanitized_value if conf_val.is_valid else 4

        # Ensure student profile exists in DB
        from core.db.repository import StudentRepository
        if not StudentRepository.get_profile(student_id):
            from core.services.student_service import StudentService
            StudentService.get_or_create_student(student_id)

        # Mark remediated in domain & database
        misconception.mark_remediated()
        MisconceptionRepository.save_misconception_state(student_id, misconception)
        METRICS.record_misconception_remediated(misconception.id)

        # Update Knowledge State
        state_record = knowledge_state.update_from_evidence(
            topic_name=topic_name,
            is_correct=True,
            confidence_rating=confidence,
            difficulty="Medium",
            reason=f"Remediated misconception: {misconception.title}"
        )
        KnowledgeStateRepository.save_knowledge_state(knowledge_state)
        AuditRepository.record_change(student_id, state_record)

        # Recalculate Path
        updated_path = self.optimizer.generate_path(
            knowledge_state=knowledge_state,
            misconceptions=misconceptions
        )
        LearningPathRepository.save_path(student_id, updated_path)
        GLOBAL_CACHE.set(f"learning_path:{student_id}", updated_path, ttl_seconds=300)
        METRICS.record_path_recalc("remediation_success")

        logger.info(f"Student [{student_id}] successfully remediated [{misconception.title}]. Path unlocked.")

        return AdaptiveLoopResult(
            is_correct=True,
            confidence=confidence,
            detected_misconception=misconception,
            state_change_record=state_record,
            recalculated_path=updated_path,
            message="Misconception successfully remediated. Knowledge state increased and learning path unlocked."
        )
