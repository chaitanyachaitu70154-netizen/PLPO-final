"""
UI Cards and Visual Container Components.
Built entirely using Streamlit-native components (st.container, st.metric, st.progress).
Zero raw HTML/CSS strings to prevent any browser escaping or plain-text rendering issues.
"""

import streamlit as st
from typing import List, Optional
from core.knowledge_state import TopicMastery, MasteryStatus
from core.misconception import Misconception
from core.optimizer import LearningPathNode
from utils.config import CONFIG, get_mastery_label

def render_metric_card(
    title: str,
    value: str,
    subtitle: str,
    badge_text: str = "",
    badge_color: str = "primary",
    icon: str = "📊",
    help_text: str = ""
):
    """
    Render a clean metric card using Streamlit-native st.container and st.metric.
    Zero raw HTML strings are used, eliminating any risk of literal <span> text rendering.
    """
    with st.container(border=True):
        delta_color = (
            "normal" if badge_color == "success"
            else ("inverse" if badge_color == "danger" else "off")
        )
        st.metric(
            label=f"{icon}  {title.upper()}",
            value=value,
            delta=badge_text if badge_text else None,
            delta_color=delta_color,
            help=help_text if help_text else None
        )
        if subtitle:
            st.caption(subtitle)

def render_topic_progress_card(topic: TopicMastery):
    """Render an individual topic mastery card using native container and progress bar."""
    pct = topic.percentage
    label = get_mastery_label(pct)

    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 2])
        with col_t1:
            st.markdown(f"**{topic.topic_name}**")
        with col_t2:
            st.markdown(f"**{pct:.0f}%** `({label})`")
        
        # Native Streamlit progress bar (clamped to 0.0 - 1.0)
        st.progress(min(1.0, max(0.0, pct / 100.0)))
        
        st.caption(f"Confidence: {topic.confidence_percentage:.0f}%  •  Last active: {topic.last_updated}")

def render_next_activity_hero(node: LearningPathNode, on_start_click=None):
    """Render a prominent hero banner card for recommended next activity using native components."""
    with st.container(border=True):
        st.markdown(
            f"🎯 **RECOMMENDED NEXT ACTIVITY**  •  ⏱️ **{node.estimated_minutes} min duration**  •  🏷️ **{node.node_type.value}**"
        )
        st.subheader(node.title)
        st.write(node.summary)
        st.info(f"💡 **AI Optimizer Rationale:** {node.pedagogical_rationale}")

def render_misconception_alert(misconception: Misconception):
    """Render a dedicated educational alert highlighting detected misconceptions using native components."""
    with st.container(border=True):
        st.markdown(f"### ⚠️ Diagnosed Misconception: {misconception.title}")
        st.markdown(
            f"**Severity:** `{misconception.severity.value}`  •  "
            f"**Diagnostic Confidence:** `{int(misconception.confidence * 100)}%`"
        )
        st.write(misconception.description)
        with st.expander("🔍 Typical Manifestations / Symptoms", expanded=True):
            for symptom in misconception.symptoms:
                st.markdown(f"- {symptom}")
        st.warning(f"🛠️ **Remedy:** {misconception.remedy_title} *(Sequenced as Step 3 in Path)*")
