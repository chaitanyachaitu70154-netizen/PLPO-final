"""
Configuration settings and design constants for Personalized Learning Path Optimizer.
"""

from dataclasses import dataclass
import os
from typing import Dict

@dataclass(frozen=True)
class AppConfig:
    APP_NAME: str = "Personalized Learning Path Optimizer"
    APP_SHORT_NAME: str = "PLPO"
    APP_TAGLINE: str = "Adaptive AI-driven knowledge modeling and dynamic curricular path optimization"
    APP_VERSION: str = "1.0.0-phase1"
    THEME_PRIMARY: str = "#2563EB"       # Modern Indigo/Blue
    THEME_SECONDARY: str = "#4F46E5"     # Deep Indigo
    COLOR_SUCCESS: str = "#10B981"       # Emerald (Mastered)
    COLOR_WARNING: str = "#F59E0B"       # Amber (Developing/Review)
    COLOR_DANGER: str = "#EF4444"        # Coral/Red (Needs Focus/Misconception)
    COLOR_INFO: str = "#06B6D4"          # Cyan
    COLOR_MUTED: str = "#64748B"         # Slate Muted
    COLOR_BG_CARD: str = "#FFFFFF"
    COLOR_BG_PAGE: str = "#F8FAFC"
    COLOR_BORDER: str = "#E2E8F0"
    
    # Mastery Thresholds
    MASTERY_HIGH_THRESHOLD: float = 0.80      # >= 80%: Mastered
    MASTERY_MEDIUM_THRESHOLD: float = 0.60    # 60% - 79%: Proficient / Review
    # < 60%: Needs Focus / Critical
    
    # Phase notice
    PHASE_LABEL: str = "Phase 1 Prototype"
    PHASE_DISCLAIMER: str = (
        "Phase 1 provides the foundational knowledge modeling, UI architecture, and diagnostic "
        "pathway visualization. Full real-time LLM inference and dynamic BKT updates will connect in Phase 2."
    )

CONFIG = AppConfig()

def get_mastery_color(score: float) -> str:
    """Return appropriate hex color code based on mastery score (0.0 to 1.0 or 0 to 100)."""
    normalized = score / 100.0 if score > 1.0 else score
    if normalized >= CONFIG.MASTERY_HIGH_THRESHOLD:
        return CONFIG.COLOR_SUCCESS
    elif normalized >= CONFIG.MASTERY_MEDIUM_THRESHOLD:
        return CONFIG.COLOR_WARNING
    else:
        return CONFIG.COLOR_DANGER

def get_mastery_label(score: float) -> str:
    """Return descriptive mastery level label."""
    normalized = score / 100.0 if score > 1.0 else score
    if normalized >= CONFIG.MASTERY_HIGH_THRESHOLD:
        return "Mastered"
    elif normalized >= CONFIG.MASTERY_MEDIUM_THRESHOLD:
        return "Developing"
    else:
        return "Needs Focus"

def clean_html(html: str) -> str:
    """
    Strips leading and trailing whitespace from each line of an HTML string.
    Crucial for Streamlit st.markdown to prevent CommonMark from treating lines
    with 4+ spaces of indentation as indented code blocks (<pre><code>).
    """
    return "\n".join(line.strip() for line in html.strip().splitlines())

def render_html(html: str) -> None:
    """Safely renders HTML via Streamlit without risking CommonMark code block escaping."""
    import streamlit as st
    st.markdown(clean_html(html), unsafe_allow_html=True)

