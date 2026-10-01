"""
Demo Data Module for Phase 2.
Provides verified baseline data structures matching hackathon specifications:
- Student: Demo Student
- Subject: Python Programming
- Topic Scores:
    Variables: 92%
    Conditions: 84%
    Loops: 68%
    Functions: 43%
    Lists / Data Structures: 57%
- Diagnosed Misconception: Parameter vs Argument
- Recommended Learning Path:
    Loops Review -> Functions Fundamentals -> Parameter vs Argument ->
    Functions Practice -> Lists -> Data Structures
"""

from typing import List, Dict, Optional
from core.student_profile import StudentProfile
from core.knowledge_state import KnowledgeState, TopicMastery, LearningStatus
from core.misconception import MisconceptionCatalog, Misconception
from core.prerequisites import PrerequisiteGraph
from core.optimizer import DynamicLearningPathOptimizer, LearningPath
from core.assessment import DiagnosticQuestion

def get_demo_student_profile() -> StudentProfile:
    """Build and return StudentProfile (Feature 1)."""
    return StudentProfile(
        student_id="STU-2026-PY-089",
        name="Demo Student",
        education_level="Undergraduate Computer Science",
        subject="Python Programming",
        current_level="Intermediate Foundations",
        learning_goal="Master Modular Function Design & Data Structures",
        preferred_pace="Moderate (3 modules/week)"
    )

def get_demo_knowledge_state() -> KnowledgeState:
    """Build and return student knowledge state matching the exact hackathon requirements."""
    ks = KnowledgeState(
        student_id="STU-2026-PY-089",
        student_name="Demo Student",
        subject="Python Programming"
    )

    # Hackathon Required Topic Scores & Confidence
    ks.set_topic_score("Programming Basics", 95.0, confidence=96.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Variables", 92.0, confidence=95.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Conditions", 84.0, confidence=88.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Loops", 68.0, confidence=72.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Functions", 43.0, confidence=31.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Lists", 57.0, confidence=62.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Data Structures", 45.0, confidence=50.0, reason="Diagnostic Baseline")
    ks.set_topic_score("Object-Oriented Programming", 25.0, confidence=20.0, reason="Diagnostic Baseline")

    # Set initial active misconception status on Functions
    func_topic = ks.get_topic("Functions")
    if func_topic:
        func_topic.misconception_status["misc_param_vs_arg"] = "detected"
        func_topic.learning_status = LearningStatus.REMEDIATING

    return ks

def get_demo_misconceptions() -> List[Misconception]:
    """Return active diagnosed misconceptions for Demo Student."""
    param_vs_arg = MisconceptionCatalog.get_parameter_vs_argument()
    return [param_vs_arg]

def get_demo_learning_path(
    ks: Optional[KnowledgeState] = None,
    misc: Optional[List[Misconception]] = None
) -> LearningPath:
    """Generate the dynamic learning path for Demo Student."""
    state = ks or get_demo_knowledge_state()
    misconceptions = misc or get_demo_misconceptions()
    optimizer = DynamicLearningPathOptimizer()
    return optimizer.generate_path(state, misconceptions)

def get_demo_diagnostic_questions() -> List[DiagnosticQuestion]:
    """
    Curated diagnostic questions with misconception distractors and prerequisite links.
    """
    return [
        DiagnosticQuestion(
            id="q_func_param_01",
            question="Examine the code snippet below. Which statement correctly describes the roles of 'multiplier' and '5'?",
            topic="Functions",
            difficulty="Medium",
            options=[
                "Both 'multiplier' and '5' are parameters of the scale_value function.",
                "'multiplier' is the parameter defined in the signature; '5' is the argument passed during invocation.",
                "'5' is the parameter received; 'multiplier' is an argument assigned globally.",
                "Neither is an argument; both are local variables created inside the stack frame."
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! 'multiplier' is the formal parameter (a named placeholder in the function definition 'def'), "
                "while '5' is the actual concrete argument passed when 'scale_value(5)' is executed."
            ),
            prerequisite_topic="Loops",
            misconception_category="misc_param_vs_arg",
            distractor_misconceptions={
                0: "misc_param_vs_arg",  # Conflating parameter and argument terminology
                2: "misc_param_vs_arg",  # Inverting parameter vs argument roles
            },
            code_snippet=(
                "def scale_value(multiplier):\n"
                "    factor = 10\n"
                "    return factor * multiplier\n\n"
                "output = scale_value(5)\n"
                "print(output)"
            )
        ),

        DiagnosticQuestion(
            id="q_ds_fifo_01",
            question="Which data structure strictly operates on a First-In, First-Out (FIFO) processing order?",
            topic="Data Structures",
            difficulty="Medium",
            options=[
                "Stack",
                "Queue",
                "Binary Search Tree",
                "Hash Map"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! A Queue follows First-In, First-Out (FIFO) order: the element entered first is processed first. "
                "A Stack follows Last-In, First-Out (LIFO)."
            ),
            prerequisite_topic="Functions",
            misconception_category="misc_fifo_vs_lifo",
            distractor_misconceptions={
                0: "misc_fifo_vs_lifo"  # Confusing Stack (LIFO) with Queue (FIFO)
            },
            code_snippet=None
        ),

        DiagnosticQuestion(
            id="q_loops_bound_01",
            question="How many times will the print statement execute in the loop below?",
            topic="Loops",
            difficulty="Easy",
            options=[
                "6 times (from 1 to 6)",
                "4 times (for values 2, 3, 4, 5)",
                "5 times (for values 2, 3, 4, 5, 6)",
                "3 times (for values 3, 4, 5)"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! In Python, range(start, stop) includes 'start' (2) up to but NOT including 'stop' (6). "
                "The iterated values are 2, 3, 4, 5 — exactly 4 iterations."
            ),
            prerequisite_topic="Conditions",
            misconception_category="misc_loop_bounds",
            distractor_misconceptions={
                2: "misc_loop_bounds"  # Off-by-one error (inclusive stop assumption)
            },
            code_snippet=(
                "counter = 0\n"
                "for i in range(2, 6):\n"
                "    counter += 1\n"
                "print(f'Ran {counter} times')"
            )
        ),

        DiagnosticQuestion(
            id="q_return_scope_01",
            question="What will be the value stored in the variable 'bill' after executing this code?",
            topic="Functions",
            difficulty="Medium",
            options=[
                "15.0",
                "None",
                "'Tax: 15.0'",
                "SyntaxError: missing return statement"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! Because calculate_tax lacks an explicit 'return' statement, Python implicitly returns None. "
                "print() merely displays output on the screen and does not pass a value to the caller."
            ),
            prerequisite_topic="Loops",
            misconception_category="misc_return_vs_print",
            distractor_misconceptions={
                0: "misc_return_vs_print"  # Conflating print side-effects with returned expressions
            },
            code_snippet=(
                "def calculate_tax(amount):\n"
                "    tax = amount * 0.15\n"
                "    print(f'Tax: {tax}')\n\n"
                "bill = calculate_tax(100)"
            )
        )
    ]

def get_follow_up_question(misconception_id: str) -> DiagnosticQuestion:
    """Return targeted follow-up question for reassessment after cognitive intervention."""
    follow_ups = {
        "misc_param_vs_arg": DiagnosticQuestion(
            id="q_func_param_followup",
            question="A developer writes `def register(username, email): ...` and executes `register('dev_user', 'user@test.org')`. In this invocation, what is `'dev_user'`?",
            topic="Functions",
            difficulty="Medium",
            options=[
                "A parameter declared in the function header",
                "An argument passed to the function call",
                "A global variable scope declaration",
                "A return value expression"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! `'dev_user'` is the concrete value supplied during invocation, making it an Argument. "
                "`username` is the receiving Parameter."
            ),
            prerequisite_topic="Loops",
            misconception_category="misc_param_vs_arg",
            distractor_misconceptions={0: "misc_param_vs_arg"},
            code_snippet="def register(username, email):\n    print(f'Registered: {username}')\n\nregister('dev_user', 'user@test.org')"
        ),

        "misc_fifo_vs_lifo": DiagnosticQuestion(
            id="q_ds_fifo_followup",
            question="In an operating system printer spooler, print jobs must be printed in the exact order they arrive (the first document queued is printed first). Which data structure model must this spooler implement?",
            topic="Data Structures",
            difficulty="Medium",
            options=[
                "Stack (Last-In, First-Out)",
                "Queue (First-In, First-Out)",
                "Priority Tree",
                "Hash Set"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! First-In, First-Out (FIFO) processing is the defining behavior of a Queue. "
                "Stacks use LIFO where the most recently added item is handled first."
            ),
            prerequisite_topic="Functions",
            misconception_category="misc_fifo_vs_lifo",
            distractor_misconceptions={0: "misc_fifo_vs_lifo"},
            code_snippet=None
        ),

        "misc_loop_bounds": DiagnosticQuestion(
            id="q_loops_bound_followup",
            question="In Python, which range call will iterate through the numbers 0, 1, 2, 3, 4, and 5 (a total of 6 numbers)?",
            topic="Loops",
            difficulty="Easy",
            options=[
                "range(0, 5)",
                "range(0, 6)",
                "range(1, 5)",
                "range(1, 6)"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! range(0, 6) starts at 0 and stops before 6, visiting 0, 1, 2, 3, 4, 5 (exactly 6 items)."
            ),
            prerequisite_topic="Conditions",
            misconception_category="misc_loop_bounds",
            distractor_misconceptions={0: "misc_loop_bounds"},
            code_snippet=None
        ),

        "misc_return_vs_print": DiagnosticQuestion(
            id="q_func_return_followup",
            question="How do you pass a calculated value back from a function so another part of the program can store it in a variable?",
            topic="Functions",
            difficulty="Medium",
            options=[
                "Use the print() function inside the body",
                "Use the return statement with the value",
                "Assign it to a global variable with no return",
                "Use the echo keyword"
            ],
            correct_answer_index=1,
            explanation=(
                "Correct! Only the `return` statement passes a value back out of the function stack frame into the caller's variable."
            ),
            prerequisite_topic="Loops",
            misconception_category="misc_return_vs_print",
            distractor_misconceptions={0: "misc_return_vs_print"},
            code_snippet=None
        )
    }
    return follow_ups.get(
        misconception_id,
        follow_ups["misc_param_vs_arg"]
    )

def get_demo_historical_progress() -> List[Dict]:
    """Historical progression data for analytics tracking."""
    return [
        {"week": "Week 1", "date": "2026-09-07", "Variables": 72, "Conditions": 55, "Loops": 40, "Functions": 20, "Lists": 25, "Data Structures": 20, "overall": 42.4},
        {"week": "Week 2", "date": "2026-09-14", "Variables": 85, "Conditions": 70, "Loops": 54, "Functions": 30, "Lists": 38, "Data Structures": 32, "overall": 55.4},
        {"week": "Week 3", "date": "2026-09-21", "Variables": 90, "Conditions": 80, "Loops": 62, "Functions": 38, "Lists": 48, "Data Structures": 40, "overall": 63.6},
        {"week": "Week 4 (Current)", "date": "2026-09-28", "Variables": 92, "Conditions": 84, "Loops": 68, "Functions": 43, "Lists": 57, "Data Structures": 45, "overall": 68.8}
    ]

def get_demo_practice_drills() -> List[Dict]:
    """Legacy practice challenges dictionary matching old interface."""
    from core.practice_generator import TargetedPracticeGenerator
    gen = TargetedPracticeGenerator()
    drills = gen._drill_repository
    legacy = []
    for d in drills:
        legacy.append({
            "id": d.id,
            "title": d.title,
            "topic": d.topic,
            "difficulty": d.difficulty,
            "prompt": d.prompt,
            "starter_code": d.starter_code or d.code_snippet or "",
            "hints": d.hints
        })
    return legacy
