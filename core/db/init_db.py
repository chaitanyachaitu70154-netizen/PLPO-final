"""
Database initialization and seeding module for Phase 4.
Runs schema migration, creates tables, and seeds the baseline student and curriculum embeddings.
"""

import os
import math
import random
import logging
from core.db.session import init_database, get_engine
from core.db.repository import (
    StudentRepository,
    KnowledgeStateRepository,
    MisconceptionRepository,
    LearningPathRepository,
    CurriculumEmbeddingRepository
)
from data.demo_data import (
    get_demo_student_profile,
    get_demo_knowledge_state,
    get_demo_misconceptions,
    get_demo_learning_path
)

logger = logging.getLogger("plpo.init_db")

def generate_mock_embedding(seed_word: str, dim: int = 768) -> list:
    """Generate a deterministic normalized mock vector for testing when LLM API is offline."""
    rng = random.Random(seed_word)
    vec = [rng.gauss(0, 1) for _ in range(dim)]
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]

def seed_database_if_empty() -> None:
    """Seed baseline student profile, knowledge state, and curriculum embeddings if not already in DB."""
    profile = get_demo_student_profile()
    existing_prof = StudentRepository.get_profile(profile.student_id)

    if not existing_prof:
        logger.info(f"Seeding baseline student profile: {profile.name} ({profile.student_id})")
        StudentRepository.save_profile(profile)

        # Seed Knowledge State
        ks = get_demo_knowledge_state()
        KnowledgeStateRepository.save_knowledge_state(ks)
        logger.info("Seeded baseline topic masteries and calibration states.")

        # Seed Misconceptions
        miscs = get_demo_misconceptions()
        for m in miscs:
            MisconceptionRepository.save_misconception_state(profile.student_id, m)
        logger.info("Seeded diagnosed misconceptions.")

        # Seed Initial Learning Path
        path = get_demo_learning_path(ks, miscs)
        LearningPathRepository.save_path(profile.student_id, path)
        logger.info("Seeded baseline dynamic learning path.")

        # Seed Semantic Curriculum Embeddings for Vector Search
        seed_chunks = [
            (
                "Functions",
                "Parameter vs Argument Distinction",
                "In Python, a parameter is the variable listed inside parentheses in the function header (def). An argument is the actual value or reference passed to the function when invoked.",
                {"difficulty": "Medium", "module": "Functions Core"}
            ),
            (
                "Data Structures",
                "FIFO Queue Invariant",
                "A Queue adheres strictly to the First-In, First-Out (FIFO) principle. Elements are appended to the rear and evicted from the front.",
                {"difficulty": "Medium", "module": "Linear Collections"}
            ),
            (
                "Loops",
                "Loop Invariants & Off-by-One Guarding",
                "For loops in Python iterate over iterables. The range(start, stop) function excludes the stop boundary, requiring range(0, n) to execute n iterations.",
                {"difficulty": "Easy", "module": "Control Flow"}
            ),
            (
                "Object-Oriented Programming",
                "Encapsulation and Instance State",
                "Classes define prototypes for objects. The self parameter references the concrete instance executing the method, binding instance attributes in the local scope.",
                {"difficulty": "Hard", "module": "OOP Foundations"}
            )
        ]

        for topic, subtopic, text, meta in seed_chunks:
            embedding = generate_mock_embedding(f"{topic}:{subtopic}", 768)
            CurriculumEmbeddingRepository.store_embedding(
                topic_name=topic,
                subtopic_title=subtopic,
                content_text=text,
                embedding=embedding,
                metadata=meta
            )
        logger.info("Seeded curriculum chunks and vector embeddings.")
    else:
        logger.info("Database already seeded with student profile.")

def bootstrap() -> None:
    """Complete bootstrap workflow: schema creation + data seeding."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logger.info("Starting PLPO database bootstrap...")
    init_database()
    seed_database_if_empty()
    logger.info("PLPO database bootstrap completed successfully.")

if __name__ == "__main__":
    bootstrap()
