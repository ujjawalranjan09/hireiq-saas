"""Results page - Score overview, tabbed graphs/feedback/replay, download PDF."""

import streamlit as st
import os


def show():
    """Render the results page."""
    results = st.session_state.get("interview_results")
    candidate_name = st.session_state.get("candidate_name", "Candidate")

    if not results:
        st.warning("No interview results available.")
        if st.button("Start New Interview"):
            st.session_state["current_page"] = "home"
            st.rerun()
        return

    st.title(f"📊 Interview Results - {candidate_name}")
    st.markdown("---")

    # Score overview
    report = results.get("report", {})
    metrics = report.get("metrics", results.get("metrics", {}))
    feedback = report.get("feedback", results.get("feedback", {}))

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_score = metrics.get("average_score", results.get("average_score", 0))
        st.metric("Overall Score", f"{avg_score:.1f}/100")
    with col2:
        grade = metrics.get("overall_grade", "N/A")
        st.metric("Grade", grade)
    with col3:
        answered = metrics.get("questions_answered", results.get("questions_answered", 0))
        total = metrics.get("total_questions", 0)
        st.metric("Questions", f"{answered}/{total}")
    with col4:
        confidence = metrics.get("average_confidence", 50)
        st.metric("Confidence", f"{confidence:.0f}/100")

    st.markdown("---")

    # Tabs for detailed views
    tab_graphs, tab_feedback, tab_questions, tab_download = st.tabs([
        "📈 Performance Charts",
        "💬 Feedback",
        "📝 Questions",
        "📥 Download",
    ])

    # ─── Charts Tab ───────────────────────────────────────────────────
    with tab_graphs:
        st.subheader("Performance Visualizations")
        chart_paths = report.get("chart_paths", {})
        if chart_paths:
            from frontend.components.chart_widget import show_charts
            show_charts(chart_paths)
        else:
            # Generate charts on the fly
            st.info("Generating charts...")
            try:
                interview_id = st.session_state.get("interview_id")
                if interview_id:
                    from database.queries import get_questions_for_interview, get_emotion_timeline
                    db_questions = get_questions_for_interview(interview_id)
                    emotion_data = [e.to_dict() for e in get_emotion_timeline(interview_id)]

                    questions = [
                        {
                            "question_text": q.question_text,
                            "question_type": q.question_type,
                            "difficulty": q.difficulty,
                            "answer_score": q.answer_score,
                            "semantic_similarity_score": q.semantic_similarity_score,
                            "keyword_match_score": q.keyword_match_score,
                            "concept_coverage_score": q.concept_coverage_score,
                        }
                        for q in db_questions
                    ]

                    from modules.analytics.graph_generator import generate_all_charts
                    from app.config import GRAPHS_DIR
                    charts = generate_all_charts(questions, emotion_data, metrics, str(GRAPHS_DIR))
                    if charts:
                        from frontend.components.chart_widget import show_charts
                        show_charts(charts)
                    else:
                        st.warning("Could not generate charts.")
            except Exception as e:
                st.error(f"Error generating charts: {e}")

    # ─── Feedback Tab ─────────────────────────────────────────────────
    with tab_feedback:
        st.subheader("Interview Feedback")

        col_str, col_weak = st.columns(2)

        with col_str:
            st.markdown("#### 💪 Strengths")
            for strength in feedback.get("strengths", ["No strengths identified"]):
                st.success(f"✅ {strength}")

        with col_weak:
            st.markdown("#### 📈 Areas for Improvement")
            for weakness in feedback.get("weaknesses", ["No weaknesses identified"]):
                st.warning(f"⚠️ {weakness}")

        st.markdown("---")
        st.markdown("#### 💡 Suggestions")
        for suggestion in feedback.get("suggestions", ["No suggestions available"]):
            st.info(f"💡 {suggestion}")

        st.markdown("---")
        st.markdown("#### 📝 Overall Assessment")
        st.markdown(f"*{feedback.get('overall_assessment', 'No assessment available.')}*")

        # Score breakdown by type
        st.markdown("---")
        st.markdown("#### 📊 Score Breakdown")
        scores_by_type = metrics.get("scores_by_type", {})
        if scores_by_type:
            import plotly.graph_objects as go
            fig = go.Figure(data=[
                go.Bar(
                    x=list(scores_by_type.keys()),
                    y=list(scores_by_type.values()),
                    marker_color=["#3498db", "#2ecc71", "#e67e22", "#e74c3c"],
                    text=[f"{v:.0f}" for v in scores_by_type.values()],
                    textposition="auto",
                )
            ])
            fig.update_layout(
                title="Average Score by Question Type",
                yaxis_range=[0, 100],
                template="plotly_white",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ─── Questions Tab ────────────────────────────────────────────────
    with tab_questions:
        st.subheader("Question-by-Question Detail")

        interview_id = st.session_state.get("interview_id")
        if interview_id:
            try:
                from database.queries import get_questions_for_interview
                db_questions = get_questions_for_interview(interview_id)

                for i, q in enumerate(db_questions):
                    score = q.answer_score
                    color = "green" if score >= 70 else "orange" if score >= 50 else "red"

                    with st.expander(f"Q{i+1}: {q.question_text[:80]}... | Score: {score:.0f}"):
                        st.markdown(f"**Type:** {q.question_type} | **Difficulty:** {q.difficulty}")
                        st.markdown(f"**Question:** {q.question_text}")

                        if q.candidate_answer_text:
                            st.markdown("**Your Answer:**")
                            st.text(q.candidate_answer_text)

                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Semantic", f"{q.semantic_similarity_score:.0f}")
                        with col_b:
                            st.metric("Keywords", f"{q.keyword_match_score:.0f}")
                        with col_c:
                            st.metric("Concepts", f"{q.concept_coverage_score:.0f}")

            except Exception as e:
                st.error(f"Error loading questions: {e}")

    # ─── Download Tab ─────────────────────────────────────────────────
    with tab_download:
        st.subheader("Download Report")

        pdf_path = report.get("pdf_path", "")

        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="📥 Download PDF Report",
                    data=f.read(),
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            st.success(f"Report saved at: {pdf_path}")
        else:
            st.warning("PDF report not available. Generate one now:")
            if st.button("Generate Report"):
                with st.spinner("Generating report..."):
                    try:
                        interview_id = st.session_state.get("interview_id")
                        if interview_id:
                            from database.queries import get_questions_for_interview, get_emotion_timeline
                            db_questions = get_questions_for_interview(interview_id)
                            emotion_data = [e.to_dict() for e in get_emotion_timeline(interview_id)]

                            questions = [
                                {
                                    "question_text": q.question_text,
                                    "question_type": q.question_type,
                                    "difficulty": q.difficulty,
                                    "candidate_answer_text": q.candidate_answer_text,
                                    "answer_score": q.answer_score,
                                    "semantic_similarity_score": q.semantic_similarity_score,
                                    "keyword_match_score": q.keyword_match_score,
                                    "concept_coverage_score": q.concept_coverage_score,
                                }
                                for q in db_questions
                            ]

                            from modules.analytics.performance_engine import calculate_performance_metrics
                            from modules.report.feedback_generator import generate_feedback
                            from modules.analytics.graph_generator import generate_all_charts
                            from modules.report.pdf_report import generate_pdf_report
                            from app.config import GRAPHS_DIR

                            perf_metrics = calculate_performance_metrics(questions, emotion_data)
                            fb = generate_feedback(candidate_name, questions, emotion_data, perf_metrics)
                            charts = generate_all_charts(questions, emotion_data, perf_metrics, str(GRAPHS_DIR))

                            new_pdf = generate_pdf_report(
                                candidate_name=candidate_name,
                                interview_data={"status": "completed"},
                                questions=questions,
                                feedback=fb,
                                metrics=perf_metrics,
                                chart_paths=charts,
                            )

                            with open(new_pdf, "rb") as f:
                                st.download_button(
                                    label="📥 Download PDF Report",
                                    data=f.read(),
                                    file_name=os.path.basename(new_pdf),
                                    mime="application/pdf",
                                    type="primary",
                                    use_container_width=True,
                                )
                    except Exception as e:
                        st.error(f"Error generating report: {e}")

    # Navigation
    st.markdown("---")
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🏠 New Interview", use_container_width=True):
            # Clear session state
            for key in ["interview_results", "interview_controller", "interview_started",
                       "interview_id", "session_id", "questions", "interview_phase"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["current_page"] = "home"
            st.rerun()
    with col_nav2:
        if st.button("🔄 Replay Interview", use_container_width=True):
            st.session_state["current_page"] = "replay"
            st.rerun()
