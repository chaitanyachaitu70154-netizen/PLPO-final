"""
Authentication and Authorization Preparation Module for Phase 3.
Implements Role-Based Access Control (RBAC), user session tracking,
and permission enforcement.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from core.security import UserRole, SecurityValidationResult, SecurityViolationType

class Permission(str):
    VIEW_LEARNING_PATH = "view_learning_path"
    TAKE_ASSESSMENT = "take_assessment"
    USE_AI_TUTOR = "use_ai_tutor"
    PRACTICE_DRILLS = "practice_drills"
    VIEW_ANALYTICS = "view_analytics"
    OVERRIDE_MASTERY = "override_mastery"       # Instructor / Admin only
    INSPECT_SECURITY_LOGS = "inspect_security_logs" # Admin only
    CONFIGURE_AI_PROVIDER = "configure_ai_provider" # Admin only

ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.STUDENT: {
        Permission.VIEW_LEARNING_PATH,
        Permission.TAKE_ASSESSMENT,
        Permission.USE_AI_TUTOR,
        Permission.PRACTICE_DRILLS,
        Permission.VIEW_ANALYTICS,
    },
    UserRole.INSTRUCTOR: {
        Permission.VIEW_LEARNING_PATH,
        Permission.TAKE_ASSESSMENT,
        Permission.USE_AI_TUTOR,
        Permission.PRACTICE_DRILLS,
        Permission.VIEW_ANALYTICS,
        Permission.OVERRIDE_MASTERY,
        Permission.INSPECT_SECURITY_LOGS,
    },
    UserRole.ADMIN: {
        Permission.VIEW_LEARNING_PATH,
        Permission.TAKE_ASSESSMENT,
        Permission.USE_AI_TUTOR,
        Permission.PRACTICE_DRILLS,
        Permission.VIEW_ANALYTICS,
        Permission.OVERRIDE_MASTERY,
        Permission.INSPECT_SECURITY_LOGS,
        Permission.CONFIGURE_AI_PROVIDER,
    }
}

@dataclass
class UserSession:
    """Represents the authenticated session of an active user."""
    user_id: str
    username: str
    role: UserRole
    session_token: str
    login_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    is_active: bool = True

    def has_permission(self, permission: str) -> bool:
        """Check if user's role grants requested permission."""
        perms = ROLE_PERMISSIONS.get(self.role, set())
        return permission in perms

class AuthService:
    """Authentication and session management provider."""

    @staticmethod
    def get_demo_student_session() -> UserSession:
        return UserSession(
            user_id="STU-2026-PY-089",
            username="Demo Student",
            role=UserRole.STUDENT,
            session_token="tok_demo_student_2026"
        )

    @staticmethod
    def get_instructor_session() -> UserSession:
        return UserSession(
            user_id="INST-8802",
            username="Prof. Alan Turing (Auditor)",
            role=UserRole.INSTRUCTOR,
            session_token="tok_instructor_auditor_2026"
        )

    @staticmethod
    def verify_action(session: UserSession, permission: str) -> SecurityValidationResult:
        """Authorize action against session permissions."""
        if not session or not session.is_active:
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.UNAUTHORIZED_ACTION,
                message="Authentication required: No active session found."
            )

        if not session.has_permission(permission):
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.UNAUTHORIZED_ACTION,
                message=f"Access Denied: Role '{session.role.value}' does not have '{permission}' permission."
            )

        return SecurityValidationResult(is_valid=True)
