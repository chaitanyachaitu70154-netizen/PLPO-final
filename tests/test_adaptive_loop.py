"""
Unit and Integration Tests for the Core Adaptive Learning Loop.
Verifies the complete cycle:
ASSESS -> ANALYZE -> IDENTIFY GAP -> CHECK PREREQUISITES -> DETECT MISCONCEPTION
-> GENERATE INTERVENTION -> PRACTICE -> REASSESS -> UPDATE KNOWLEDGE STATE -> RECALCULATE LEARNING PATH
"""

import pytest
from core.knowledge_state import KnowledgeState, LearningStatus
from core.misconception import MisconceptionCatalog, MisconceptionStatus
from core.prerequisites import PrerequisiteGraph
from core.optimizer import DynamicLearningPathOptimizer, PathNodeStatus
from core.assessment import AssessmentEngine
from core.services.adaptive_service import AdaptiveService
from data.demo_data import (
    get_demo_knowledge_state,
    get_demo_misconceptions,
    get_demo_diagnostic_questions,
    get_demo_student_profile
)

@pytest.fixture
def adaptive_setup():
    ks = get_demo_knowledge_state()
    miscs = get_demo_misconceptions()
    questions = get_demo_diagnostic_questions()
    prereq = PrerequisiteGraph()
    optimizer = DynamicLearningPathOptimizer(prereq)
    engine = AssessmentEngine()
    service = AdaptiveService(engine, prereq, optimizer)
    return {
        "ks": ks,
        "miscs": miscs,
        "questions": questions,
        "prereq": prereq,
        "optimizer": optimizer,
        "service": service,
        "student_id": "TEST-STU-001"
    }

def test_initial_state_and_prerequisites(adaptive_setup):
    """Test initial baseline mastery scores and prerequisite DAG invariants."""
    ks: KnowledgeState = adaptive_setup["ks"]
    prereq: PrerequisiteGraph = adaptive_setup["prereq"]

    assert ks.get_topic("Functions").percentage == 43.0
    assert ks.get_topic("Variables").percentage == 92.0
    assert ks.get_topic("Loops").percentage == 68.0

    # Prerequisite verification
    func_prereqs = prereq.get_prerequisites("Functions")
    assert "Loops" in func_prereqs
    assert "Conditions" in prereq.get_prerequisites("Loops")

def test_adaptive_loop_misconception_detection(adaptive_setup):
    """
    Test Step 1-5: Submit incorrect answer with high confidence (distractor 0).
    Verify that misconception is detected and active intervention is triggered.
    """
    service: AdaptiveService = adaptive_setup["service"]
    ks: KnowledgeState = adaptive_setup["ks"]
    miscs = adaptive_setup["miscs"]
    questions = adaptive_setup["questions"]
    student_id = adaptive_setup["student_id"]

    func_q = questions[0]  # Question on Functions (parameter vs argument)
    assert func_q.topic == "Functions"

    # Distractor 0 represents Parameter vs Argument confusion
    result = service.process_diagnostic_submission(
        student_id=student_id,
        question=func_q,
        chosen_option_index=0,  # Distractor
        confidence_rating=5,    # High confidence error
        response_time_sec=12.5,
        knowledge_state=ks,
        misconceptions=miscs
    )

    assert not result.is_correct
    assert result.intervention_delivered is True
    assert result.detected_misconception is not None
    assert result.detected_misconception.id == "misc_param_vs_arg"
    assert result.detected_misconception.status == MisconceptionStatus.DETECTED

    # Topic should enter REMEDIATING status
    func_topic = ks.get_topic("Functions")
    assert func_topic.learning_status == LearningStatus.REMEDIATING

def test_adaptive_loop_remediation_and_recalculation(adaptive_setup):
    """
    Test Step 6-10: Complete follow-up reassessment.
    Verify:
    1. Misconception marked remediated
    2. Knowledge state increases
    3. Audit record created
    4. Learning path recalculates dynamically
    """
    service: AdaptiveService = adaptive_setup["service"]
    ks: KnowledgeState = adaptive_setup["ks"]
    miscs = adaptive_setup["miscs"]
    student_id = adaptive_setup["student_id"]

    param_misc = MisconceptionCatalog.get_parameter_vs_argument()
    param_misc.register_trigger(high_confidence=True)

    initial_mastery = ks.get_topic("Functions").percentage

    # Student succeeds on follow-up question
    remediation_res = service.process_remediation_success(
        student_id=student_id,
        topic_name="Functions",
        misconception=param_misc,
        confidence_rating=4,
        knowledge_state=ks,
        misconceptions=miscs
    )

    assert remediation_res.is_correct is True
    assert param_misc.status == MisconceptionStatus.REMEDIATED

    # Verify Knowledge State mastery delta
    new_mastery = ks.get_topic("Functions").percentage
    assert new_mastery > initial_mastery
    assert remediation_res.state_change_record is not None
    assert remediation_res.state_change_record.new_mastery > remediation_res.state_change_record.old_mastery

    # Verify learning path recalculation
    new_path = remediation_res.recalculated_path
    assert new_path is not None
    assert len(new_path.nodes) > 0
