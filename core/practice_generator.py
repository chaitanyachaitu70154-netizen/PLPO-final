"""
Targeted Practice Generator module for Phase 2.
Generates deliberate, personalized practice drills based on:
- Active knowledge gaps / weak topics (< 70% mastery)
- Diagnosed misconceptions (e.g. Parameter vs Argument, FIFO vs LIFO)
- Curricular prerequisite status (ensuring readiness)
- Historical student mistakes and difficulty calibration.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
from core.knowledge_state import KnowledgeState
from core.misconception import Misconception, MisconceptionStatus
from core.prerequisites import PrerequisiteGraph

class PracticeType(str, Enum):
    CONCEPT_IDENTIFICATION = "Concept Identification"
    CODE_ANALYSIS = "Code Analysis"
    DEBUG_FIX = "Code Debugging & Fix"
    WRITE_SNIPPET = "Implementation"

@dataclass
class PracticeDrill:
    """Represents a targeted deliberate practice problem."""
    id: str
    title: str
    topic: str
    difficulty: str  # Easy, Medium, Hard
    practice_type: PracticeType
    prompt: str
    code_snippet: Optional[str] = None
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    targeted_misconception: Optional[str] = None
    options: Optional[List[str]] = None
    correct_option_index: Optional[int] = None
    expected_output: Optional[str] = None
    pedagogical_reason: str = ""

class TargetedPracticeGenerator:
    """
    Generates targeted practice drills tailored to learner deficiencies.
    Avoids random generation; strictly addresses diagnosed cognitive bugs and prerequisite needs.
    """

    def __init__(self, prereq_graph: Optional[PrerequisiteGraph] = None):
        self.prereq_graph = prereq_graph or PrerequisiteGraph()
        self._drill_repository = self._build_drill_repository()

    def _build_drill_repository(self) -> List[PracticeDrill]:
        return [
            # Functions: Parameter vs Argument Drills
            PracticeDrill(
                id="drill_param_arg_id",
                title="Identify Parameters vs Arguments in Call Stack",
                topic="Functions",
                difficulty="Easy",
                practice_type=PracticeType.CONCEPT_IDENTIFICATION,
                prompt="Examine the code snippet below. Identify which identifiers are Parameters and which are Arguments.",
                code_snippet="""def compute_tax(subtotal, tax_rate):  # Line 1
    return subtotal * tax_rate

final_bill = compute_tax(150.0, 0.08)   # Line 4""",
                options=[
                    "'subtotal' and 'tax_rate' are arguments; '150.0' and '0.08' are parameters.",
                    "'subtotal' and 'tax_rate' are parameters (in def); '150.0' and '0.08' are arguments (in call).",
                    "All four items are local parameters.",
                    "All four items are runtime arguments."
                ],
                correct_option_index=1,
                hints=[
                    "Look at Line 1 with 'def': identifiers declared here act as receiving containers (Parameters).",
                    "Look at Line 4 with 'compute_tax(...)': the concrete numbers passed are Arguments."
                ],
                targeted_misconception="misc_param_vs_arg",
                pedagogical_reason="Directly targets the parameter vs argument conceptual conflation."
            ),

            PracticeDrill(
                id="drill_param_shadowing_fix",
                title="Debug: Fix Parameter Shadowing Bug",
                topic="Functions",
                difficulty="Medium",
                practice_type=PracticeType.DEBUG_FIX,
                prompt=(
                    "A student wrote this function to calculate circle area, but it always returns "
                    "the area for radius 10 regardless of the argument passed. Fix the bug!"
                ),
                starter_code="""import math

def calculate_circle_area(radius):
    radius = 10  # <-- Bug: Overwriting the parameter!
    return math.pi * (radius ** 2)

# Test call:
print(calculate_circle_area(5))  # Should print ~78.54""",
                solution_code="""import math

def calculate_circle_area(radius):
    return math.pi * (radius ** 2)

print(calculate_circle_area(5))""",
                hints=[
                    "The parameter 'radius' already receives the caller's argument (5).",
                    "Remove the line re-assigning 'radius = 10' so the function uses the caller's value."
                ],
                targeted_misconception="misc_param_vs_arg",
                pedagogical_reason="Reinforces that parameters hold caller-supplied arguments and must not be overwritten."
            ),

            # Functions: Return vs Print
            PracticeDrill(
                id="drill_return_vs_print_fix",
                title="Debug: Captured None Return Value",
                topic="Functions",
                difficulty="Medium",
                practice_type=PracticeType.DEBUG_FIX,
                prompt=(
                    "The caller expects 'total' to hold the discounted amount, but 'total' is None. "
                    "Replace the print side-effect with a proper return statement."
                ),
                starter_code="""def apply_discount(price, discount):
    discounted = price - (price * discount)
    print(discounted)  # Bug: caller gets None!

total = apply_discount(100, 0.20)
print(f"Total to pay: {total}")""",
                solution_code="""def apply_discount(price, discount):
    discounted = price - (price * discount)
    return discounted

total = apply_discount(100, 0.20)
print(f"Total to pay: {total}")""",
                hints=[
                    "print() only outputs to the screen and does not send a value back to the caller.",
                    "Use the 'return' keyword to pass 'discounted' back into the 'total' variable."
                ],
                targeted_misconception="misc_return_vs_print",
                pedagogical_reason="Resolves conflation between terminal output and expression return values."
            ),

            # Data Structures: FIFO vs LIFO
            PracticeDrill(
                id="drill_queue_fifo_order",
                title="Implement FIFO Order with collections.deque",
                topic="Data Structures",
                difficulty="Medium",
                practice_type=PracticeType.CODE_ANALYSIS,
                prompt="Which method call on a `collections.deque` object removes the item that was inserted FIRST (FIFO)?",
                code_snippet="""from collections import deque

queue = deque()
queue.append("Customer_A")  # Arrived 1st
queue.append("Customer_B")  # Arrived 2nd
queue.append("Customer_C")  # Arrived 3rd

# Which operation correctly serves Customer_A first?
served = queue._____()""",
                options=[
                    "pop() (Removes last element: Customer_C)",
                    "popleft() (Removes first element: Customer_A - FIFO)",
                    "remove_first()",
                    "dequeue_now()"
                ],
                correct_option_index=1,
                hints=[
                    "pop() removes from the right end (LIFO behavior like a stack).",
                    "popleft() removes from the left end, giving First-In, First-Out (FIFO) queue behavior."
                ],
                targeted_misconception="misc_fifo_vs_lifo",
                pedagogical_reason="Contrasts queue FIFO operations with stack LIFO operations in Python."
            ),

            # Loops: Range Bounds
            PracticeDrill(
                id="drill_range_bounds_check",
                title="Fix Off-By-One Range Iteration",
                topic="Loops",
                difficulty="Easy",
                practice_type=PracticeType.CODE_ANALYSIS,
                prompt="You need a loop that prints the numbers from 1 to 10 inclusive. Which range expression is correct?",
                code_snippet="""# We need to output: 1 2 3 4 5 6 7 8 9 10
for n in range(_____):
    print(n, end=" ")""",
                options=[
                    "range(1, 10)",
                    "range(1, 11)",
                    "range(0, 10)",
                    "range(10)"
                ],
                correct_option_index=1,
                hints=[
                    "Python ranges stop at 'stop - 1'.",
                    "To include 10, the stop parameter must be 10 + 1 = 11."
                ],
                targeted_misconception="misc_loop_bounds",
                pedagogical_reason="Directly addresses half-open interval boundaries in loop iterations."
            )
        ]

    def generate_drills(
        self,
        knowledge_state: KnowledgeState,
        misconceptions: List[Misconception],
        limit: int = 3
    ) -> List[PracticeDrill]:
        """
        Synthesize prioritized practice drills matching active gaps and diagnosed misconceptions.
        """
        weak_topics = [t.topic_name for t in knowledge_state.get_weak_topics()]
        active_misc_ids = [m.id for m in misconceptions if m.status in (MisconceptionStatus.DETECTED, MisconceptionStatus.SUSPECTED)]

        matched_drills: List[PracticeDrill] = []

        # 1. First priority: Drills matching active misconceptions
        for drill in self._drill_repository:
            if drill.targeted_misconception and drill.targeted_misconception in active_misc_ids:
                if drill not in matched_drills:
                    matched_drills.append(drill)

        # 2. Second priority: Drills matching weak topics
        for drill in self._drill_repository:
            if drill.topic in weak_topics and drill not in matched_drills:
                matched_drills.append(drill)

        # 3. Third priority: General drills if list is below limit
        for drill in self._drill_repository:
            if drill not in matched_drills:
                matched_drills.append(drill)
            if len(matched_drills) >= limit:
                break

        return matched_drills[:limit]
