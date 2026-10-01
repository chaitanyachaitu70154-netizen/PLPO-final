"""
Analytics Page for Phase 3: Telemetry & Knowledge Modeling from Actual Interaction Data.
Strict Guarantee: Zero fabricated statistics. All metrics, charts, and tables are derived
strictly from actual student attempts, knowledge state transitions, and diagnostic logs.
Built 100% with Streamlit-native components with zero raw HTML.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Optional
from core.knowledge_state import KnowledgeState, StateChangeRecord
from core.prerequisites import PrerequisiteGraph
from core.misconception import MisconceptionCatalog, Misconception, MisconceptionStatus
from core.assessment import AssessmentEngine, StudentAttemptRecord
from core.optimizer import LearningPath
from core.telemetry import get_system_health, METRICS
from core.cache import GLOBAL_CACHE
from core.background import GLOBAL_TASK_QUEUE

def render_analytics_page(
    knowledge_state: KnowledgeState,
    prereq_graph: PrerequisiteGraph,
    engine: Optional[AssessmentEngine] = None,
    misconceptions: Optional[List[Misconception]] = None,
    learning_path: Optional[LearningPath] = None
):
    """Render authentic, interaction-driven analytics interface."""
    st.title("📈 Curricular Telemetry & Learning Analytics")
    st.caption("Comprehensive evaluation derived strictly from verified student interactions, attempt records, and state transitions.")

    # Integrity & Transparency Notice (Feature 9 requirement)
    st.info(
        "🛡️ **Data Integrity Guarantee:** All metrics, quadrant mappings, and performance indicators below are computed "
        "**exclusively from actual recorded telemetry events**. The platform never fabricates or hallucinates improvement statistics."
    )

    attempts: List[StudentAttemptRecord] = engine.attempt_history if engine else []
    state_records: List[StateChangeRecord] = knowledge_state.history
    all_miscs: List[Misconception] = misconceptions or list(MisconceptionCatalog.get_catalog().values())

    # 1. High-Level Actual Performance KPIs
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    total_attempts = len(attempts)
    correct_attempts = sum(1 for a in attempts if a.is_correct)
    actual_accuracy = (correct_attempts / total_attempts * 100.0) if total_attempts > 0 else 0.0

    detected_misc_count = sum(1 for m in all_miscs if m.status in (MisconceptionStatus.DETECTED, MisconceptionStatus.SUSPECTED))
    resolved_misc_count = sum(1 for m in all_miscs if m.status == MisconceptionStatus.REMEDIATED)
    path_version = learning_path.version if learning_path else 1

    with m1:
        st.metric(
            label="ASSESSMENT SCORE",
            value=f"{actual_accuracy:.0f}%" if total_attempts > 0 else "N/A",
            delta=f"{correct_attempts}/{total_attempts} Correct" if total_attempts > 0 else "0 Attempts"
        )
    with m2:
        st.metric(
            label="OVERALL MASTERY",
            value=f"{knowledge_state.get_overall_mastery():.1f}%"
        )
    with m3:
        st.metric(
            label="CONFIDENCE INDEX",
            value=f"{knowledge_state.get_overall_confidence():.1f}%"
        )
    with m4:
        st.metric(
            label="BUGS DETECTED",
            value=str(detected_misc_count),
            delta="Active" if detected_misc_count > 0 else "None",
            delta_color="inverse"
        )
    with m5:
        st.metric(
            label="BUGS RESOLVED",
            value=str(resolved_misc_count),
            delta=f"{resolved_misc_count} Remediated",
            delta_color="normal"
        )
    with m6:
        st.metric(
            label="PATH RECALCULATIONS",
            value=f"v{path_version}",
            delta=f"{len(state_records)} State Updates"
        )

    st.divider()

    # 2. Topic Performance from Actual Interactions
    st.markdown("### 📊 Topic Performance (Actual Diagnostic Attempts)")
    if attempts:
        topic_stats = {}
        for a in attempts:
            stats = topic_stats.setdefault(a.topic, {"attempts": 0, "correct": 0, "total_time": 0.0, "confidences": []})
            stats["attempts"] += 1
            if a.is_correct:
                stats["correct"] += 1
            stats["total_time"] += a.response_time_seconds
            stats["confidences"].append(a.confidence_rating)

        t_rows = []
        for top, data in topic_stats.items():
            acc = (data["correct"] / data["attempts"]) * 100.0
            avg_time = data["total_time"] / data["attempts"]
            avg_conf = sum(data["confidences"]) / len(data["confidences"])
            t = knowledge_state.get_topic(top)
            t_rows.append({
                "Curricular Topic": top,
                "Current Mastery": f"{t.percentage:.1f}%" if t else "N/A",
                "Total Attempts": data["attempts"],
                "Correct": data["correct"],
                "Accuracy Rate": f"{acc:.1f}%",
                "Avg Confidence": f"{avg_conf:.1f}/5",
                "Avg Response Time": f"{avg_time:.1f}s"
            })

        st.dataframe(pd.DataFrame(t_rows), use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No diagnostic attempts recorded yet in this session. Complete questions in Diagnostic Assessment to generate topic telemetry.")

    st.divider()

    # 3. Confidence vs Accuracy & Metacognitive Calibration
    st.markdown("### ⚖️ Confidence vs. Accuracy Calibration")
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        if attempts:
            df_att = pd.DataFrame([
                {
                    "Question": a.question_id,
                    "Topic": a.topic,
                    "Confidence (1-5)": a.confidence_rating,
                    "Result": "Correct" if a.is_correct else "Incorrect",
                    "Quadrant": a.quadrant.value,
                    "Response Time (s)": a.response_time_seconds
                }
                for a in attempts
            ])
            fig_scatter = px.strip(
                df_att,
                x="Confidence (1-5)",
                y="Result",
                color="Result",
                color_discrete_map={"Correct": "#10B981", "Incorrect": "#EF4444"},
                hover_data=["Topic", "Quadrant", "Response Time (s)"],
                title="Actual Attempts: Self-Reported Confidence vs. Correctness"
            )
            fig_scatter.update_layout(height=320, plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            with st.container(border=True):
                st.caption("Awaiting diagnostic submissions to plot confidence vs. accuracy distribution.")
                st.info("When student submits answers with confidence ratings, each attempt is mapped into metacognitive quadrants.")

    with col_c2:
        # Mastery over Time from State Change Audit Records
        if state_records:
            df_hist = pd.DataFrame([
                {
                    "Time": r.timestamp,
                    "Topic": r.topic_name,
                    "New Mastery": r.new_mastery,
                    "Delta": r.new_mastery - r.old_mastery,
                    "Reason": r.trigger_reason
                }
                for r in state_records
            ])
            fig_time = px.line(
                df_hist,
                x="Time",
                y="New Mastery",
                color="Topic",
                markers=True,
                title="Knowledge State Mastery Transitions Over Time"
            )
            fig_time.update_layout(yaxis_range=[0, 100], height=320, plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            with st.container(border=True):
                st.caption("Awaiting knowledge state updates to plot real-time mastery transitions.")
                st.info("As the student answers diagnostic and follow-up questions, state transitions appear here.")

    st.divider()

    # 4. Learning Path Adaptation History & Change Log
    st.markdown("### 🗺️ Learning Path Changes & Curricular Adaptations")
    if learning_path and learning_path.change_log:
        cl = learning_path.change_log
        with st.container(border=True):
            st.markdown(f"**Latest Path Optimization (Version {learning_path.version}):** `{cl.summary_message}`")
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                st.caption("Milestones Mastered / Remediated:")
                if cl.nodes_completed:
                    for n in cl.nodes_completed:
                        st.markdown(f"- ✅ **{n}**")
                else:
                    st.write("None in this iteration")
            with col_l2:
                st.caption("Milestones Unlocked from Prerequisite Gates:")
                if cl.nodes_unlocked:
                    for u in cl.nodes_unlocked:
                        st.markdown(f"- 🔓 **{u}**")
                else:
                    st.write("Prerequisites still gating downstream topics")
    else:
        st.caption("Initial optimized trajectory established. Complete reassessment to trigger dynamic adaptations.")

    st.divider()

    # 5. Granular Telemetry & Production Observability
    tab_att, tab_trans, tab_ops = st.tabs([
        "📝 Detailed Attempt Telemetry Log",
        "🔄 State Delta Audit Records",
        "🖥️ Production Health & Prometheus Metrics"
    ])

    with tab_att:
        if attempts:
            att_display = []
            for a in reversed(attempts):
                att_display.append({
                    "Timestamp": a.timestamp,
                    "Question": a.question_id,
                    "Topic": a.topic,
                    "Outcome": "✅ Correct" if a.is_correct else "❌ Incorrect",
                    "Confidence": f"{a.confidence_rating}/5",
                    "Quadrant": a.quadrant.value,
                    "Response Time": f"{a.response_time_seconds:.1f}s",
                    "Misconception": a.misconception_detected or "None"
                })
            st.dataframe(pd.DataFrame(att_display), use_container_width=True, hide_index=True)
        else:
            st.write("No attempts logged yet.")

    with tab_trans:
        if state_records:
            trans_display = []
            for r in reversed(state_records):
                trans_display.append({
                    "Timestamp": r.timestamp,
                    "Topic": r.topic_name,
                    "Mastery Before": f"{r.old_mastery:.1f}%",
                    "Mastery After": f"{r.new_mastery:.1f}%",
                    "Mastery Delta": f"{(r.new_mastery - r.old_mastery):+.1f}%",
                    "Confidence Before": f"{r.old_confidence:.1f}%",
                    "Confidence After": f"{r.new_confidence:.1f}%",
                    "Confidence Delta": f"{(r.new_confidence - r.old_confidence):+.1f}%",
                    "Trigger Reason": r.trigger_reason
                })
            st.dataframe(pd.DataFrame(trans_display), use_container_width=True, hide_index=True)
        else:
            st.write("No state changes logged yet.")

    with tab_ops:
        st.markdown("#### 🏥 Live System Health & Service Diagnostics")
        health = get_system_health()

        col_h1, col_h2, col_h3, col_h4 = st.columns(4)
        with col_h1:
            st.metric(
                label="SYSTEM STATUS",
                value=health["status"],
                delta="Online & Healthy" if health["status"] == "HEALTHY" else "Degraded"
            )
        with col_h2:
            db_info = health["services"]["database"]
            st.metric(
                label="DATABASE ENGINE",
                value=f"{db_info['dialect'].upper()}",
                delta=f"{db_info['latency_ms']:.1f}ms Query Ping"
            )
        with col_h3:
            cache_info = health["services"]["cache"]
            st.metric(
                label="CACHE HIT RATE",
                value=f"{cache_info['hit_rate_pct']:.1f}%",
                delta=f"{cache_info['backend']} ({cache_info['size']} keys)"
            )
        with col_h4:
            ai_info = health["services"]["ai_provider"]
            st.metric(
                label="AI TUTOR PROVIDER",
                value="Gemini API" if ai_info["api_key_configured"] else "Deterministic Fallback",
                delta="Zero-Downtime Resilience"
            )

        st.markdown("#### ⚡ Cache Manager & Background Workers")
        c_stats = GLOBAL_CACHE.get_stats()
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.write(f"**Cache Backend:** `{c_stats['backend']}`")
            st.write(f"**Cached Objects:** `{c_stats['size']} / {c_stats['maxsize']}`")
        with col_c2:
            st.write(f"**Cache Hits:** `{c_stats['hits']}`")
            st.write(f"**Cache Misses:** `{c_stats['misses']}`")
        with col_c3:
            st.write(f"**Background Workers:** `{GLOBAL_TASK_QUEUE.max_workers} threads active`")
            st.write(f"**Recent Background Tasks:** `{len(GLOBAL_TASK_QUEUE.list_tasks())} queued/finished`")

        with st.expander("📊 Inspect Live Prometheus Scraping Text (/metrics)"):
            st.code(METRICS.export_metrics(), language="text")
