"""
Misconception Modeling and Diagnostic Detection module for Phase 2.
Implements cognitive bug detection, pedagogical interventions (explanation, example,
corrective question, follow-up check), and transient hypothesis tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

class MisconceptionSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class MisconceptionStatus(str, Enum):
    SUSPECTED = "suspected"     # Flagged once; hypothesis being tested
    DETECTED = "detected"       # Confirmed with high confidence or repeated errors
    REMEDIATED = "remediated"   # Successfully corrected via corrective check / follow-up

@dataclass
class CorrectiveQuestion:
    """A rapid targeted check to test if the student grasped the corrective intervention."""
    question_text: str
    options: List[str]
    correct_option_index: int
    explanation: str

@dataclass
class Misconception:
    """Represents a specific conceptual misconception diagnosed for a student."""
    id: str
    title: str
    topic: str
    target_concept: str
    severity: MisconceptionSeverity
    status: MisconceptionStatus
    confidence: float  # Diagnostic confidence (0.0 - 1.0)
    trigger_count: int = 1
    short_explanation: str = ""
    simple_example: str = ""
    corrective_question: Optional[CorrectiveQuestion] = None
    follow_up_question_id: Optional[str] = None
    code_example_flawed: str = ""
    code_example_corrected: str = ""
    symptoms: List[str] = field(default_factory=list)
    remedy_title: str = ""

    @property
    def description(self) -> str:
        return self.short_explanation

    def register_trigger(self, high_confidence: bool = False):
        """Register another observation of this misconception."""
        self.trigger_count += 1
        if high_confidence or self.trigger_count >= 2:
            self.status = MisconceptionStatus.DETECTED
            self.confidence = min(0.95, self.confidence + 0.15)
        else:
            self.confidence = min(0.80, self.confidence + 0.10)

    def mark_remediated(self):
        """Mark as remediated after successful corrective intervention."""
        self.status = MisconceptionStatus.REMEDIATED
        self.confidence = max(0.15, self.confidence - 0.50)

class MisconceptionCatalog:
    """Curated knowledge base of recognized programming misconceptions for Phase 2."""

    @staticmethod
    def get_catalog() -> Dict[str, Misconception]:
        return {
            "misc_param_vs_arg": Misconception(
                id="misc_param_vs_arg",
                title="Parameter vs Argument",
                topic="Functions",
                target_concept="Function Signatures & Invocation",
                severity=MisconceptionSeverity.HIGH,
                status=MisconceptionStatus.DETECTED,
                confidence=0.88,
                trigger_count=2,
                short_explanation=(
                    "You may be treating parameters (the variable placeholders defined in 'def func(x):') "
                    "and arguments (the concrete values supplied when calling 'func(5)') as interchangeable. "
                    "Parameters act as receiving containers at definition time; arguments fill those containers at runtime."
                ),
                simple_example=(
                    "Analogy: A postal slot labeled 'Recipient' is a Parameter. "
                    "The actual letter with 'Alice' written on it dropped into the slot is the Argument."
                ),
                code_example_flawed="""# Misconception: Re-assigning parameter inside function
def greet_user(name):
    name = "Alice"  # Overwrites caller argument!
    return f"Hello, {name}!"
greet_user("Bob")  # Always returns 'Alice'""",
                code_example_corrected="""# Correct: Parameter acts as a receiver
def greet_user(name):  # 'name' is the PARAMETER
    return f"Hello, {name}!"
greet_user("Bob")  # 'Bob' is the ARGUMENT (returns 'Hello, Bob!')""",
                corrective_question=CorrectiveQuestion(
                    question_text="In `def multiply(x, y): return x * y`, what are `x` and `y`?",
                    options=[
                        "Arguments",
                        "Parameters",
                        "Global constants",
                        "Return variables"
                    ],
                    correct_option_index=1,
                    explanation="Correct! `x` and `y` are declared in the function header, so they are formal Parameters."
                ),
                follow_up_question_id="q_func_param_followup",
                symptoms=[
                    "Attempting to read parameter variables outside the function scope",
                    "Assuming arguments must have identical names to parameters",
                    "Hardcoding internal variables instead of passing arguments"
                ],
                remedy_title="Visual Parameter-Argument Mapping & Scope Micro-Drill"
            ),

            "misc_fifo_vs_lifo": Misconception(
                id="misc_fifo_vs_lifo",
                title="Confusing FIFO and LIFO in Stacks vs Queues",
                topic="Data Structures",
                target_concept="Queue vs Stack Processing Order",
                severity=MisconceptionSeverity.HIGH,
                status=MisconceptionStatus.SUSPECTED,
                confidence=0.75,
                trigger_count=1,
                short_explanation=(
                    "A Stack follows LIFO (Last-In, First-Out) like a stack of cafeteria trays. "
                    "A Queue follows FIFO (First-In, First-Out) like people waiting in a movie ticket line."
                ),
                simple_example=(
                    "- Stack (LIFO): The plate placed last on top is taken first.\n"
                    "- Queue (FIFO): The person who arrived first at the line is served first."
                ),
                code_example_flawed="""# Misconception: Calling a stack FIFO
stack = []
stack.append("Task1")
stack.append("Task2")
# Thinking stack.pop() removes Task1 first!
item = stack.pop()  # Removes 'Task2' (LIFO), not 'Task1'""",
                code_example_corrected="""# Correct: Queue follows FIFO
from collections import deque
queue = deque(["Customer1", "Customer2"])
served = queue.popleft()  # Serves 'Customer1' first (FIFO)""",
                corrective_question=CorrectiveQuestion(
                    question_text="If you push A, then push B onto a Stack, which element is popped first?",
                    options=[
                        "Element A (FIFO)",
                        "Element B (LIFO)",
                        "Both at the same time",
                        "Neither, stacks do not allow removal"
                    ],
                    correct_option_index=1,
                    explanation="Correct! A stack is LIFO (Last-In, First-Out), so the last pushed item 'B' is popped first."
                ),
                follow_up_question_id="q_ds_fifo_followup",
                symptoms=[
                    "Calling stack operations FIFO",
                    "Expecting pop() on a list to return the first inserted element"
                ],
                remedy_title="Queue vs Stack Interactive Pipeline"
            ),

            "misc_loop_bounds": Misconception(
                id="misc_loop_bounds",
                title="Off-by-One in Range Iterations",
                topic="Loops",
                target_concept="Half-Open Interval range(start, stop)",
                severity=MisconceptionSeverity.MEDIUM,
                status=MisconceptionStatus.SUSPECTED,
                confidence=0.64,
                trigger_count=1,
                short_explanation=(
                    "In Python, `range(start, stop)` is a half-open interval `[start, stop)`: "
                    "it includes `start`, but stops immediately BEFORE `stop`."
                ),
                simple_example="range(1, 5) generates values 1, 2, 3, 4 (4 iterations, NOT 5).",
                code_example_flawed="for i in range(1, 5): # Iterates 1, 2, 3, 4 only",
                code_example_corrected="for i in range(1, 6): # Iterates 1, 2, 3, 4, 5",
                corrective_question=CorrectiveQuestion(
                    question_text="What is the final value of `i` in `for i in range(0, 3):`?",
                    options=["3", "2", "1", "0"],
                    correct_option_index=1,
                    explanation="Correct! The loop visits 0, 1, and 2. It terminates before reaching 3."
                ),
                follow_up_question_id="q_loops_bound_followup",
                symptoms=["Loop iterates n-1 times", "IndexError on boundary checks"],
                remedy_title="Range Boundary Step-Through"
            ),

            "misc_return_vs_print": Misconception(
                id="misc_return_vs_print",
                title="Return vs Print",
                topic="Functions",
                target_concept="Function Value Passing vs Console Output",
                severity=MisconceptionSeverity.HIGH,
                status=MisconceptionStatus.REMEDIATED,
                confidence=0.20,
                trigger_count=1,
                short_explanation=(
                    "`print()` merely displays text to the terminal screen (a side-effect). "
                    "`return` passes a tangible data value back into the caller's expression."
                ),
                simple_example="print() is a billboard; return is handing a physical envelope to someone.",
                code_example_flawed="def add(a, b): print(a + b)\nx = add(2, 3) # x is None!",
                code_example_corrected="def add(a, b): return a + b\nx = add(2, 3) # x is 5",
                corrective_question=CorrectiveQuestion(
                    question_text="If a function has no `return` statement, what value does it evaluate to?",
                    options=["0", "Empty string", "None", "Error"],
                    correct_option_index=2,
                    explanation="Correct! Functions without an explicit return statement return None in Python."
                ),
                follow_up_question_id="q_func_return_followup",
                symptoms=["Expecting print to store values into variables", "Missing return keyword"],
                remedy_title="Value Pipeline & Scope Flow"
            )
        }

    @classmethod
    def get_by_id(cls, misc_id: str) -> Optional[Misconception]:
        return cls.get_catalog().get(misc_id)

    @classmethod
    def get_parameter_vs_argument(cls) -> Misconception:
        return cls.get_catalog()["misc_param_vs_arg"]

    @classmethod
    def get_fifo_vs_lifo(cls) -> Misconception:
        return cls.get_catalog()["misc_fifo_vs_lifo"]
