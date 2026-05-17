"""Copilot dashboard page — split-screen view for human interviewers."""

import streamlit as st


def show():
    """Render the copilot dashboard page."""
    st.set_page_config(page_title="Copilot Mode", page_icon="🎯", layout="wide")

    # Check for active interview
    suggestion_engine = st.session_state.get("copilot_engine")
    interview_results = st.session_state.get("interview_results")

    if not suggestion_engine and not interview_results:
        _render_setup()
        return

    if suggestion_engine:
        _render_active_copilot(suggestion_engine)
    else:
        _render_post_interview_copilot(interview_results)


def _render_setup():
    """Render the copilot setup/landing view."""
    st.title("🎯 Copilot Mode")
    st.markdown(
        "The **Copilot** gives you real-time AI suggestions while you watch "
        "a candidate's interview. It highlights strengths, flags concerns, "
        "and suggests follow-up questions."
    )
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚀 Start with Live Interview")
        st.info(
            "Start or join an active interview session. "
            "The copilot will analyze the candidate in real-time."
        )
        if st.button("Go to Interview", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "interview"
            st.rerun()

    with col2:
        st.markdown("### 📊 Review Past Interview")
        if interview_results := st.session_state.get("interview_results"):
            st.success("Interview data available!")
            if st.button("Load Copilot Review", use_container_width=True):
                st.rerun()
        else:
            st.warning("No completed interview found. Start a new one first.")

    # Feature overview
    st.markdown("---")
    st.markdown("### ✨ What the Copilot Does")

    features = [
        ("🔄 **Follow-up Suggestions**", "AI detects topics worth exploring further"),
        ("🔍 **Probe Deeper**", "Identifies when the candidate is strong and can handle harder questions"),
        ("💬 **Rephrase Prompts**", "Flags vague answers and suggests rephrasing"),
        ("⭐ **STAR Method Check**", "Detects when behavioral answers lack structure"),
        ("🎯 **Gap Detection**", "Tracks which required topics haven't been covered"),
        ("📊 **Live Scorecard**", "Real-time candidate score tracking with trend analysis"),
        ("⚡ **Quick Actions**", "Mark strong areas, flag concerns, skip topics with one click"),
    ]

    for title, desc in features:
        st.markdown(f"**{title}** — {desc}")


def _render_active_copilot(suggestion_engine):
    """Render the copilot during an active interview."""
    from modules.copilot.copilot_dashboard import render_copilot_dashboard

    candidate_name = st.session_state.get("candidate_name", "Candidate")
    current_question = st.session_state.get("current_question", "")
    current_answer = st.session_state.get("current_transcription", "")
    topic_list = st.session_state.get("interview_topics", [])

    render_copilot_dashboard(
        suggestion_engine=suggestion_engine,
        candidate_name=candidate_name,
        current_question=current_question,
        current_answer=current_answer,
        topic_list=topic_list,
    )

    # Auto-refresh for live updates
    if st.session_state.get("interview_active", False):
        import time
        time.sleep(2)
        st.rerun()


def _render_post_interview_copilot(interview_results):
    """Render copilot review mode after an interview."""
    st.title("🎯 Copilot Review")
    st.markdown("Review the AI suggestions from the completed interview.")
    st.markdown("---")

    if not interview_results:
        st.warning("No interview data available.")
        return

    # Extract copilot data
    copilot_data = interview_results.get("copilot_data", {})
    suggestions = copilot_data.get("suggestions", [])
    scorecard = copilot_data.get("scorecard", {})
    analytics = copilot_data.get("analytics", {})

    # Scorecard summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg = scorecard.get("average", 0)
        st.metric("Average Score", f"{avg:.0f}/100")
    with col2:
        trend = scorecard.get("trend", "neutral")
        trend_display = {"improving": "📈 Improving", "declining": "📉 Declining", "neutral": "➡️ Stable"}
        st.metric("Trend", trend_display.get(trend, trend))
    with col3:
        st.metric("Questions", scorecard.get("questions_answered", 0))
    with col4:
        strong = len(scorecard.get("strong_topics", []))
        st.metric("Strong Areas", strong)

    st.markdown("---")

    # Suggestion log
    st.markdown("### 📋 Suggestion Log")
    if suggestions:
        for i, sug in enumerate(suggestions):
            sug_type = sug.get("type", "")
            message = sug.get("message", "")
            detail = sug.get("detail", "")
            icon_map = {
                "follow_up": "🔄", "probe_deeper": "🔍", "rephrase": "💬",
                "star_method": "⭐", "gap_fill": "🎯", "encourage": "👏",
                "redirect": "🔀", "skip": "⏭️", "strong_area": "💪",
            }
            icon = icon_map.get(sug_type, "💡")
            with st.expander(f"{icon} {message}"):
                st.markdown(f"**Type:** {sug_type}")
                if detail:
                    st.markdown(f"**Detail:** {detail}")
    else:
        st.caption("No suggestions were generated during this interview.")

    # Pacing analytics
    if analytics:
        st.markdown("---")
        st.markdown("### ⏱️ Pacing Analytics")
        total_actions = analytics.get("total_actions", 0)
        action_counts = analytics.get("action_counts", {})
        st.metric("Total Pacing Adjustments", total_actions)
        if action_counts:
            for action, count in action_counts.items():
                st.markdown(f"- **{action}**: {count}")

    # Navigation
    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("📊 View Full Results", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "results"
            st.rerun()
    with col_nav2:
        if st.button("🏠 New Interview", use_container_width=True):
            for key in ["interview_results", "copilot_engine", "interview_active"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["current_page"] = "home"
            st.rerun()
