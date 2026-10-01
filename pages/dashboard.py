"""
Dashboard Page: Core Landing and Knowledge State Overview for Phase 2.
Implements all Phase 1 & Phase 2 dashboard requirements:
- Project name & tagline
- Student profile (name, education level, current level, goal, pace - Feature 1)
- Overall mastery & confidence metrics (Features 3 & 4)
- Live knowledge state change audit notifications (Feature 9 & 10)
- Strong topics & weak topics breakdown
- Possible misconceptions alerts (Feature 5)
- Current dynamic learning path connected node flow (Feature 7)
- Recommended next activity hero
- Interactive Plotly progress charts
Built 100% using Streamlit-native components with zero raw HTML leakage.
"""

import streamlit as st
from typing import Optional, List
from core.knowledge_state import KnowledgeState, LearningStatus, StateChangeRecord
from core.optimizer import LearningPath
from core.misconception import Misconception, MisconceptionStatus
from core.student_profile import StudentProfile
from components.cards import (
    render_metric_card,
    render_topic_progress_card,
    render_next_activity_hero,
    render_misconception_alert
)
from components.charts import (
    plot_topic_mastery_barchart,
    plot_competency_radar,
    plot_calibration_quadrant,
    plot_historical_trajectory
)
from components.learning_path_view import render_connected_learning_path
from utils.config import CONFIG

def render_dashboard(
    knowledge_state: KnowledgeState,
    learning_path: LearningPath,
    misconceptions: List[Misconception],
    profile: Optional[StudentProfile] = None
):
    """Render the primary dashboard interface using Streamlit-native components."""

    # Top Header: Project Name & Student Badge
    col_hdr1, col_hdr2 = st.columns([3, 2])
    with col_hdr1:
        st.title(f"🧠 {CONFIG.APP_NAME}")
        st.caption(CONFIG.APP_TAGLINE)

    with col_hdr2:
        with st.container(border=True):
            c_s1, c_s2, c_s3 = st.columns(3)
            with c_s1:
                st.caption("STUDENT")
                st.markdown(f"**{profile.name if profile else knowledge_state.student_name}**")
            with c_s2:
                st.caption("CURRICULUM")
                st.markdown(f"**{knowledge_state.subject}**")
            with c_s3:
                st.caption("STATUS")
                st.markdown("🟢 **Active Learner**")

    # Feature 1: Student Profile Banner Container
    with st.container(border=True):
        c_p1, c_p2, c_p3, c_p4 = st.columns(4)
        with c_p1:
            st.caption("EDUCATION LEVEL")
            st.markdown(f"🎓 **{profile.education_level if profile else 'Undergraduate Computer Science'}**")
        with c_p2:
            st.caption("CURRENT PROFICIENCY")
            st.markdown(f"📈 **{profile.current_level if profile else 'Intermediate Foundations'}**")
        with c_p3:
            st.caption("TARGET LEARNING GOAL")
            st.markdown(f"🎯 **{profile.learning_goal if profile else 'Master Modular Function Design'}**")
        with c_p4:
            st.caption("LEARNING PACE")
            st.markdown(f"⚡ **{profile.preferred_pace if profile else 'Moderate (3 modules/week)'}**")

    # Feature 9 & 10: Real-time State Change Banner (if an assessment was completed)
    recent_change: Optional[StateChangeRecord] = st.session_state.get("last_state_change")
    if recent_change:
        with st.container(border=True):
            st.success(
                f"🔄 **REAL-TIME LEARNING UPDATE DETECTED:** Knowledge state and curricular path recalculated at {recent_change.timestamp}! "
                f"**{recent_change.topic_name}:** `{recent_change.old_mastery:.1f}% → {recent_change.new_mastery:.1f}%` "
                f"({recent_change.new_mastery - recent_change.old_mastery:+.1f}%)"
            )

    # 1. High-Level Performance Metrics Row
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    overall_mastery = knowledge_state.get_overall_mastery()
    overall_conf = knowledge_state.get_overall_confidence()
    strong_topics = knowledge_state.get_strong_topics()
    weak_topics = knowledge_state.get_weak_topics()

    active_misc = [m for m in misconceptions if m.status in (MisconceptionStatus.DETECTED, MisconceptionStatus.SUSPECTED)]
    remediated_misc = [m for m in misconceptions if m.status == MisconceptionStatus.REMEDIATED]

    with m_col1:
        render_metric_card(
            title="Overall Mastery",
            value=f"{overall_mastery:.1f}%",
            subtitle="Curricular competency weighted score",
            badge_text="Mastered" if overall_mastery >= 80 else "Developing",
            badge_color="success" if overall_mastery >= 80 else "warning",
            icon="🎯"
        )

    with m_col2:
        render_metric_card(
            title="Confidence Index",
            value=f"{overall_conf:.1f}%",
            subtitle="Self-reported & calibrated metric",
            badge_text="Calibrated",
            badge_color="info",
            icon="⚖️"
        )

    with m_col3:
        render_metric_card(
            title="Strong Topics",
            value=f"{len(strong_topics)}",
            subtitle=f"{', '.join([t.topic_name for t in strong_topics])}",
            badge_text="≥ 80% Mastered",
            badge_color="success",
            icon="🏆"
        )

    with m_col4:
        if active_misc:
            render_metric_card(
                title="Active Misconceptions",
                value=f"{len(active_misc)}",
                subtitle=f"{active_misc[0].title} detected",
                badge_text="Action Required",
                badge_color="danger",
                icon="⚠️"
            )
        else:
            render_metric_card(
                title="Active Misconceptions",
                value="0",
                subtitle=f"{len(remediated_misc)} remediated!",
                badge_text="All Clear",
                badge_color="success",
                icon="✅"
            )

    st.write("")

    # 2. Recommended Next Activity Hero Banner
    next_node = learning_path.current_node
    if next_node:
        render_next_activity_hero(next_node)

    # 3. Possible Misconception Section
    if active_misc:
        for misc in active_misc:
            render_misconception_alert(misc)
            with st.expander(f"🔍 Examine Cognitive Error Analysis & Code Comparison: {misc.title}"):
                c_flawed, c_fixed = st.columns(2)
                with c_flawed:
                    st.markdown("**❌ Flawed Code Pattern (Detected Mental Model):**")
                    st.code(misc.code_example_flawed, language="python")
                    st.caption("Notice how hardcoding parameter variables breaks caller flexibility.")
                with c_fixed:
                    st.markdown("**✅ Corrected Mental Model:**")
                    st.code(misc.code_example_corrected, language="python")
                    st.caption("Parameters serve as receivers; callers inject dynamic arguments.")

    if remediated_misc:
        for rm in remediated_misc:
            st.success(f"✅ **Remediated Misconception: {rm.title}** — Correct mental models successfully validated via follow-up reassessment!")

    # 4. Progress Charts Row
    st.markdown("### 📊 Knowledge State Analytics & Profiling")
    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        fig_bar = plot_topic_mastery_barchart(knowledge_state)
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_c2:
        fig_radar = plot_competency_radar(knowledge_state)
        st.plotly_chart(fig_radar, use_container_width=True)

    chart_c3, chart_c4 = st.columns(2)
    with chart_c3:
        fig_quad = plot_calibration_quadrant(knowledge_state)
        st.plotly_chart(fig_quad, use_container_width=True)

    with chart_c4:
        from data.demo_data import get_demo_historical_progress
        fig_hist = plot_historical_trajectory(get_demo_historical_progress())
        st.plotly_chart(fig_hist, use_container_width=True)

    st.divider()

    # 5. Strong Topics vs Weak Topics Deep-Dive
    st.markdown("### 🔍 Topic Diagnostic Breakdown")
    topic_col1, topic_col2 = st.columns(2)

    with topic_col1:
        st.markdown(f"#### 🟢 Strong Topics ({len(strong_topics)})")
        for t in strong_topics:
            render_topic_progress_card(t)
        st.info("💡 **Pedagogical note:** Solid mastery in strong topics provides a secure cognitive foundation for advancing to dependent modules.")

    with topic_col2:
        st.markdown(f"#### 🟠 Weak Topics & Review Needed ({len(weak_topics)})")
        for t in weak_topics:
            render_topic_progress_card(t)
        st.warning("⚠️ **Optimizer Alert:** Prerequisite bottlenecks isolate downstream concepts until foundational competence reaches ≥ 70%.")

    st.divider()

    # 6. Current Learning Path Visualization
    st.markdown("### 🗺️ Dynamic Curricular Learning Path")
    st.caption(
        "Sequenced dynamically based on prerequisite dependencies, mastery deficits, "
        "and active cognitive misconceptions."
    )
    render_connected_learning_path(learning_path, interactive=True)
