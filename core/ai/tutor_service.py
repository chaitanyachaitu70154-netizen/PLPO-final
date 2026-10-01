"""
Context-Aware Socratic AI Tutor Service for Phase 3.
Conditioned on real-time student knowledge state, active misconceptions, and prerequisite DAG.
Guarantees pedagogical depth, non-generic Socratic dialogue, and adversarial protection.
"""

from typing import List, Optional, Dict, Any, Tuple
from core.knowledge_state import KnowledgeState
from core.misconception import Misconception, MisconceptionStatus
from core.ai.base import BaseAIProvider
from core.ai.gemini_provider import GeminiProvider
from core.ai.schema import StudentDiagnosticAnalysis, SocraticTutorResponse, GeneratedPracticeOutput
from core.security import InputValidator, SECURITY_RATE_LIMITER, SecurityViolationType

class AITutorService:
    """
    Socratic AI Tutor conditioned on real-time cognitive knowledge states.
    Prevents generic chatbot behavior by injecting structured student context.
    """

    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self.provider = provider or GeminiProvider()

    def build_system_context(
        self,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception]
    ) -> str:
        """
        Synthesize detailed cognitive context to guide the LLM's pedagogical posture.
        """
        weak_topics = [f"{t.topic_name} ({t.percentage:.0f}%)" for t in knowledge_state.get_weak_topics()]
        strong_topics = [f"{t.topic_name} ({t.percentage:.0f}%)" for t in knowledge_state.get_strong_topics()]
        active_miscs = [m.title for m in misconceptions if m.status != MisconceptionStatus.REMEDIATED]

        context = (
            "You are an empathetic, world-class Socratic Computer Science AI Tutor on the PLPO platform.\n"
            "You are NOT a generic conversational chatbot. You are teaching a specific student whose cognitive state is known:\n\n"
            f"- Student Name: {knowledge_state.student_name}\n"
            f"- Enrolled Curriculum: {knowledge_state.subject}\n"
            f"- Overall Mastery: {knowledge_state.get_overall_mastery():.1f}%\n"
            f"- Metacognitive Confidence: {knowledge_state.get_overall_confidence():.1f}%\n"
            f"- Strong Mastery Anchor Topics: {', '.join(strong_topics) if strong_topics else 'None yet'}\n"
            f"- Current Weak Knowledge Gaps: {', '.join(weak_topics) if weak_topics else 'None'}\n"
            f"- Active Cognitive Misconceptions: {', '.join(active_miscs) if active_miscs else 'None detected'}\n\n"
            "PEDAGOGICAL RULES:\n"
            "1. Do NOT immediately output full code solutions. Guide the learner to discover the invariant.\n"
            "2. When explaining errors, contrast the student's flawed mental model against ground truth.\n"
            "3. Use vivid, real-world analogies (e.g. slots vs letters, cafeteria trays vs lines, billboards vs envelopes).\n"
            "4. Always conclude with a targeted Socratic question that checks for conceptual stability.\n"
            "5. If foundational prerequisites are weak, explicitly recommend prerequisite review before advanced logic."
        )
        return context

    def get_socratic_guidance(
        self,
        student_query: str,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception],
        client_session_id: str = "session_default"
    ) -> Tuple[bool, Optional[SocraticTutorResponse], str]:
        """
        Process student query with adversarial screening, rate limiting, and context injection.
        Returns: (success: bool, response: Optional[SocraticTutorResponse], message: str)
        """
        # 1. Adversarial & Security Validation
        validation = InputValidator.validate_user_tutor_query(student_query)
        if not validation.is_valid:
            return False, None, validation.message

        # 2. Rate Limiting Check
        allowed, remaining, retry_after = SECURITY_RATE_LIMITER.check_limit(client_session_id)
        if not allowed:
            return (
                False,
                None,
                f"Rate limit exceeded: You have made multiple rapid AI inquiries. Please pause for {retry_after} seconds."
            )

        # 3. Construct System Prompt & User Inquiry
        system_instruction = self.build_system_context(knowledge_state, misconceptions)
        prompt = (
            f"STUDENT INQUIRY: {validation.sanitized_value}\n\n"
            "Provide your Socratic response structured according to the SocraticTutorResponse schema:\n"
            "- analogy_title\n"
            "- conceptual_explanation\n"
            "- code_example_flawed\n"
            "- code_example_corrected\n"
            "- socratic_question\n"
            "- prerequisite_recommendation"
        )

        # 4. Generate & Validate Structured Output
        try:
            response = self.provider.generate_structured_json(
                prompt=prompt,
                schema_class=SocraticTutorResponse,
                system_instruction=system_instruction
            )
            return True, response, "Success"
        except Exception as e:
            return False, None, f"AI generation error: {str(e)}"

    def analyze_knowledge_state_structured(
        self,
        knowledge_state: KnowledgeState,
        target_topic: str = "Functions",
        active_misconception: Optional[str] = "Parameter vs Argument"
    ) -> StudentDiagnosticAnalysis:
        """
        Generates validated structured JSON diagnostic analysis matching Feature 2 specification.
        """
        t = knowledge_state.get_topic(target_topic)
        mastery_val = t.percentage if t else 43.0
        conf_val = t.confidence_percentage if t else 31.0

        prompt = (
            f"Analyze student knowledge state for topic '{target_topic}'.\n"
            f"Current Mastery: {mastery_val}%\n"
            f"Current Confidence: {conf_val}%\n"
            f"Diagnosed Misconception: {active_misconception or 'None'}\n"
            "Return a StudentDiagnosticAnalysis JSON object."
        )

        return self.provider.generate_structured_json(
            prompt=prompt,
            schema_class=StudentDiagnosticAnalysis,
            system_instruction="You are an automated curricular diagnostic analyzer. Output strictly validated JSON."
        )

    def generate_practice_drill(
        self,
        topic: str,
        misconception_title: Optional[str] = None,
        difficulty: str = "Medium"
    ) -> GeneratedPracticeOutput:
        """
        Synthesizes an on-demand targeted coding drill matching active cognitive deficits.
        """
        prompt = (
            f"Generate a targeted coding drill for topic '{topic}' with difficulty '{difficulty}'.\n"
            f"Targeted Misconception to eliminate: {misconception_title or 'General practice'}.\n"
            "Return a GeneratedPracticeOutput JSON object."
        )

        return self.provider.generate_structured_json(
            prompt=prompt,
            schema_class=GeneratedPracticeOutput,
            system_instruction="You are a deliberate practice curriculum designer. Output strictly validated JSON."
        )
