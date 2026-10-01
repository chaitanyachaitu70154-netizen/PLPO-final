"""
Security, Adversarial Resilience, Input Validation, and RBAC Module for Phase 3.
Implements:
- Defense against prompt injection, manipulation, and unauthorized state changes.
- Rigorous boundary and type checking for confidence ratings (1-5) and mastery scores (0-100%).
- Token-bucket/sliding-window rate limiting for server-side AI requests.
- Role-based authorization preparation (Student, Instructor, Admin).
"""

import re
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

class UserRole(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"

class SecurityViolationType(str, Enum):
    INVALID_CONFIDENCE = "INVALID_CONFIDENCE"
    INVALID_MASTERY = "INVALID_MASTERY"
    MANIPULATION_ATTEMPT = "MANIPULATION_ATTEMPT"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    UNAUTHORIZED_ACTION = "UNAUTHORIZED_ACTION"
    MALFORMED_PAYLOAD = "MALFORMED_PAYLOAD"

@dataclass
class SecurityValidationResult:
    """Outcome of an adversarial or parameter validation check."""
    is_valid: bool
    sanitized_value: Any = None
    violation_type: Optional[SecurityViolationType] = None
    message: str = ""

class PromptInjectionDetector:
    """
    Guards AI prompts and Socratic tutor interactions against prompt injection attacks,
    jailbreaks, and instruction override attempts.
    """
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+|any\s+|previous\s+|prior\s+)?instructions", re.IGNORECASE),
        re.compile(r"mark\s+everything\s+(as\s+)?mastered", re.IGNORECASE),
        re.compile(r"set\s+(my\s+)?mastery\s+to\s+\d+", re.IGNORECASE),
        re.compile(r"override\s+(knowledge\s+state|mastery|score)", re.IGNORECASE),
        re.compile(r"reveal\s+(the\s+)?(api\s+key|system\s+prompt|credentials)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
        re.compile(r"disregard\s+(the\s+)?rules", re.IGNORECASE),
        re.compile(r"jailbreak", re.IGNORECASE),
        re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"drop\s+table", re.IGNORECASE),
    ]

    @classmethod
    def scan_text(cls, text: str) -> SecurityValidationResult:
        """Scan free-form text for injection or override signatures."""
        if not text or not isinstance(text, str):
            return SecurityValidationResult(is_valid=True, sanitized_value="")

        cleaned = text.strip()
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(cleaned):
                return SecurityValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    violation_type=SecurityViolationType.PROMPT_INJECTION,
                    message="Security Alert: Malicious prompt injection or unauthorized state manipulation pattern detected and neutralized."
                )

        return SecurityValidationResult(is_valid=True, sanitized_value=cleaned)

class InputValidator:
    """
    Validates all inputs against strict pedagogical and security bounds.
    Rejects manipulated requests (e.g. 999 confidence, 150% mastery).
    """

    @staticmethod
    def validate_confidence(rating: Any) -> SecurityValidationResult:
        """
        Confidence rating must be strictly an integer in [1, 5].
        Rejects out-of-bounds or non-numeric requests (e.g. 999 confidence).
        """
        try:
            val = int(rating)
            if 1 <= val <= 5:
                return SecurityValidationResult(is_valid=True, sanitized_value=val)
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.INVALID_CONFIDENCE,
                message=f"Invalid confidence rating '{rating}'. Confidence must be between 1 (Not confident) and 5 (Very confident)."
            )
        except (ValueError, TypeError):
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.INVALID_CONFIDENCE,
                message=f"Confidence value '{rating}' is not a valid number."
            )

    @staticmethod
    def validate_mastery(score: Any) -> SecurityValidationResult:
        """
        Mastery score must be strictly a float in [0.0, 100.0].
        Rejects impossible scores (e.g. 150% or -20%).
        """
        try:
            val = float(score)
            if 0.0 <= val <= 100.0:
                return SecurityValidationResult(is_valid=True, sanitized_value=round(val, 1))
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.INVALID_MASTERY,
                message=f"Invalid mastery score '{score}%'. Mastery must be between 0.0% and 100.0%."
            )
        except (ValueError, TypeError):
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.INVALID_MASTERY,
                message=f"Mastery value '{score}' is not a valid numeric score."
            )

    @staticmethod
    def validate_user_tutor_query(query: str) -> SecurityValidationResult:
        """Validates student queries submitted to the Socratic AI Tutor."""
        if not query or len(query.strip()) < 3:
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.MALFORMED_PAYLOAD,
                message="Inquiry is too short. Please ask a specific programming question."
            )

        if len(query) > 1200:
            return SecurityValidationResult(
                is_valid=False,
                violation_type=SecurityViolationType.MALFORMED_PAYLOAD,
                message="Inquiry exceeds maximum allowed length of 1200 characters."
            )

        # Check for prompt injection
        return PromptInjectionDetector.scan_text(query)

    @staticmethod
    def validate_state_change_authorization(
        role: UserRole,
        action: str = "direct_mastery_override"
    ) -> SecurityValidationResult:
        """
        Ensures students cannot directly overwrite their knowledge state without verified assessment evidence.
        Only Instructors and Admins possess override privileges.
        """
        if role in (UserRole.INSTRUCTOR, UserRole.ADMIN):
            return SecurityValidationResult(is_valid=True, sanitized_value=role)
        
        return SecurityValidationResult(
            is_valid=False,
            violation_type=SecurityViolationType.UNAUTHORIZED_ACTION,
            message="Unauthorized: Knowledge state updates must originate from verified diagnostic evidence, not direct manual overrides."
        )

class RateLimiter:
    """
    Sliding window rate limiter to prevent API quota exhaustion and denial-of-service.
    Default: 15 requests per 60-second window per client session.
    """
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._client_timestamps: Dict[str, List[float]] = {}

    def check_limit(self, client_id: str = "session_default") -> Tuple[bool, int, int]:
        """
        Check if client is within rate limits.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        timestamps = self._client_timestamps.setdefault(client_id, [])

        # Filter out timestamps older than sliding window
        timestamps = [t for t in timestamps if now - t < self.window_seconds]
        self._client_timestamps[client_id] = timestamps

        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return False, 0, max(1, retry_after)

        timestamps.append(now)
        remaining = self.max_requests - len(timestamps)
        return True, remaining, 0

# Global singletons for application-wide protection
SECURITY_RATE_LIMITER = RateLimiter(max_requests=15, window_seconds=60)
