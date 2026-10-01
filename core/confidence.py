"""
Confidence Analysis and Calibration Engine for Phase 2.
Analyzes learner metacognition by pairing correctness with self-reported confidence.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict

class ConfidenceRating(int, Enum):
    NOT_CONFIDENT = 1
    SLIGHTLY_CONFIDENT = 2
    MODERATELY_CONFIDENT = 3
    CONFIDENT = 4
    VERY_CONFIDENT = 5

    @classmethod
    def get_label(cls, val: int) -> str:
        labels = {
            1: "1 = Not confident",
            2: "2 = Slightly confident",
            3: "3 = Moderately confident",
            4: "4 = Confident",
            5: "5 = Very confident"
        }
        return labels.get(val, f"{val}")

class MetacognitiveQuadrant(str, Enum):
    STRONG_EVIDENCE = "Strong Evidence of Mastery"
    UNSTABLE_UNDERSTANDING = "Potentially Unstable Understanding"
    MISCONCEPTION_CANDIDATE = "Possible Misconception Candidate"
    KNOWLEDGE_GAP = "Possible Knowledge Gap"
    MODERATE_CALIBRATION = "Moderate Calibration"

@dataclass
class ConfidenceAnalysisResult:
    """Detailed evaluation of answer correctness paired with self-reported confidence."""
    is_correct: bool
    confidence_rating: int
    quadrant: MetacognitiveQuadrant
    insight_title: str
    pedagogical_explanation: str
    mastery_multiplier: float  # Multiplier for score adjustment
    confidence_shift: float     # Estimated shift in topic confidence
    recommended_action: str

class ConfidenceAnalyzer:
    """
    Evaluates metacognitive calibration.
    Does NOT treat confidence as infallible proof; rather, it uses confidence
    as a Bayesian signal of conceptual stability or entrenched misconception.
    """

    @staticmethod
    def analyze(is_correct: bool, confidence_rating: int) -> ConfidenceAnalysisResult:
        rating = int(confidence_rating)

        if is_correct:
            if rating >= 4:
                # Correct + High Confidence
                return ConfidenceAnalysisResult(
                    is_correct=True,
                    confidence_rating=rating,
                    quadrant=MetacognitiveQuadrant.STRONG_EVIDENCE,
                    insight_title="🎯 Strong Evidence of Mastery",
                    pedagogical_explanation=(
                        "Correct answer delivered with high metacognitive confidence. "
                        "Provides strong evidence of stable conceptual mental models."
                    ),
                    mastery_multiplier=1.2,
                    confidence_shift=0.08,
                    recommended_action="Reinforce mastery and proceed to higher difficulty or downstream concepts."
                )
            elif rating <= 2:
                # Correct + Low Confidence
                return ConfidenceAnalysisResult(
                    is_correct=True,
                    confidence_rating=rating,
                    quadrant=MetacognitiveQuadrant.UNSTABLE_UNDERSTANDING,
                    insight_title="⚠️ Potentially Unstable Understanding",
                    pedagogical_explanation=(
                        "Correct answer, but low confidence suggests hesitant reasoning, guessing, "
                        "or fragile conceptual recall."
                    ),
                    mastery_multiplier=0.6,
                    confidence_shift=0.02,
                    recommended_action="Provide positive reinforcement and schedule a near-term recall check to solidify understanding."
                )
            else:
                # Correct + Moderate Confidence (3)
                return ConfidenceAnalysisResult(
                    is_correct=True,
                    confidence_rating=rating,
                    quadrant=MetacognitiveQuadrant.MODERATE_CALIBRATION,
                    insight_title="⚖️ Calibrated Progress",
                    pedagogical_explanation="Correct answer with balanced confidence.",
                    mastery_multiplier=1.0,
                    confidence_shift=0.04,
                    recommended_action="Continue standard learning progression."
                )
        else:
            if rating >= 4:
                # Incorrect + High Confidence
                return ConfidenceAnalysisResult(
                    is_correct=False,
                    confidence_rating=rating,
                    quadrant=MetacognitiveQuadrant.MISCONCEPTION_CANDIDATE,
                    insight_title="🚨 Possible Misconception Candidate",
                    pedagogical_explanation=(
                        "Incorrect answer delivered with HIGH confidence. The student firmly believes a "
                        "flawed model is correct — the classic hallmark of a deep cognitive bug rather than simple ignorance."
                    ),
                    mastery_multiplier=-1.3,
                    confidence_shift=-0.05,
                    recommended_action="Trigger immediate diagnostic intervention: Contrast flawed mental model against ground truth."
                )
            elif rating <= 2:
                # Incorrect + Low Confidence
                return ConfidenceAnalysisResult(
                    is_correct=False,
                    confidence_rating=rating,
                    quadrant=MetacognitiveQuadrant.KNOWLEDGE_GAP,
                    insight_title="📖 Possible Knowledge Gap",
                    pedagogical_explanation=(
                        "Incorrect answer accompanied by low confidence. The learner is accurately aware "
                        "they lack familiarity with this concept (calibrated novice state)."
                    ),
                    mastery_multiplier=-0.8,
                    confidence_shift=-0.02,
                    recommended_action="Introduce foundational conceptual walkthrough before attempting harder problem solving."
                )
            else:
                # Incorrect + Moderate Confidence (3)
                return ConfidenceAnalysisResult(
                    is_correct=False,
                    confidence_rating=rating,
                    quadrant=MetacognitiveQuadrant.MODERATE_CALIBRATION,
                    insight_title="🔄 Developing Concept",
                    pedagogical_explanation="Incorrect answer with moderate confidence.",
                    mastery_multiplier=-1.0,
                    confidence_shift=-0.03,
                    recommended_action="Review explanations and attempt a similar practice problem."
                )
