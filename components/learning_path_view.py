"""
Interactive Learning Path Node Visualization Component.
Built using 100% Streamlit-native containers, subheaders, info boxes, and metrics.
Completely avoids LaTeX / KaTeX rendering so all text is displayed as normal UI content.
"""

import streamlit as st
from typing import List
from core.optimizer import LearningPath, LearningPathNode, PathNodeStatus, PathNodeType

def render_connected_learning_path(learning_path: LearningPath, interactive: bool = True):
    """
    Renders connected learning-path nodes in responsive educational layout using native components.
    Guarantees all text is rendered as standard UI text/markdown with zero LaTeX/math interpretation.
    """
    # Summary Bar
    with st.container(border=True):
        col_s1, col_s2 = st.columns([3, 2])
        with col_s1:
            st.markdown(
                f"**Curricular Path Progress:** `{learning_path.total_count} Sequence Milestones`  •  "
                f"⏱️ Total Estimated Time: **{learning_path.total_estimated_minutes} mins**"
            )
        with col_s2:
            st.markdown("**Target Goal:** `Modular Python Proficiency`")

    # Nodes Sequence
    for i, node in enumerate(learning_path.nodes):
        is_active = (node.status in (PathNodeStatus.ACTIVE_TARGET, PathNodeStatus.ACTIVE))
        is_remedy = (node.node_type == PathNodeType.MISCONCEPTION_REMEDY)
        is_locked = (node.status == PathNodeStatus.LOCKED)
        is_completed = (node.status == PathNodeStatus.COMPLETED)
        is_review = (node.status == PathNodeStatus.REVIEW)

        if is_completed:
            status_badge = "✓ [MASTERED / RESOLVED]"
        elif is_active:
            status_badge = "🎯 [CURRENT ACTIVE TARGET]"
        elif is_review:
            status_badge = "⚠ [PREREQUISITE REVIEW]"
        elif is_remedy:
            status_badge = "⚡ [MISCONCEPTION REMEDIATION]"
        elif is_locked:
            status_badge = "🔒 [LOCKED]"
        else:
            status_badge = f"[Step {node.step_number}]"

        type_badge = f"`{node.node_type.value}`"

        # Sanitize any accidental dollar signs to prevent KaTeX triggering
        safe_title = node.title.replace("$", "\\$")
        safe_summary = node.summary.replace("$", "\\$")
        safe_rationale = node.pedagogical_rationale.replace("$", "\\$")

        with st.container(border=True):
            col_h1, col_h2 = st.columns([3, 1])
            with col_h1:
                st.subheader(f"Step {node.step_number}: {safe_title}")
                st.caption(f"Status: **{status_badge}**  •  Category: {type_badge}")
            with col_h2:
                st.metric(
                    label="ESTIMATED TIME",
                    value=f"{node.estimated_minutes} min" if node.estimated_minutes > 0 else "Mastered"
                )

            st.write(safe_summary)
            st.info(f"Why this step: {safe_rationale}")
            st.caption(f"Topic Domain: **{node.topic}**  •  Curricular Milestones: **{len(node.learning_objectives)} Objectives**")

            if interactive:
                with st.expander(f"View Step {node.step_number} Objectives & Action Plan"):
                    st.markdown(f"**Learning Objectives for {safe_title}:**")
                    for obj in node.learning_objectives:
                        safe_obj = obj.replace("$", "\\$")
                        st.markdown(f"- ✅ {safe_obj}")
                    col_btn1, col_btn2 = st.columns([1, 4])
                    with col_btn1:
                        if is_completed:
                            btn_label = "Review Completed"
                        elif is_active:
                            btn_label = "Begin Step"
                        elif "Practice" in node.title:
                            btn_label = "Practice Drill"
                        else:
                            btn_label = "Preview Module"

                        if st.button(btn_label, key=f"btn_node_{node.id}_{i}", disabled=is_locked):
                            if "Practice" in node.title:
                                st.session_state["nav_selection"] = "Practice"
                            else:
                                st.session_state["nav_selection"] = "Diagnostic Assessment"
                            st.rerun()
                    with col_btn2:
                        if is_remedy:
                            st.caption("⚠️ High-priority cognitive remediation step. Prioritized before open-ended practice.")
                        elif is_locked:
                            st.caption("🔒 Locked until foundational prerequisite competencies reach >= 70%.")
                        elif is_completed:
                            st.caption("✓ Concept demonstrated with stable mastery. Serves as active anchor.")
                        else:
                            st.caption(f"Estimated duration: {node.estimated_minutes} minutes.")
