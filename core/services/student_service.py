"""
Student Profile & State Management Service for Phase 4.
Handles multi-tenant student profile persistence, retrieval, and baseline resets.
"""

from typing import Optional
from core.student_profile import StudentProfile
from core.db.repository import (
    StudentRepository,
    KnowledgeStateRepository,
    MisconceptionRepository,
    LearningPathRepository
)
from data.demo_data import (
    get_demo_student_profile,
    get_demo_knowledge_state,
    get_demo_misconceptions,
    get_demo_learning_path
)
from core.cache import GLOBAL_CACHE

class StudentService:
    """Service boundary for student profile lifecycle and state management."""

    @staticmethod
    def get_or_create_student(student_id: str = "STU-2026-PY-089") -> StudentProfile:
        """Fetch profile from database or seed baseline demo student."""
        profile = StudentRepository.get_profile(student_id)
        if profile is not None:
            return profile

        # Seed and return
        profile = get_demo_student_profile()
        profile.student_id = student_id
        StudentRepository.save_profile(profile)
        return profile

    @staticmethod
    def update_profile(profile: StudentProfile) -> None:
        StudentRepository.save_profile(profile)

    @staticmethod
    def reset_to_baseline(student_id: str = "STU-2026-PY-089") -> None:
        """Reset student knowledge state and path to the baseline hackathon benchmark."""
        # 1. Clear caches
        GLOBAL_CACHE.delete(f"learning_path:{student_id}")

        # 2. Reset Profile
        profile = get_demo_student_profile()
        profile.student_id = student_id
        StudentRepository.save_profile(profile)

        # 3. Reset Knowledge State
        ks = get_demo_knowledge_state()
        ks.student_id = student_id
        KnowledgeStateRepository.save_knowledge_state(ks)

        # 4. Reset Misconceptions
        miscs = get_demo_misconceptions()
        for m in miscs:
            MisconceptionRepository.save_misconception_state(student_id, m)

        # 5. Reset Learning Path
        path = get_demo_learning_path(ks, miscs)
        LearningPathRepository.save_path(student_id, path)
