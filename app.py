"""
Personalized Learning Path Optimizer (PLPO) - Main Application Entrypoint.
Phase 2: Core MVP - Dynamic Adaptive Knowledge Modeling & Learning Loop.
Run with: streamlit run app.py
"""

import streamlit as st
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.config import CONFIG
from data.demo_data import (
    get_demo_student_profile,
    get_demo_knowledge_state,
    get_demo_misconceptions,
    get_demo_learning_path
)
from core.prerequisites import PrerequisiteGraph
from core.optimizer import DynamicLearningPathOptimizer, LearningPath
from core.assessment import AssessmentEngine
from core.student_profile import StudentProfile
from components.sidebar import render_sidebar
from pages.dashboard import render_dashboard
from pages.assessment import render_assessment
from pages.learning_path import render_learning_path_page
from pages.practice import render_practice_page
from pages.tutor import render_tutor_page
from pages.analytics import render_analytics_page

# Configure Streamlit page settings
st.set_page_config(
    page_title=f"{CONFIG.APP_NAME} | PLPO",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global Custom CSS for clean educational AI aesthetic with ZERO raw HTML leaks
st.markdown("""
<style>
    /* Google Fonts & Base Typography */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Main container background and spacing */
    .stApp {
        background-color: #F8FAFC;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }
    
    /* Button enhancements */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.88rem;
        padding: 0.45rem 1rem;
        transition: all 0.2s ease;
    }
    
    .stButton > button[kind="primary"] {
        background: #2563EB;
        border: 1px solid #1D4ED8;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: #1D4ED8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1E293B;
        background-color: #FFFFFF;
        border-radius: 8px;
    }
    
    /* Sidebar polish */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Divider subtle color */
    hr {
        margin: 1.5rem 0;
        border-color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize persistent student state from database and Phase 4 service components."""
    # Ensure database schema is initialized and baseline data seeded
    if "db_initialized" not in st.session_state:
        from core.db.init_db import init_database, seed_database_if_empty
        init_database()
        seed_database_if_empty()
        st.session_state["db_initialized"] = True

    if "prereq_graph" not in st.session_state:
        st.session_state["prereq_graph"] = PrerequisiteGraph()

    if "optimizer" not in st.session_state:
        st.session_state["optimizer"] = DynamicLearningPathOptimizer(st.session_state["prereq_graph"])

    if "assessment_engine" not in st.session_state:
        st.session_state["assessment_engine"] = AssessmentEngine()

    if "adaptive_service" not in st.session_state:
        from core.services.adaptive_service import AdaptiveService
        st.session_state["adaptive_service"] = AdaptiveService(
            assessment_engine=st.session_state["assessment_engine"],
            prereq_graph=st.session_state["prereq_graph"],
            optimizer=st.session_state["optimizer"]
        )

    if "student_profile" not in st.session_state:
        from core.services.student_service import StudentService
        st.session_state["student_profile"] = StudentService.get_or_create_student("STU-2026-PY-089")

    if "knowledge_state" not in st.session_state:
        adaptive_srv: AdaptiveService = st.session_state["adaptive_service"]
        st.session_state["knowledge_state"] = adaptive_srv.load_or_init_knowledge_state("STU-2026-PY-089")

    if "misconceptions" not in st.session_state:
        st.session_state["misconceptions"] = get_demo_misconceptions()

    if "tutor_service" not in st.session_state:
        from core.ai.tutor_service import AITutorService
        st.session_state["tutor_service"] = AITutorService()

def main():
    initialize_session_state()

    profile = st.session_state["student_profile"]
    ks = st.session_state["knowledge_state"]
    misc = st.session_state["misconceptions"]
    prereq_graph = st.session_state["prereq_graph"]
    optimizer = st.session_state["optimizer"]
    assessment_engine = st.session_state["assessment_engine"]
    tutor_service = st.session_state["tutor_service"]

    # Maintain or generate dynamic learning path
    if "current_learning_path" not in st.session_state:
        st.session_state["current_learning_path"] = optimizer.generate_path(
            knowledge_state=ks,
            misconceptions=misc,
            profile=profile
        )
    learning_path = st.session_state["current_learning_path"]

    # Render sidebar and get current selected navigation item
    selected_page = render_sidebar(ks, profile)

    # Page Routing
    if selected_page == "Dashboard":
        render_dashboard(ks, learning_path, misc, profile=profile)
    elif selected_page == "Diagnostic Assessment":
        render_assessment(ks, assessment_engine, optimizer=optimizer, misconceptions=misc)
    elif selected_page == "Learning Path":
        render_learning_path_page(ks, learning_path, misc, optimizer)
    elif selected_page == "Practice":
        render_practice_page(ks, misc)
    elif selected_page == "AI Tutor":
        render_tutor_page(ks, misc, tutor_service=tutor_service)
    elif selected_page == "Analytics":
        render_analytics_page(ks, prereq_graph, engine=assessment_engine, misconceptions=misc, learning_path=learning_path)
    else:
        render_dashboard(ks, learning_path, misc, profile=profile)

if __name__ == "__main__":
    main()
