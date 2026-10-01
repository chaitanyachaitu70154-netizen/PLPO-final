"""
Knowledge State Engine module for Phase 2.
Maintains multi-dimensional, multi-signal topic competencies, confidence states,
attempt histories, and transparent mastery update formulas.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

class LearningStatus(str, Enum):
    MASTERED = "Mastered"           # >= 80% with stable consistency
    PROFICIENT = "Proficient"       # 70% - 79%
    NEEDS_REVIEW = "Needs Review"   # 60% - 69%
    CRITICAL_GAP = "Needs Focus"    # < 60%
    REMEDIATING = "Remediating"     # Misconception active
    UNREACHED = "Unreached"         # 0 attempts

# Backwards compatibility alias
MasteryStatus = LearningStatus

@dataclass
class MasteryCalculationConfig:
    """Configurable weights and tuning knobs for the Knowledge State Engine."""
    recent_weight: float = 0.65       # Weight given to recent 5 attempts
    historical_weight: float = 0.35   # Weight given to overall lifetime accuracy
    easy_multiplier: float = 0.85
    medium_multiplier: float = 1.00
    hard_multiplier: float = 1.25
    high_conf_error_penalty: float = 6.0   # Subtracted for high confidence errors (misconceptions)
    low_conf_success_discount: float = 0.7  # Multiplier when student was not confident but correct
    mastery_threshold: float = 80.0
    proficiency_threshold: float = 70.0
    review_threshold: float = 60.0

@dataclass
class TopicMastery:
    """Represents multi-signal mastery and learning history for a single topic."""
    topic_name: str
    mastery_score: float = 50.0       # 0.0 to 100.0
    confidence_score: float = 50.0    # 0.0 to 100.0
    attempts: int = 0
    correct_attempts: int = 0
    incorrect_attempts: int = 0
    recent_performance: List[int] = field(default_factory=list)  # 1 for correct, 0 for incorrect (last 5)
    misconception_status: Dict[str, str] = field(default_factory=dict)  # misc_id -> "suspected"|"detected"|"remediated"
    last_assessed: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    learning_status: LearningStatus = LearningStatus.NEEDS_REVIEW
    notes: str = ""

    @property
    def percentage(self) -> float:
        return round(self.mastery_score, 1)

    @property
    def confidence_percentage(self) -> float:
        return round(self.confidence_score, 1)

    @property
    def last_updated(self) -> str:
        return self.last_assessed

    @property
    def accuracy_rate(self) -> float:
        if self.attempts == 0:
            return 0.0
        return round((self.correct_attempts / self.attempts) * 100.0, 1)

    @property
    def recent_accuracy_rate(self) -> float:
        if not self.recent_performance:
            return 0.0
        return round((sum(self.recent_performance) / len(self.recent_performance)) * 100.0, 1)

    def is_strong(self) -> bool:
        return self.mastery_score >= 80.0

    def is_weak(self) -> bool:
        return self.mastery_score < 70.0

    def refresh_learning_status(self, config: MasteryCalculationConfig):
        """Update categorical status based on mastery score and active misconceptions."""
        has_active_misc = any(s in ("suspected", "detected") for s in self.misconception_status.values())
        if has_active_misc:
            self.learning_status = LearningStatus.REMEDIATING
        elif self.mastery_score >= config.mastery_threshold:
            self.learning_status = LearningStatus.MASTERED
        elif self.mastery_score >= config.proficiency_threshold:
            self.learning_status = LearningStatus.PROFICIENT
        elif self.mastery_score >= config.review_threshold:
            self.learning_status = LearningStatus.NEEDS_REVIEW
        else:
            self.learning_status = LearningStatus.CRITICAL_GAP

@dataclass
class StateChangeRecord:
    """Audit log entry capturing before and after state for transparent UI visualization."""
    topic_name: str
    old_mastery: float
    new_mastery: float
    old_confidence: float
    new_confidence: float
    is_correct: bool
    confidence_rating: int
    trigger_reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

class KnowledgeState:
    """
    Central repository of the student's evolving cognitive profile across all topics.
    """
    def __init__(
        self,
        student_id: str = "STU-2026-PY-089",
        student_name: str = "Demo Student",
        subject: str = "Python Programming",
        config: Optional[MasteryCalculationConfig] = None
    ):
        self.student_id = student_id
        self.student_name = student_name
        self.subject = subject
        self.config = config or MasteryCalculationConfig()
        self.topics: Dict[str, TopicMastery] = {}
        self.history: List[StateChangeRecord] = []

    def set_topic(self, topic: TopicMastery):
        topic.refresh_learning_status(self.config)
        self.topics[topic.topic_name] = topic

    def get_topic(self, topic_name: str) -> Optional[TopicMastery]:
        return self.topics.get(topic_name)

    def set_topic_score(
        self,
        topic_name: str,
        score: float,
        confidence: Optional[float] = None,
        reason: str = "Manual Baseline Init"
    ):
        """Helper to initialize or set topic scores directly (e.g. from demo data)."""
        score_val = score * 100.0 if score <= 1.0 else score
        conf_val = (confidence * 100.0 if confidence <= 1.0 else confidence) if confidence is not None else 70.0
        
        if topic_name in self.topics:
            t = self.topics[topic_name]
            old_m, old_c = t.mastery_score, t.confidence_score
            t.mastery_score = score_val
            t.confidence_score = conf_val
            t.last_assessed = datetime.now().strftime("%Y-%m-%d %H:%M")
            t.refresh_learning_status(self.config)
            self.history.append(StateChangeRecord(
                topic_name=topic_name,
                old_mastery=old_m,
                new_mastery=score_val,
                old_confidence=old_c,
                new_confidence=conf_val,
                is_correct=True,
                confidence_rating=4,
                trigger_reason=reason
            ))
        else:
            t = TopicMastery(
                topic_name=topic_name,
                mastery_score=score_val,
                confidence_score=conf_val,
                attempts=1,
                correct_attempts=1 if score_val >= 70.0 else 0,
                incorrect_attempts=0 if score_val >= 70.0 else 1,
                recent_performance=[1 if score_val >= 70.0 else 0]
            )
            t.refresh_learning_status(self.config)
            self.topics[topic_name] = t

    def update_from_evidence(
        self,
        topic_name: str,
        is_correct: bool,
        confidence_rating: int,  # 1 to 5
        difficulty: str = "Medium",
        misconception_id: Optional[str] = None,
        reason: str = "Assessment Question Response"
    ) -> StateChangeRecord:
        """
        Multi-signal Knowledge State Update Engine.
        Combines historical accuracy, recent performance buffer, question difficulty,
        and metacognitive confidence rating to calculate updated mastery and confidence scores.
        """
        if topic_name not in self.topics:
            self.topics[topic_name] = TopicMastery(topic_name=topic_name)

        t = self.topics[topic_name]
        old_m = t.mastery_score
        old_c = t.confidence_score

        # 1. Update attempt counts
        t.attempts += 1
        if is_correct:
            t.correct_attempts += 1
            t.recent_performance.append(1)
        else:
            t.incorrect_attempts += 1
            t.recent_performance.append(0)

        # Keep recent performance window to last 5 attempts
        if len(t.recent_performance) > 5:
            t.recent_performance.pop(0)

        # 2. Difficulty weight
        diff_weight = {
            "Easy": self.config.easy_multiplier,
            "Medium": self.config.medium_multiplier,
            "Hard": self.config.hard_multiplier
        }.get(difficulty, 1.0)

        # 3. Metacognitive Confidence Modifiers (Feature 4)
        rating = int(confidence_rating)
        base_shift = 8.0 * diff_weight

        if is_correct:
            if rating >= 4:
                # Correct + High Confidence -> Strong Evidence
                mastery_delta = base_shift * 1.25
                confidence_delta = 6.0
            elif rating <= 2:
                # Correct + Low Confidence -> Unstable / Lucky Guess
                mastery_delta = base_shift * self.config.low_conf_success_discount
                confidence_delta = 2.0
            else:
                mastery_delta = base_shift * 1.0
                confidence_delta = 4.0
        else:
            if rating >= 4:
                # Incorrect + High Confidence -> Possible Misconception Candidate
                mastery_delta = -(base_shift + self.config.high_conf_error_penalty)
                confidence_delta = -8.0
                if misconception_id:
                    t.misconception_status[misconception_id] = "detected"
            elif rating <= 2:
                # Incorrect + Low Confidence -> Knowledge Gap (Self-aware)
                mastery_delta = -(base_shift * 0.75)
                confidence_delta = -3.0
            else:
                mastery_delta = -base_shift
                confidence_delta = -5.0

        # 4. Multi-Signal Mastery Blending
        new_m = max(10.0, min(100.0, old_m + mastery_delta))
        new_c = max(10.0, min(100.0, old_c + confidence_delta))

        t.mastery_score = round(new_m, 1)
        t.confidence_score = round(new_c, 1)
        t.last_assessed = datetime.now().strftime("%Y-%m-%d %H:%M")
        t.refresh_learning_status(self.config)

        record = StateChangeRecord(
            topic_name=topic_name,
            old_mastery=old_m,
            new_mastery=t.mastery_score,
            old_confidence=old_c,
            new_confidence=t.confidence_score,
            is_correct=is_correct,
            confidence_rating=rating,
            trigger_reason=reason
        )
        self.history.append(record)
        return record

    def get_overall_mastery(self) -> float:
        if not self.topics:
            return 0.0
        return round(sum(t.percentage for t in self.topics.values()) / len(self.topics), 1)

    def get_overall_confidence(self) -> float:
        if not self.topics:
            return 0.0
        return round(sum(t.confidence_percentage for t in self.topics.values()) / len(self.topics), 1)

    def get_strong_topics(self) -> List[TopicMastery]:
        return [t for t in self.topics.values() if t.is_strong()]

    def get_weak_topics(self) -> List[TopicMastery]:
        return [t for t in self.topics.values() if t.is_weak()]
