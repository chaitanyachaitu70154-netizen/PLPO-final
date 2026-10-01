"""
Prerequisites Graph and Curricular Dependency Modeling module for Phase 2.
Defines the DAG of Python Programming concepts:
Programming Basics -> Variables -> Conditions -> Loops -> Functions -> Data Structures -> Object-Oriented Programming.
Ensures learning paths respect cognitive readiness and foundational prerequisites.
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field

@dataclass
class TopicNode:
    """Represents a topic node within the curricular dependency graph."""
    id: str
    name: str
    description: str
    prerequisites: List[str] = field(default_factory=list)
    suggested_hours: float = 2.0
    level: str = "Foundations"

class PrerequisiteGraph:
    """
    Directed Acyclic Graph representing dependencies between programming concepts.
    """
    def __init__(self):
        self._nodes: Dict[str, TopicNode] = {}
        self._initialize_graph()

    def _initialize_graph(self):
        """Construct verified curricular sequence matching Phase 2 specification."""
        nodes = [
            TopicNode(
                id="programming_basics",
                name="Programming Basics",
                description="Algorithms, computation concepts, input/output flow, and execution environment.",
                prerequisites=[],
                suggested_hours=1.0,
                level="Foundations"
            ),
            TopicNode(
                id="variables",
                name="Variables",
                description="Memory assignment, data types (int, float, str, bool), and basic expressions.",
                prerequisites=["programming_basics"],
                suggested_hours=1.5,
                level="Foundations"
            ),
            TopicNode(
                id="conditions",
                name="Conditions",
                description="Boolean logic, if/elif/else control branching, and comparison operators.",
                prerequisites=["variables"],
                suggested_hours=2.0,
                level="Control Flow"
            ),
            TopicNode(
                id="loops",
                name="Loops",
                description="Iteration constructs: for loops, while loops, range(), break and continue.",
                prerequisites=["conditions"],
                suggested_hours=2.5,
                level="Control Flow"
            ),
            TopicNode(
                id="functions",
                name="Functions",
                description="Function definitions, parameters vs arguments, return values, and local frame scope.",
                prerequisites=["loops"],
                suggested_hours=3.5,
                level="Modular Design"
            ),
            TopicNode(
                id="lists",
                name="Lists",
                description="Sequential mutable lists, indexing, slicing, appending, and list comprehensions.",
                prerequisites=["functions"],
                suggested_hours=2.5,
                level="Sequences & Collections"
            ),
            TopicNode(
                id="data_structures",
                name="Data Structures",
                description="Stacks, queues, dictionaries, sets, and associative collections.",
                prerequisites=["lists"],
                suggested_hours=4.0,
                level="Collections & Structures"
            ),
            TopicNode(
                id="oop",
                name="Object-Oriented Programming",
                description="Classes, objects, attributes, methods, inheritance, and encapsulation.",
                prerequisites=["data_structures"],
                suggested_hours=4.5,
                level="Advanced Paradigms"
            ),
        ]
        for node in nodes:
            self.add_node(node)

    def add_node(self, node: TopicNode) -> None:
        self._nodes[node.name] = node

    def get_node(self, topic_name: str) -> Optional[TopicNode]:
        return self._nodes.get(topic_name)

    def get_prerequisites(self, topic_name: str) -> List[str]:
        """Return direct prerequisite topic names for a given topic."""
        node = self._nodes.get(topic_name)
        if not node:
            return []
        resolved = []
        for prereq_id in node.prerequisites:
            for k, v in self._nodes.items():
                if v.id == prereq_id:
                    resolved.append(k)
        return resolved

    def are_prerequisites_met(
        self,
        topic_name: str,
        topic_scores: Dict[str, float],
        min_threshold: float = 70.0
    ) -> bool:
        """Check if all direct prerequisites meet the minimum mastery threshold."""
        prereqs = self.get_prerequisites(topic_name)
        for prereq in prereqs:
            score = topic_scores.get(prereq, 0.0)
            if score < min_threshold:
                return False
        return True

    def get_blocking_prerequisites(
        self,
        topic_name: str,
        topic_scores: Dict[str, float],
        min_threshold: float = 70.0
    ) -> List[str]:
        """Return which prerequisites are currently below the required threshold."""
        prereqs = self.get_prerequisites(topic_name)
        blocking = []
        for prereq in prereqs:
            score = topic_scores.get(prereq, 0.0)
            if score < min_threshold:
                blocking.append(prereq)
        return blocking

    def get_all_topics_in_order(self) -> List[str]:
        """Return canonical ordered sequence of all topics in curriculum."""
        return [
            "Programming Basics",
            "Variables",
            "Conditions",
            "Loops",
            "Functions",
            "Lists",
            "Data Structures",
            "Object-Oriented Programming"
        ]
