"""
Diagnostic Assessment Engine and Metacognitive Evaluation module for Phase 2.
Implements question schemas, distractor analysis, confidence tracking, and
adaptive intervention triggers.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

from core.confidence import ConfidenceAnalyzer, ConfidenceAnalysisResult, MetacognitiveQuadrant
from core.misconception import Misconception, MisconceptionCatalog

@dataclass
class DiagnosticQuestion:
    """Represents a diagnostic question engineered with prerequisites and misconception mapping."""
    id: str
    question: str
    topic: str
    difficulty: str  # Easy, Medium, Hard
    options: List[str]
    correct_answer_index: int
    explanation: str
    prerequisite_topic: str
    misconception_category: str
    distractor_misconceptions: Dict[int, str] = field(default_factory=dict)
    code_snippet: Optional[str] = None

@dataclass
class StudentAttemptRecord:
    """Persistent telemetry record of a single question attempt."""
    question_id: str
    topic: str
    difficulty: str
    selected_option_index: int
    selected_answer_text: str
    is_correct: bool
    confidence_rating: int  # 1 to 5
    quadrant: MetacognitiveQuadrant
    response_time_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    misconception_detected: Optional[str] = None

@dataclass
class AssessmentEvaluationResult:
    """Holistic diagnostic output after a student submits an answer and confidence rating."""
    is_correct: bool
    selected_option_index: int
    correct_option_index: int
    explanation: str
    confidence_result: ConfidenceAnalysisResult
    detected_misconception: Optional[Misconception] = None
    prerequisite_topic: str = ""
    attempt_record: Optional[StudentAttemptRecord] = None

class AssessmentEngine:
    """
    Evaluates assessment questions, performs distractor analysis to detect underlying misconceptions,
    and conducts confidence calibration analysis.
    """
    def __init__(self, catalog: Optional[Dict[str, Misconception]] = None):
        self.catalog = catalog or MisconceptionCatalog.get_catalog()
        self.attempt_history: List[StudentAttemptRecord] = []

    def evaluate_submission(
        self,
        question: DiagnosticQuestion,
        selected_index: int,
        confidence_rating: int,
        response_time_seconds: float = 0.0
    ) -> AssessmentEvaluationResult:
        """
        Complete diagnostic evaluation:
        1. Evaluates correctness
        2. Conducts Confidence Analysis (Feature 4)
        3. Conducts Misconception Distractor Analysis (Feature 5)
        4. Logs attempt telemetry
        """
        is_correct = (selected_index == question.correct_answer_index)
        conf_result = ConfidenceAnalyzer.analyze(is_correct, confidence_rating)

        detected_misc: Optional[Misconception] = None
        misc_id: Optional[str] = None

        if not is_correct:
            # Check if student picked a specific distractor option
            misc_id = question.distractor_misconceptions.get(selected_index)
            if not misc_id and question.misconception_category:
                # Fallback to question's general misconception category if distractor map didn't match
                misc_id = question.misconception_category

            if misc_id and misc_id in self.catalog:
                detected_misc = self.catalog[misc_id]
                # If student answered with high confidence (4 or 5), promote to detected!
                detected_misc.register_trigger(high_confidence=(confidence_rating >= 4))

        # Record telemetry
        record = StudentAttemptRecord(
            question_id=question.id,
            topic=question.topic,
            difficulty=question.difficulty,
            selected_option_index=selected_index,
            selected_answer_text=question.options[selected_index] if 0 <= selected_index < len(question.options) else "Unknown",
            is_correct=is_correct,
            confidence_rating=confidence_rating,
            quadrant=conf_result.quadrant,
            response_time_seconds=response_time_seconds,
            misconception_detected=detected_misc.id if detected_misc else None
        )
        self.attempt_history.append(record)

        return AssessmentEvaluationResult(
            is_correct=is_correct,
            selected_option_index=selected_index,
            correct_option_index=question.correct_answer_index,
            explanation=question.explanation,
            confidence_result=conf_result,
            detected_misconception=detected_misc,
            prerequisite_topic=question.prerequisite_topic,
            attempt_record=record
        )
