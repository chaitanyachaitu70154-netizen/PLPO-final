"""
Student Profile Model module for Phase 2.
Encapsulates demographic, pedagogical, and pacing preferences of the learner.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any

@dataclass
class StudentProfile:
    """Represents the student's background, enrolled curriculum, and pacing goals."""
    student_id: str = "STU-2026-PY-089"
    name: str = "Demo Student"
    education_level: str = "Undergraduate Computer Science"
    subject: str = "Python Programming"
    current_level: str = "Intermediate Foundations"
    learning_goal: str = "Master Modular Function Design & Data Structures"
    preferred_pace: str = "Moderate (3 modules/week)"
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    updated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "education_level": self.education_level,
            "subject": self.subject,
            "current_level": self.current_level,
            "learning_goal": self.learning_goal,
            "preferred_pace": self.preferred_pace,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StudentProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
