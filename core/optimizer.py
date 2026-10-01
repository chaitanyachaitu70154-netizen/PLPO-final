"""
Dynamic Learning Path Optimization Engine for Phase 2.
Non-static, reactive curricular sequencer that evaluates multi-signal mastery states,
prerequisite dependencies, active misconceptions, and learner goals.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from core.knowledge_state import KnowledgeState, TopicMastery, LearningStatus
from core.prerequisites import PrerequisiteGraph
from core.misconception import Misconception, MisconceptionStatus
from core.student_profile import StudentProfile

class PathNodeStatus(str, Enum):
    COMPLETED = "completed"        # ✓ Mastered concept
    REVIEW = "review"              # ⚠ Prerequisite review required
    ACTIVE_TARGET = "active"       # 🎯 Primary bottleneck focus
    ACTIVE = "active"              # Alias
    REMEDIATION = "remediation"    # ⚡ Misconception intervention
    PRACTICE = "practice"          # 💻 Deliberate application practice
    QUEUED = "queued"              # 📋 Next in natural curriculum
    LOCKED = "locked"              # 🔒 Blocked by unfulfilled prerequisites

class PathNodeType(str, Enum):
    FOUNDATIONAL = "Foundation"
    REVIEW = "Prerequisite Review"
    CORE_CONCEPT = "Core Concept"
    MISCONCEPTION_REMEDY = "Misconception Remedy"
    PRACTICE = "Targeted Practice"
    ADVANCEMENT = "Advanced Concept"
    CAPSTONE = "Capstone"

@dataclass
class LearningPathNode:
    """Represents a discrete milestone or instructional unit in the adaptive path."""
    id: str
    step_number: int
    title: str
    topic: str
    node_type: PathNodeType
    status: PathNodeStatus
    estimated_minutes: int
    summary: str
    pedagogical_rationale: str
    learning_objectives: List[str]
    is_remediated: bool = False
    is_blocking: bool = False

@dataclass
class PathChangeLog:
    """Records how and why the dynamic learning path adapted."""
    trigger: str
    nodes_completed: List[str] = field(default_factory=list)
    nodes_unlocked: List[str] = field(default_factory=list)
    nodes_added: List[str] = field(default_factory=list)
    summary_message: str = ""

@dataclass
class LearningPath:
    """Container for the student's dynamic curricular trajectory."""
    student_id: str
    subject: str
    nodes: List[LearningPathNode] = field(default_factory=list)
    change_log: Optional[PathChangeLog] = None
    version: int = 1

    @property
    def current_node(self) -> Optional[LearningPathNode]:
        for node in self.nodes:
            if node.status in (PathNodeStatus.ACTIVE_TARGET, PathNodeStatus.REVIEW, PathNodeStatus.REMEDIATION):
                return node
        for node in self.nodes:
            if node.status != PathNodeStatus.COMPLETED and node.status != PathNodeStatus.LOCKED:
                return node
        return self.nodes[0] if self.nodes else None

    @property
    def total_estimated_minutes(self) -> int:
        return sum(n.estimated_minutes for n in self.nodes if n.status != PathNodeStatus.COMPLETED)

    @property
    def completed_count(self) -> int:
        return sum(1 for n in self.nodes if n.status == PathNodeStatus.COMPLETED)

    @property
    def total_count(self) -> int:
        return len(self.nodes)

    @property
    def progress_percentage(self) -> float:
        if not self.nodes:
            return 0.0
        return round((self.completed_count / self.total_count) * 100.0, 1)

class DynamicLearningPathOptimizer:
    """
    Core Adaptive Engine for Phase 2.
    Dynamically recalculates curricular sequences using real-time Bayesian evidence,
    prerequisite DAG readiness, and detected misconceptions.
    """

    def __init__(self, prereq_graph: Optional[PrerequisiteGraph] = None):
        self.prereq_graph = prereq_graph or PrerequisiteGraph()

    def generate_path(
        self,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception],
        profile: Optional[StudentProfile] = None,
        previous_path: Optional[LearningPath] = None
    ) -> LearningPath:
        """
        Dynamically synthesize personalized learning trajectory.
        This algorithm responds in real time to new student scores and misconceptions.
        """
        nodes: List[LearningPathNode] = []
        topic_scores = {name: t.percentage for name, t in knowledge_state.topics.items()}
        step = 1

        # Map active misconceptions by topic
        active_misconceptions_by_topic: Dict[str, List[Misconception]] = {}
        remediated_misconceptions_by_topic: Dict[str, List[Misconception]] = {}
        for m in misconceptions:
            if m.status in (MisconceptionStatus.DETECTED, MisconceptionStatus.SUSPECTED):
                active_misconceptions_by_topic.setdefault(m.topic, []).append(m)
            elif m.status == MisconceptionStatus.REMEDIATED:
                remediated_misconceptions_by_topic.setdefault(m.topic, []).append(m)

        # Retrieve canonical curricular sequence
        canonical_topics = self.prereq_graph.get_all_topics_in_order()

        for topic_name in canonical_topics:
            t = knowledge_state.get_topic(topic_name)
            score = t.percentage if t else 0.0
            prereqs_of_topic = self.prereq_graph.get_prerequisites(topic_name)
            blocking_prereqs = self.prereq_graph.get_blocking_prerequisites(topic_name, topic_scores, min_threshold=70.0)

            # Check for strictly blocking prerequisites (critical gap < 60%)
            strictly_blocking = [
                p for p in prereqs_of_topic
                if topic_scores.get(p, 0.0) < 60.0
            ]
            has_unmet_critical_prereqs = len(strictly_blocking) > 0

            # Check if this topic is a prerequisite for a downstream struggling topic (< 70%)
            downstream_struggling = False
            for down_topic in canonical_topics[canonical_topics.index(topic_name)+1:]:
                down_t = knowledge_state.get_topic(down_topic)
                if down_t and down_t.percentage < 70.0:
                    prereqs_of_down = self.prereq_graph.get_prerequisites(down_topic)
                    if topic_name in prereqs_of_down:
                        downstream_struggling = True
                        break

            # CASE 1: Topic Mastered (>= 80%)
            if score >= 80.0:
                nodes.append(LearningPathNode(
                    id=f"node_{topic_name.lower().replace(' ', '_')}_mastered",
                    step_number=step,
                    title=f"{topic_name} (Mastered)",
                    topic=topic_name,
                    node_type=PathNodeType.FOUNDATIONAL,
                    status=PathNodeStatus.COMPLETED,
                    estimated_minutes=0,
                    summary=f"Solid foundational competence demonstrated ({score:.0f}% mastery).",
                    pedagogical_rationale=f"Score exceeds 80% threshold. Serves as active anchor for downstream concepts.",
                    learning_objectives=[f"Maintain mastery in {topic_name}"]
                ))
                step += 1

            # CASE 2: Prerequisite Review Needed (60% - 79% score while downstream topic is struggling)
            elif 60.0 <= score < 80.0 and downstream_struggling:
                nodes.append(LearningPathNode(
                    id=f"node_{topic_name.lower().replace(' ', '_')}_review",
                    step_number=step,
                    title=f"{topic_name} Review",
                    topic=topic_name,
                    node_type=PathNodeType.REVIEW,
                    status=PathNodeStatus.REVIEW,
                    estimated_minutes=15,
                    summary=f"Targeted review of key {topic_name} invariants ({score:.0f}% mastery).",
                    pedagogical_rationale=(
                        f"Mastery is at {score:.0f}%. Reinforcing {topic_name} prevents cognitive friction "
                        f"in dependent downstream modules."
                    ),
                    learning_objectives=[
                        f"Reinforce core {topic_name} edge cases",
                        f"Ensure stability before progressing"
                    ],
                    is_blocking=True
                ))
                step += 1

            # CASE 3: Active Knowledge Gap / Bottleneck (< 60% score or unmet prerequisites)
            elif score < 60.0 or (score < 80.0 and not downstream_struggling):
                if not has_unmet_critical_prereqs:
                    # Unlocked active target bottleneck!
                    active_misc = active_misconceptions_by_topic.get(topic_name, [])
                    rem_misc = remediated_misconceptions_by_topic.get(topic_name, [])

                    # 3a. Fundamentals
                    nodes.append(LearningPathNode(
                        id=f"node_{topic_name.lower().replace(' ', '_')}_fundamentals",
                        step_number=step,
                        title=f"{topic_name} Fundamentals",
                        topic=topic_name,
                        node_type=PathNodeType.CORE_CONCEPT,
                        status=PathNodeStatus.ACTIVE_TARGET,
                        estimated_minutes=25,
                        summary=f"Core structural concepts of {topic_name} (Current: {score:.0f}%).",
                        pedagogical_rationale=(
                            f"Identified as primary learning gap ({score:.0f}%). Prerequisite readiness confirmed."
                        ),
                        learning_objectives=[
                            f"Build mental model for {topic_name}",
                            f"Understand syntax and execution semantics"
                        ]
                    ))
                    step += 1

                    # 3b. Misconception Remediation (if active detected misconception exists!)
                    for misc in active_misc:
                        nodes.append(LearningPathNode(
                            id=f"node_misc_{misc.id}",
                            step_number=step,
                            title=f"Remediate: {misc.title}",
                            topic=topic_name,
                            node_type=PathNodeType.MISCONCEPTION_REMEDY,
                            status=PathNodeStatus.REMEDIATION,
                            estimated_minutes=20,
                            summary=f"Cognitive Bug Remediation: {misc.short_explanation[:120]}...",
                            pedagogical_rationale=(
                                f"Diagnosed misconception with {int(misc.confidence * 100)}% confidence. "
                                f"Must be resolved before open-ended practice."
                            ),
                            learning_objectives=[
                                f"Contrast flawed mental model with {misc.target_concept}",
                                "Verify zero regression across corrective exercises"
                            ],
                            is_blocking=True
                        ))
                        step += 1

                    # 3c. Remediated Misconceptions (show as completed milestone)
                    for misc in rem_misc:
                        nodes.append(LearningPathNode(
                            id=f"node_misc_{misc.id}",
                            step_number=step,
                            title=f"Resolved: {misc.title}",
                            topic=topic_name,
                            node_type=PathNodeType.MISCONCEPTION_REMEDY,
                            status=PathNodeStatus.COMPLETED,
                            estimated_minutes=0,
                            summary=f"Cognitive Bug Remediated: Successfully clarified {misc.target_concept}.",
                            pedagogical_rationale=f"Diagnosed misconception was successfully remediated via corrective evaluation.",
                            learning_objectives=[f"Maintain distinction in {misc.target_concept}"],
                            is_remediated=True
                        ))
                        step += 1

                    # 3c. Targeted Practice
                    nodes.append(LearningPathNode(
                        id=f"node_{topic_name.lower().replace(' ', '_')}_practice",
                        step_number=step,
                        title=f"{topic_name} Practice",
                        topic=topic_name,
                        node_type=PathNodeType.PRACTICE,
                        status=PathNodeStatus.PRACTICE,
                        estimated_minutes=30,
                        summary=f"Deliberate code exercises consolidating {topic_name}.",
                        pedagogical_rationale=(
                            f"Immediate application post-intervention cements learning and drives mastery to 80%."
                        ),
                        learning_objectives=[
                            f"Solve 3 progressive drills in {topic_name}",
                            "Confirm independent mastery"
                        ]
                    ))
                    step += 1

                else:
                    # Blocked topic
                    nodes.append(LearningPathNode(
                        id=f"node_{topic_name.lower().replace(' ', '_')}_locked",
                        step_number=step,
                        title=topic_name,
                        topic=topic_name,
                        node_type=PathNodeType.ADVANCEMENT,
                        status=PathNodeStatus.LOCKED,
                        estimated_minutes=40,
                        summary=f"Advanced module currently locked (Prerequisites missing).",
                        pedagogical_rationale=(
                            f"Locked until prerequisites [{', '.join(blocking_prereqs)}] reach >= 70%."
                        ),
                        learning_objectives=[
                            f"Unlock once {', '.join(blocking_prereqs)} are mastered"
                        ],
                        is_blocking=True
                    ))
                    step += 1

        # Detect changes vs previous path
        change_log = None
        if previous_path:
            old_statuses = {n.id: n.status for n in previous_path.nodes}
            new_completed = [n.title for n in nodes if n.status == PathNodeStatus.COMPLETED and old_statuses.get(n.id) != PathNodeStatus.COMPLETED]
            new_unlocked = [n.title for n in nodes if n.status != PathNodeStatus.LOCKED and old_statuses.get(n.id) == PathNodeStatus.LOCKED]
            
            summary_parts = []
            if new_completed:
                summary_parts.append(f"Completed: {', '.join(new_completed)}")
            if new_unlocked:
                summary_parts.append(f"Unlocked: {', '.join(new_unlocked)}")
            
            change_log = PathChangeLog(
                trigger="Knowledge state evidence update",
                nodes_completed=new_completed,
                nodes_unlocked=new_unlocked,
                summary_message=" | ".join(summary_parts) if summary_parts else "Recalculated path priorities."
            )

        new_version = (previous_path.version + 1) if previous_path else 1
        return LearningPath(
            student_id=knowledge_state.student_id,
            subject=knowledge_state.subject,
            nodes=nodes,
            change_log=change_log,
            version=new_version
        )

# Backwards compatibility alias
LearningPathOptimizer = DynamicLearningPathOptimizer
