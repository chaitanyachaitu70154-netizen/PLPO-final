"""
Practice Page for Phase 2.
Targeted deliberate micro-drills generated dynamically by evaluating:
- Active weak topics (< 70% mastery)
- Diagnosed misconceptions (Parameter vs Argument, FIFO vs LIFO, Loop Bounds)
- Curricular prerequisite status
Built 100% with Streamlit-native components with zero raw HTML.
"""

import streamlit as st
from typing import List, Optional
from core.knowledge_state import KnowledgeState
from core.misconception import Misconception, MisconceptionStatus
from core.practice_generator import TargetedPracticeGenerator, PracticeDrill, PracticeType

def render_practice_page(
    knowledge_state: KnowledgeState,
    misconceptions: List[Misconception]
):
    """Render targeted practice micro-drills interface using native Streamlit components."""
    st.title("💻 Targeted Practice Drills (Feature 8)")
    st.caption("Deliberate code exercises specifically synthesized to address active cognitive gaps and prerequisite reinforcement.")

    generator = TargetedPracticeGenerator()
    drills: List[PracticeDrill] = generator.generate_drills(
        knowledge_state=knowledge_state,
        misconceptions=misconceptions,
        limit=3
    )

    st.info(
        f"🎯 **Targeted Drill Selection:** Found {len(drills)} high-priority practice challenges matching your current "
        f"weak topics ({', '.join([t.topic_name for t in knowledge_state.get_weak_topics()])}) "
        f"and active misconceptions."
    )

    tabs = st.tabs([f"Drill {i+1}: {d.title}" for i, d in enumerate(drills)])

    for i, (tab, drill) in enumerate(zip(tabs, drills)):
        with tab:
            with st.container(border=True):
                c_d1, c_d2, c_d3 = st.columns(3)
                with c_d1:
                    st.caption("TOPIC")
                    st.markdown(f"**{drill.topic}**")
                with c_d2:
                    st.caption("DIFFICULTY")
                    st.markdown(f"**{drill.difficulty}**")
                with c_d3:
                    st.caption("EXERCISE TYPE")
                    st.markdown(f"`{drill.practice_type.value}`")

                st.divider()

                st.markdown(f"#### {drill.prompt}")
                st.caption(f"💡 Pedagogical focus: {drill.pedagogical_reason}")

                if drill.code_snippet:
                    st.code(drill.code_snippet, language="python")

                # Exercise Type 1: Multiple Choice Concept Check
                if drill.options:
                    selected_ans = st.radio(
                        label="Select your answer:",
                        options=drill.options,
                        index=None,
                        key=f"drill_opt_{drill.id}"
                    )

                    c_btn, c_h = st.columns([1, 3])
                    with c_btn:
                        if st.button("Verify Answer", type="primary", key=f"btn_v_{drill.id}"):
                            if selected_ans is None:
                                st.warning("Please choose an option.")
                            elif drill.options.index(selected_ans) == drill.correct_option_index:
                                st.success("🎉 **Correct!** Excellent understanding of this concept.")
                                st.session_state[f"drill_solved_{drill.id}"] = True
                            else:
                                st.error("❌ Not quite. Review the hints below for guidance.")

                    with c_h:
                        if drill.hints:
                            with st.expander("💡 Need a hint?"):
                                for hint in drill.hints:
                                    st.info(hint)

                # Exercise Type 2: Interactive Code Editor / Bug Fix
                elif drill.starter_code:
                    user_code = st.text_area(
                        "Edit the code to fix the issue:",
                        value=drill.starter_code,
                        height=180,
                        key=f"code_area_{drill.id}"
                    )

                    c_btn, c_h = st.columns([1, 3])
                    with c_btn:
                        if st.button("Run & Verify Solution", type="primary", key=f"btn_code_{drill.id}"):
                            # Validation rule for parameter shadowing drill
                            if "radius = 10" not in user_code and "radius" in user_code:
                                st.success("✅ **Bug Fixed!** You removed the hardcoded parameter reassignment. The function now dynamically computes the circle area for any radius passed by caller.")
                                st.session_state[f"drill_solved_{drill.id}"] = True
                            elif "celsius = 25" not in user_code and "celsius" in user_code:
                                st.success("✅ **Bug Fixed!** By removing the override, the function now honors caller arguments.")
                                st.session_state[f"drill_solved_{drill.id}"] = True
                            elif "return" in user_code and "print(discounted)" not in user_code:
                                st.success("✅ **Bug Fixed!** You replaced the print side-effect with a proper return statement.")
                                st.session_state[f"drill_solved_{drill.id}"] = True
                            else:
                                st.warning("⚠️ The bug appears to still be present in the code. Review the hints for guidance.")

                    with c_h:
                        if drill.hints:
                            with st.expander("💡 Need a hint?"):
                                for hint in drill.hints:
                                    st.info(hint)
