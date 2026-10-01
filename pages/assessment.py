"""
Diagnostic Assessment Page for Phase 2.
Implements the full adaptive diagnostic and intervention loop:
1. Question presentation with prerequisites, difficulty, and misconception mapping
2. 5-point metacognitive confidence rating
3. Distractor-based misconception detection (Feature 5)
4. Metacognitive confidence quadrant analysis (Feature 4)
5. 4-part intervention: Short explanation, Simple example, Corrective check, Follow-up assessment
6. Real-time Knowledge State updating (Feature 9)
7. Dynamic learning path recalculation and visible state-change diffs (Feature 10)
Built with 100% Streamlit-native components with zero raw HTML.
"""

import streamlit as st
import time
from typing import List, Optional
from core.knowledge_state import KnowledgeState, StateChangeRecord
from core.assessment import AssessmentEngine, DiagnosticQuestion, AssessmentEvaluationResult
from core.misconception import Misconception, MisconceptionStatus
from core.confidence import ConfidenceAnalyzer, ConfidenceRating, MetacognitiveQuadrant
from core.optimizer import DynamicLearningPathOptimizer, LearningPath
from data.demo_data import get_demo_diagnostic_questions, get_follow_up_question

def render_assessment(
    knowledge_state: KnowledgeState,
    engine: AssessmentEngine,
    optimizer: Optional[DynamicLearningPathOptimizer] = None,
    misconceptions: Optional[List[Misconception]] = None
):
    """Render the complete Phase 2 Diagnostic Assessment and Adaptive Intervention flow."""
    st.title("📝 Diagnostic Assessment & Adaptive Interventions")
    st.caption("Probing conceptual mental models, assessing metacognitive calibration, and providing instant targeted remediation.")

    # Feature 10: Complete Hackathon Demo Mode Visual Pipeline
    with st.container(border=True):
        st.markdown("### 🎯 Hackathon Judge Interactive Demo Pipeline (Feature 10)")
        st.caption("Experience the full adaptive loop in real time. Click through or use the 1-click demo button below:")
        st.markdown(
            "`1. Assessment` ➔ `2. Wrong Answer` ➔ `3. Confidence` ➔ `4. Misconception` ➔ "
            "`5. Intervention` ➔ `6. Practice` ➔ `7. Reassessment` ➔ `8. State Update` ➔ `9. Changed Path`"
        )
        
        c_guide1, c_guide2 = st.columns([2, 1])
        with c_guide1:
            st.info(
                "💡 **Quick Demo Instructions:** Select **Question 1** below, choose the distractor **'Both multiplier and 5 are parameters'**, "
                "select **Confidence = 4 (Confident)**, and click **Submit Diagnostic Response** to see the 4-part intervention and path recalculation!"
            )
        with c_guide2:
            if st.button("⚡ 1-Click Demo Auto-Run (Q1)", type="primary", use_container_width=True):
                st.session_state["auto_selected_opt"] = 0
                st.session_state["auto_conf"] = 4
                st.session_state["trigger_auto_eval"] = True
                st.rerun()

    questions = get_demo_diagnostic_questions()

    # Session state initialization for question flow
    if "current_q_index" not in st.session_state:
        st.session_state["current_q_index"] = 0
    if "q_start_time" not in st.session_state:
        st.session_state["q_start_time"] = time.time()
    if "last_eval_result" not in st.session_state:
        st.session_state["last_eval_result"] = None
    if "last_state_change" not in st.session_state:
        st.session_state["last_state_change"] = None

    # Tabs for Questions
    q_labels = [f"Q{i+1}: {q.topic} ({q.difficulty})" for i, q in enumerate(questions)]
    selected_tab_idx = st.radio(
        label="Select Diagnostic Question:",
        options=list(range(len(questions))),
        format_func=lambda i: q_labels[i],
        horizontal=True,
        key="diagnostic_q_tab_radio"
    )

    q = questions[selected_tab_idx]

    # Auto-eval trigger handling for 1-click judge demo
    if st.session_state.get("trigger_auto_eval") and selected_tab_idx == 0:
        st.session_state["trigger_auto_eval"] = False
        eval_result = engine.evaluate_submission(
            question=q,
            selected_index=0,
            confidence_rating=4,
            response_time_seconds=8.5
        )
        st.session_state["last_eval_result"] = eval_result
        st.session_state["last_q_id"] = q.id
        st.session_state["q_start_time"] = time.time()

    # Display Question Metadata in Clean Native Container
    with st.container(border=True):
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        with c_m1:
            st.caption("TOPIC DOMAIN")
            st.markdown(f"**{q.topic}**")
        with c_m2:
            st.caption("DIFFICULTY")
            st.markdown(f"**{q.difficulty}**")
        with c_m3:
            st.caption("PREREQUISITE")
            st.markdown(f"**{q.prerequisite_topic}**")
        with c_m4:
            st.caption("PROBED MISCONCEPTION")
            st.markdown(f"`{q.misconception_category}`")

        st.divider()

        # Question Text
        st.markdown(f"### {q.question}")

        if q.code_snippet:
            st.code(q.code_snippet, language="python")

        # Response Form
        form_key = f"diag_form_{q.id}"
        with st.form(key=form_key):
            selected_option_str = st.radio(
                label="**Select your answer:**",
                options=q.options,
                index=None,
                key=f"radio_ans_{q.id}"
            )

            st.markdown("**How confident are you in your answer?**")
            confidence_choice = st.radio(
                label="Self-reported confidence rating:",
                options=[1, 2, 3, 4, 5],
                format_func=lambda val: ConfidenceRating.get_label(val),
                index=3,  # default to '4 = Confident'
                key=f"conf_rating_{q.id}"
            )

            submit_btn = st.form_submit_button("Submit Diagnostic Response", type="primary")

            if submit_btn:
                if selected_option_str is None:
                    st.warning("⚠️ Please select an option before submitting.")
                else:
                    selected_idx = q.options.index(selected_option_str)
                    elapsed = max(1.0, round(time.time() - st.session_state["q_start_time"], 1))

                    # Input validation (Phase 3 defense)
                    conf_check = InputValidator.validate_confidence(confidence_choice)
                    if not conf_check.is_valid:
                        st.error(f"❌ {conf_check.message}")
                    else:
                        # Perform complete diagnostic evaluation
                        eval_result: AssessmentEvaluationResult = engine.evaluate_submission(
                            question=q,
                            selected_index=selected_idx,
                            confidence_rating=conf_check.sanitized_value,
                            response_time_seconds=elapsed
                        )
                        st.session_state["last_eval_result"] = eval_result
                        st.session_state["last_q_id"] = q.id
                        st.session_state["q_start_time"] = time.time()

    # Render Evaluation Feedback if this question was evaluated
    last_res: Optional[AssessmentEvaluationResult] = st.session_state.get("last_eval_result")
    if last_res and st.session_state.get("last_q_id") == q.id:
        render_evaluation_feedback(
            eval_result=last_res,
            question=q,
            knowledge_state=knowledge_state,
            optimizer=optimizer,
            misconceptions=misconceptions
        )

    st.divider()

    # Diagnostic Summary Box
    st.markdown("### 📋 Active Diagnostic Telemetry")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric(label="Total Diagnostic Attempts", value=str(len(engine.attempt_history)))
    with c2:
        correct_count = sum(1 for a in engine.attempt_history if a.is_correct)
        st.metric(label="Diagnostic Accuracy", value=f"{(correct_count/len(engine.attempt_history)*100):.0f}%" if engine.attempt_history else "0%")
    with c3:
        weak_topics = knowledge_state.get_weak_topics()
        st.metric(label="Targeted Weak Topics", value=str(len(weak_topics)), delta=f"{weak_topics[0].topic_name if weak_topics else 'None'}", delta_color="inverse")
    with c4:
        st.metric(label="Curricular Readiness", value="Prerequisites Checked", delta="Loops → Functions")


def render_evaluation_feedback(
    eval_result: AssessmentEvaluationResult,
    question: DiagnosticQuestion,
    knowledge_state: KnowledgeState,
    optimizer: Optional[DynamicLearningPathOptimizer],
    misconceptions: Optional[List[Misconception]]
):
    """Renders comprehensive feedback, metacognitive analysis, and 4-step intervention."""
    st.write("")
    conf_res = eval_result.confidence_result

    # Metacognitive Quadrant Banner (Feature 4)
    with st.container(border=True):
        st.markdown(f"#### Metacognitive Analysis: {conf_res.insight_title}")
        st.markdown(f"**Quadrant:** `{conf_res.quadrant.value}`  •  **Confidence:** `{ConfidenceRating.get_label(conf_res.confidence_rating)}`")
        st.info(conf_res.pedagogical_explanation)
        st.caption(f"💡 Recommended Strategy: {conf_res.recommended_action}")

    # Case 1: Correct Answer
    if eval_result.is_correct:
        st.success("✅ **Correct!** Excellent conceptual understanding.")
        st.markdown(f"**Explanation:** {eval_result.explanation}")

        # Quick action to record positive evidence
        if st.button("Apply Positive Evidence to Knowledge State", type="primary", key="btn_apply_correct"):
            rec = knowledge_state.update_from_evidence(
                topic_name=question.topic,
                is_correct=True,
                confidence_rating=conf_res.confidence_rating,
                difficulty=question.difficulty,
                reason="Diagnostic Question Correct Response"
            )
            st.session_state["last_state_change"] = rec
            if optimizer:
                st.session_state["current_learning_path"] = optimizer.generate_path(
                    knowledge_state, misconceptions or []
                )
            st.success(f"Updated {question.topic} mastery to {rec.new_mastery:.1f}%!")
            st.rerun()

    # Case 2: Incorrect Answer (Feature 5: Misconception Detection & 4-Step Intervention)
    else:
        st.error("❌ **Incorrect Answer.**")
        st.markdown(f"**Explanation:** {eval_result.explanation}")

        detected_misc = eval_result.detected_misconception
        if detected_misc:
            # Ensure misconceptions list is synchronized
            if misconceptions is not None and not any(m.id == detected_misc.id for m in misconceptions):
                misconceptions.append(detected_misc)

            st.warning(
                f"🚨 **Possible Misconception Detected: {detected_misc.title}**  \n\n"
                f"**Target Concept:** `{detected_misc.target_concept}`  \n"
                f"**Diagnostic Confidence:** `{int(detected_misc.confidence * 100)}%` (Status: `{detected_misc.status.value.upper()}`)"
            )

            # 4-PART INTERVENTION (Feature 5 specification)
            st.markdown("### 🛠️ 4-Part Adaptive Cognitive Intervention")

            # Part 1: Short Explanation
            with st.container(border=True):
                st.markdown("#### 1. Conceptual Explanation")
                st.write(detected_misc.short_explanation)

            # Part 2: Simple Example (with code contrast)
            with st.container(border=True):
                st.markdown("#### 2. Illustrative Example & Mental Model Contrast")
                st.markdown(f"*{detected_misc.simple_example}*")

                if detected_misc.code_example_flawed and detected_misc.code_example_corrected:
                    c_flawed, c_fixed = st.columns(2)
                    with c_flawed:
                        st.markdown("**❌ Flawed Mental Model Pattern:**")
                        st.code(detected_misc.code_example_flawed, language="python")
                    with c_fixed:
                        st.markdown("**✅ Corrected Python Model:**")
                        st.code(detected_misc.code_example_corrected, language="python")

            # Part 3: Corrective Micro-Question
            if detected_misc.corrective_question:
                cq = detected_misc.corrective_question
                with st.container(border=True):
                    st.markdown("#### 3. Corrective Check Question")
                    st.markdown(f"**{cq.question_text}**")

                    cq_ans = st.radio(
                        label="Select corrective check answer:",
                        options=cq.options,
                        index=None,
                        key=f"radio_cq_{detected_misc.id}"
                    )

                    if st.button("Verify Corrective Check", key=f"btn_verify_cq_{detected_misc.id}"):
                        if cq_ans is None:
                            st.warning("Please choose an answer.")
                        elif cq.options.index(cq_ans) == cq.correct_option_index:
                            st.success(f"🎉 {cq.explanation}")
                            st.session_state[f"cq_solved_{detected_misc.id}"] = True
                        else:
                            st.error("Not quite. Review the explanation in Step 1 and re-read the analogy.")

            # Part 4: Follow-Up Reassessment Assessment (Features 9 & 10)
            follow_up = get_follow_up_question(detected_misc.id)
            if follow_up:
                with st.container(border=True):
                    st.markdown(f"#### 4. Follow-Up Reassessment: {follow_up.topic}")
                    st.caption("Demonstrate mastery of the corrected concept to update your knowledge state and recalculate your path.")
                    st.markdown(f"**{follow_up.question}**")

                    if follow_up.code_snippet:
                        st.code(follow_up.code_snippet, language="python")

                    with st.form(key=f"form_followup_{detected_misc.id}"):
                        fu_choice_str = st.radio(
                            label="Your answer:",
                            options=follow_up.options,
                            index=None,
                            key=f"radio_fu_{detected_misc.id}"
                        )
                        fu_conf = st.radio(
                            label="Confidence in your follow-up answer:",
                            options=[1, 2, 3, 4, 5],
                            format_func=lambda val: ConfidenceRating.get_label(val),
                            index=3,
                            key=f"conf_fu_{detected_misc.id}"
                        )

                        fu_submit = st.form_submit_button("Submit Follow-Up Reassessment", type="primary")

                        if fu_submit:
                            if fu_choice_str is None:
                                st.warning("Please select an answer.")
                            else:
                                fu_conf_check = InputValidator.validate_confidence(fu_conf)
                                if not fu_conf_check.is_valid:
                                    st.error(f"❌ {fu_conf_check.message}")
                                else:
                                    fu_idx = follow_up.options.index(fu_choice_str)
                                    if fu_idx == follow_up.correct_answer_index:
                                        # SUCCESSFUL REMEDIATION & KNOWLEDGE STATE UPDATE!
                                        detected_misc.mark_remediated()
                                        if misconceptions is not None:
                                            for m in misconceptions:
                                                if m.id == detected_misc.id:
                                                    m.mark_remediated()

                                        # Update Knowledge State (Feature 9)
                                        rec: StateChangeRecord = knowledge_state.update_from_evidence(
                                            topic_name=follow_up.topic,
                                            is_correct=True,
                                            confidence_rating=fu_conf,
                                            difficulty=follow_up.difficulty,
                                            reason=f"Remediated {detected_misc.title} via Follow-Up Check"
                                        )
                                        st.session_state["last_state_change"] = rec

                                        # Recalculate Dynamic Learning Path (Feature 7 & 10)
                                        if optimizer:
                                            new_path = optimizer.generate_path(
                                                knowledge_state=knowledge_state,
                                                misconceptions=misconceptions or []
                                            )
                                            st.session_state["current_learning_path"] = new_path

                                        st.session_state[f"remediated_{detected_misc.id}"] = True
                                        st.rerun()
                                    else:
                                        st.error("❌ Incorrect follow-up answer. Take a moment to review the example above.")

    # Show State Change Diff Card if follow-up update occurred (Feature 9 & 10)
    state_rec: Optional[StateChangeRecord] = st.session_state.get("last_state_change")
    if state_rec:
        with st.container(border=True):
            st.success("🎉 **KNOWLEDGE STATE UPDATED & LEARNING PATH RECALCULATED!**")
            c_diff1, c_diff2, c_diff3 = st.columns(3)
            with c_diff1:
                delta_m = state_rec.new_mastery - state_rec.old_mastery
                st.metric(
                    label=f"{state_rec.topic_name} Mastery",
                    value=f"{state_rec.new_mastery:.1f}%",
                    delta=f"{delta_m:+.1f}% (Was {state_rec.old_mastery:.1f}%)"
                )
            with c_diff2:
                delta_c = state_rec.new_confidence - state_rec.old_confidence
                st.metric(
                    label="Confidence Index",
                    value=f"{state_rec.new_confidence:.1f}%",
                    delta=f"{delta_c:+.1f}% (Was {state_rec.old_confidence:.1f}%)"
                )
            with c_diff3:
                st.metric(
                    label="Curricular Trajectory",
                    value="Recalculated",
                    delta="Path Updated"
                )

            st.caption(f"Trigger Reason: **{state_rec.trigger_reason}** at {state_rec.timestamp}")

            c_nav1, c_nav2 = st.columns(2)
            with c_nav1:
                if st.button("🗺️ View Recalculated Learning Path", type="primary", key="btn_go_path"):
                    st.session_state["nav_selection"] = "Learning Path"
                    st.rerun()
            with c_nav2:
                if st.button("📊 View Updated Dashboard", key="btn_go_dash"):
                    st.session_state["nav_selection"] = "Dashboard"
                    st.rerun()
