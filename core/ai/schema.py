"""
Pydantic Schemas for Phase 3 Structured AI Outputs.
Validates all AI-generated diagnostic evaluations, tutoring interventions, and practice drills.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class StudentDiagnosticAnalysis(BaseModel):
    """
    Structured schema for real-time AI knowledge state analysis.
    Validates the exact format specified in Phase 3 requirements.
    """
    topic: str = Field(..., description="Curricular topic analyzed (e.g. Functions, Loops, Data Structures)")
    mastery: float = Field(..., ge=0.0, le=100.0, description="Evaluated mastery percentage between 0 and 100")
    confidence: float = Field(..., ge=0.0, le=100.0, description="Metacognitive calibration index between 0 and 100")
    possible_misconception: Optional[str] = Field(None, description="Diagnosed cognitive bug title or None")
    recommended_action: str = Field(..., description="Instructional action: concept_review, practice, advance, or remediation")
    next_topic: str = Field(..., description="Recommended immediate milestone in learning path")
    reason: str = Field(..., description="Explainable pedagogical rationale based on recent performance")

    @field_validator("mastery", "confidence")
    @classmethod
    def check_bounds(cls, v: float) -> float:
        if v < 0.0 or v > 100.0:
            raise ValueError(f"Score must be within [0.0, 100.0], got {v}")
        return round(float(v), 1)

class SocraticTutorResponse(BaseModel):
    """Structured response from the context-aware Socratic AI Tutor."""
    analogy_title: str = Field(..., description="Intuitive real-world mental model or analogy")
    conceptual_explanation: str = Field(..., description="Clear explanation tailored to current mastery level")
    code_example_flawed: Optional[str] = Field(None, description="Common mistaken code pattern contrasting the concept")
    code_example_corrected: Optional[str] = Field(None, description="Idiomatic correct implementation")
    socratic_question: str = Field(..., description="Guiding reflective question to encourage self-discovery")
    prerequisite_recommendation: Optional[str] = Field(None, description="Recommended foundational concept if struggling")

class GeneratedPracticeOutput(BaseModel):
    """Structured output for dynamic targeted practice generation."""
    title: str = Field(..., description="Drill title")
    topic: str = Field(..., description="Curricular topic")
    difficulty: str = Field(..., description="Easy, Medium, or Hard")
    problem_statement: str = Field(..., description="Task prompt")
    starter_code: str = Field(..., description="Starter code template")
    solution_code: str = Field(..., description="Reference solution code")
    hints: List[str] = Field(default_factory=list, description="Step-by-step guidance hints")
    targeted_misconception: Optional[str] = Field(None, description="Cognitive bug addressed")
