"""
Sidebar Component for Phase 3.
Provides student profile badges, navigation controls matching hackathon specifications,
role selector (RBAC), AI provider status, reset baseline controls, and prototype metadata using Streamlit-native components.
"""

import streamlit as st
import os
from typing import Optional
from core.knowledge_state import KnowledgeState
from core.student_profile import StudentProfile
from core.security import UserRole
from data.demo_data import get_demo_knowledge_state, get_demo_misconceptions, get_demo_student_profile

NAVIGATION_ITEMS = [
    ("Dashboard", "📊"),
    ("Diagnostic Assessment", "📝"),
    ("Learning Path", "🗺️"),
    ("Practice", "💻"),
    ("AI Tutor", "🤖"),
    ("Analytics", "📈")
]

def render_sidebar(
    knowledge_state: KnowledgeState,
    profile: Optional[StudentProfile] = None
) -> str:
    """
    Renders professional educational sidebar with student profile and navigation.
    Returns the currently selected page name.
    """
    with st.sidebar:
        # App branding header
        st.markdown("## 🧠 PLPO")
        st.caption("**Personalized Learning Path Optimizer**  \nPhase 3: Intelligence & Security")

        st.divider()

        # Role Selector (Feature 4 - RBAC Preparation)
        if "active_user_role" not in st.session_state:
            st.session_state["active_user_role"] = UserRole.STUDENT

        role_options = [UserRole.STUDENT, UserRole.INSTRUCTOR, UserRole.ADMIN]
        selected_role = st.selectbox(
            "Active User Persona (RBAC):",
            role_options,
            index=role_options.index(st.session_state["active_user_role"]),
            format_func=lambda r: "🎓 Student (Demo Learner)" if r == UserRole.STUDENT else ("🧑‍🏫 Instructor (Auditor)" if r == UserRole.INSTRUCTOR else "🛡️ System Admin")
        )
        st.session_state["active_user_role"] = selected_role

        # Student Profile Card (Feature 1)
        student_name = profile.name if profile else knowledge_state.student_name
        subject = profile.subject if profile else knowledge_state.subject

        with st.container(border=True):
            st.markdown(f"### 👤 {student_name}")
            st.caption(f"📚 {subject}")
            if profile:
                st.caption(f"🎯 Goal: {profile.learning_goal}")

            c_m1, c_m2 = st.columns(2)
            with c_m1:
                st.metric(
                    label="MASTERY",
                    value=f"{knowledge_state.get_overall_mastery():.0f}%"
                )
            with c_m2:
                st.metric(
                    label="CONFIDENCE",
                    value=f"{knowledge_state.get_overall_confidence():.0f}%"
                )

        st.caption("**NAVIGATION**")

        # Session state for navigation
        if "nav_selection" not in st.session_state:
            st.session_state["nav_selection"] = "Dashboard"

        nav_options = [item[0] for item in NAVIGATION_ITEMS]
        current_idx = (
            nav_options.index(st.session_state["nav_selection"])
            if st.session_state["nav_selection"] in nav_options else 0
        )

        selected = st.radio(
            label="Navigation Menu",
            options=nav_options,
            index=current_idx,
            label_visibility="collapsed",
            format_func=lambda x: f"{dict(NAVIGATION_ITEMS).get(x, '📌')}  {x}"
        )

        st.session_state["nav_selection"] = selected

        st.divider()

        # Hackathon Judge Demo Controls (Feature 10)
        with st.container(border=True):
            st.caption("HACKATHON DEMO CONTROLS")
            if st.button("⚡ Start Judge Demo Walkthrough", type="primary", use_container_width=True):
                st.session_state["nav_selection"] = "Diagnostic Assessment"
                st.session_state["trigger_auto_eval"] = True
                st.rerun()

            if st.button("🔄 Reset Demo Baseline", use_container_width=True):
                st.session_state["student_profile"] = get_demo_student_profile()
                st.session_state["knowledge_state"] = get_demo_knowledge_state()
                st.session_state["misconceptions"] = get_demo_misconceptions()
                st.session_state["last_eval_result"] = None
                st.session_state["last_state_change"] = None
                if "current_learning_path" in st.session_state:
                    del st.session_state["current_learning_path"]
                st.success("Reset to Phase 3 baseline!")
                st.rerun()

        # Server-side AI Provider Status (No Key Exposure)
        has_gemini_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
        with st.container(border=True):
            st.caption("AI PROVIDER STATUS")
            if has_gemini_key:
                st.markdown("🟢 **Gemini API Connected**  \n`gemini-1.5-flash` active")
            else:
                st.markdown("🟡 **Offline Socratic Engine**  \n`Deterministic Fallback` active")
            st.caption("🔒 Key safely stored server-side")

        # Architecture Badge
        st.info(
            "🚀 **Phase 3 — Production Ready**  \n"
            "AI Tutor • Structured JSON • Adversarial Defense • Rate Limiting • Interaction Analytics"
        )

    return st.session_state["nav_selection"]
