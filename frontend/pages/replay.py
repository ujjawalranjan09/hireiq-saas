"""Replay page - Video replay with emotion markers timeline."""

import streamlit as st


def show():
    """Render the replay page."""
    interview_id = st.session_state.get("interview_id")
    candidate_name = st.session_state.get("candidate_name", "Candidate")

    if not interview_id:
        st.warning("No interview to replay. Please complete an interview first.")
        if st.button("Go to Home"):
            st.session_state["current_page"] = "home"
            st.rerun()
        return

    st.title(f"🔄 Interview Replay - {candidate_name}")
    st.markdown("---")

    try:
        from database.queries import get_questions_for_interview, get_emotion_timeline, get_interview
        from modules.report.replay_system import build_replay_data

        interview_data_raw = get_interview(interview_id)
        interview_data = interview_data_raw.to_dict() if interview_data_raw else {"_id": interview_id}

        db_questions = get_questions_for_interview(interview_id)
        emotion_timeline = get_emotion_timeline(interview_id)

        questions = [
            {
                "question_text": q.question_text,
                "question_type": q.question_type,
                "difficulty": q.difficulty,
                "candidate_answer_text": q.candidate_answer_text,
                "answer_score": q.answer_score,
                "answer_audio_path": q.answer_audio_path,
                "timestamp": q.timestamp,
                "order": q.order,
            }
            for q in db_questions
        ]

        emotion_data = [e.to_dict() for e in emotion_timeline]

        replay = build_replay_data(questions, emotion_data, interview_data)

    except Exception as e:
        st.error(f"Error loading replay data: {e}")
        return

    # Emotion Timeline
    st.subheader("😊 Emotion Timeline")
    markers = replay.get("emotion_markers", [])
    if markers:
        import plotly.graph_objects as go

        timestamps = list(range(len(markers)))
        confidences = [m.get("confidence", 50) for m in markers]
        emotions = [m.get("emotion", "neutral") for m in markers]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=confidences,
            mode="lines+markers",
            name="Confidence",
            line=dict(color="#3498db"),
            text=emotions,
            hovertemplate="Time: %{x}<br>Confidence: %{y:.1f}<br>Emotion: %{text}",
            marker=dict(
                size=8,
                color=[_emotion_color(e) for e in emotions],
            ),
        ))

        fig.update_layout(
            title="Emotion & Confidence Over Time",
            xaxis_title="Time (snapshots)",
            yaxis_title="Confidence Score",
            yaxis_range=[0, 100],
            template="plotly_white",
            height=300,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Emotion legend
        from collections import Counter
        emotion_counts = Counter(emotions)
        cols = st.columns(min(len(emotion_counts), 5))
        for i, (emotion, count) in enumerate(emotion_counts.most_common()):
            with cols[i % len(cols)]:
                st.markdown(f":{_emotion_color_name(emotion)}[{emotion.capitalize()}]: {count}")
    else:
        st.info("No emotion data recorded during this interview.")

    st.markdown("---")

    # Question Replay
    st.subheader("📝 Question Replay")

    replay_questions = replay.get("questions", [])
    score_progression = replay.get("score_progression", [])

    if replay_questions:
        # Score progression chart
        if score_progression:
            import plotly.graph_objects as go
            scores = [s.get("score", 0) for s in score_progression]
            labels = [f"Q{s.get('order', i)+1}" for i, s in enumerate(score_progression)]

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=labels,
                y=scores,
                marker_color=[_score_color(s) for s in scores],
                text=[f"{s:.0f}" for s in scores],
                textposition="auto",
            ))
            fig2.update_layout(
                title="Score Progression",
                yaxis_range=[0, 100],
                template="plotly_white",
                height=250,
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Detailed question cards
        for i, q in enumerate(replay_questions):
            score = q.get("score", 0)
            q_type = q.get("type", "technical")
            difficulty = q.get("difficulty", "medium")

            with st.expander(
                f"Q{i+1}: {q.get('text', '')[:60]}... | "
                f"Score: {score:.0f} | "
                f"{q_type.capitalize()} | {difficulty.capitalize()}"
            ):
                st.markdown(f"**Question:** {q.get('text', '')}")
                st.markdown(f"**Type:** {q_type} | **Difficulty:** {difficulty}")

                answer = q.get("answer", "")
                if answer:
                    st.markdown("**Answer:**")
                    st.text_area("", value=answer, height=100, disabled=True, key=f"replay_answer_{i}")

                st.metric("Score", f"{score:.0f}/100")

                audio_path = q.get("audio_path", "")
                if audio_path and os.path.exists(audio_path):
                    st.audio(audio_path)

    # Navigation
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 View Results", use_container_width=True):
            st.session_state["current_page"] = "results"
            st.rerun()
    with col2:
        if st.button("🏠 New Interview", use_container_width=True):
            for key in ["interview_results", "interview_controller", "interview_started",
                       "interview_id", "session_id", "questions"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["current_page"] = "home"
            st.rerun()


def _emotion_color(emotion: str) -> str:
    """Get color for an emotion."""
    colors = {
        "happy": "#2ecc71",
        "confident": "#3498db",
        "excited": "#f39c12",
        "neutral": "#95a5a6",
        "calm": "#1abc9c",
        "nervous": "#e74c3c",
        "uncertain": "#e67e22",
        "sad": "#8e44ad",
        "angry": "#c0392b",
        "fear": "#d35400",
        "surprise": "#f1c40f",
    }
    return colors.get(emotion.lower(), "#95a5a6")


def _emotion_color_name(emotion: str) -> str:
    """Get Streamlit color name for emotion."""
    mapping = {
        "happy": "green",
        "confident": "blue",
        "neutral": "gray",
        "nervous": "red",
        "sad": "violet",
        "angry": "red",
        "surprise": "orange",
    }
    return mapping.get(emotion.lower(), "gray")


import os  # import at module level
