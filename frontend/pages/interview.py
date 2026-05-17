"""Interview page - Video feed, question display, recording controls, progress."""

import streamlit as st
import os
import tempfile
import time


def show():
    """Render the interview page."""
    # Check interview state
    if not st.session_state.get("interview_started"):
        st.warning("Please start an interview from the home page.")
        if st.button("Go to Home"):
            st.session_state["current_page"] = "home"
            st.rerun()
        return

    controller = st.session_state.get("interview_controller")
    candidate_name = st.session_state.get("candidate_name", "Candidate")
    questions = st.session_state.get("questions", [])

    if not controller:
        st.error("Interview controller not found. Please restart the interview.")
        return

    # Initialize interview state
    if "interview_phase" not in st.session_state:
        st.session_state["interview_phase"] = "introduction"
        st.session_state["current_q_index"] = 0
        st.session_state["answer_recorded"] = False

    phase = st.session_state["interview_phase"]

    # Header with progress
    current_q = st.session_state.get("current_q_index", 0)
    total_q = len(questions)
    progress = current_q / total_q if total_q > 0 else 0

    st.progress(progress, text=f"Question {current_q}/{total_q}")

    # ─── Introduction Phase ───────────────────────────────────────────
    if phase == "introduction":
        st.title(f"👋 Welcome, {candidate_name}!")
        st.markdown("---")

        intro_text = controller.get_introduction(candidate_name)
        st.markdown(f"### Interview Introduction")
        st.info(intro_text)

        # Generate TTS for introduction
        if st.button("🔊 Play Introduction"):
            try:
                from modules.voice.text_to_speech import text_to_speech
                from app.config import RECORDINGS_DIR
                audio_path = str(RECORDINGS_DIR / "intro.mp3")
                text_to_speech(intro_text, output_path=audio_path)
                st.audio(audio_path)
            except Exception as e:
                st.warning(f"Audio generation failed: {e}")

        st.markdown("---")
        if st.button("▶️ Begin Interview", type="primary", use_container_width=True):
            st.session_state["interview_phase"] = "asking"
            st.rerun()

    # ─── Asking Question Phase ────────────────────────────────────────
    elif phase == "asking":
        q_index = st.session_state.get("current_q_index", 0)

        if q_index >= len(questions):
            st.session_state["interview_phase"] = "closing"
            st.rerun()
            return

        q_data = questions[q_index]
        q_text = q_data.get("question_text", "No question available")
        q_type = q_data.get("question_type", "technical")
        q_diff = q_data.get("difficulty", "medium")

        # Display question
        st.markdown(f"### Question {q_index + 1} of {total_q}")
        type_badge = {"resume": "🔵", "technical": "🟢", "behavioral": "🟡"}.get(q_type, "⚪")
        st.markdown(f"{type_badge} **{q_type.capitalize()}** | Difficulty: **{q_diff.capitalize()}**")
        st.markdown(f"> {q_text}")

        # TTS for question
        if st.button("🔊 Read Question", key=f"tts_q_{q_index}"):
            try:
                from modules.voice.text_to_speech import text_to_speech
                from app.config import RECORDINGS_DIR
                audio_path = str(RECORDINGS_DIR / f"question_{q_index}.mp3")
                text_to_speech(q_text, output_path=audio_path)
                st.audio(audio_path)
            except Exception as e:
                st.warning(f"Audio generation failed: {e}")

        st.markdown("---")

        # Answer input
        tab_text, tab_voice = st.tabs(["⌨️ Type Answer", "🎤 Voice Answer"])

        with tab_text:
            answer_text = st.text_area(
                "Your answer:",
                height=150,
                placeholder="Type your answer here...",
                key=f"answer_text_{q_index}",
            )
            if st.button("✅ Submit Answer", type="primary", key=f"submit_text_{q_index}"):
                if answer_text.strip():
                    st.session_state["pending_answer"] = answer_text
                    st.session_state["pending_audio"] = ""
                    st.session_state["interview_phase"] = "processing"
                    st.rerun()
                else:
                    st.warning("Please provide an answer.")

        with tab_voice:
            st.markdown("Click to record your answer:")
            from frontend.components.audio_widget import show_recorder
            audio_result = show_recorder(key=f"recorder_{q_index}")

            if audio_result:
                st.session_state["pending_answer"] = audio_result.get("text", "")
                st.session_state["pending_audio"] = audio_result.get("audio_path", "")
                st.session_state["interview_phase"] = "processing"
                st.rerun()

        # Video feed (optional)
        with st.sidebar:
            st.markdown("### 📹 Camera Feed")
            from frontend.components.video_widget import show_camera_feed
            show_camera_feed()

    # ─── Processing Phase ─────────────────────────────────────────────
    elif phase == "processing":
        answer_text = st.session_state.get("pending_answer", "")
        audio_path = st.session_state.get("pending_audio", "")

        with st.spinner("Analyzing your answer..."):
            # Get emotion data (simplified - in real use would capture during recording)
            facial_emotion = {"dominant_emotion": "neutral", "confidence_score": 50.0}
            voice_features = {"emotion_label": "neutral", "confidence_score": 50.0,
                            "speaking_speed": 120, "pause_ratio": 0.2, "hesitation_detected": False,
                            "pitch_mean": 150, "duration": 10}

            result = controller.process_answer(
                answer_text=answer_text,
                audio_path=audio_path,
                facial_emotion=facial_emotion,
                voice_features=voice_features,
            )

        # Display evaluation
        st.markdown("### 📊 Answer Evaluation")
        evaluation = result.get("evaluation", {})
        confidence = result.get("confidence", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Score", f"{evaluation.get('total_score', 0):.0f}/100")
        with col2:
            st.metric("Semantic", f"{evaluation.get('semantic_score', 0):.0f}")
        with col3:
            st.metric("Keywords", f"{evaluation.get('keyword_score', 0):.0f}")
        with col4:
            st.metric("Confidence", f"{confidence.get('combined_score', 50):.0f}")

        st.info(evaluation.get("feedback", ""))

        next_action = result.get("next_action")

        if next_action == "followup":
            followup = result.get("followup", {})
            st.markdown("---")
            st.markdown("### 🔄 Follow-up Question")
            st.warning(followup.get("question_text", ""))

            if st.button("Answer Follow-up"):
                st.session_state["interview_phase"] = "followup"
                st.session_state["followup_question"] = followup
                st.rerun()
            elif st.button("Skip Follow-up"):
                st.session_state["current_q_index"] += 1
                st.session_state["interview_phase"] = "asking"
                st.session_state["interview_controller"].session_manager.reset_followup(
                    st.session_state.get("session_id", "")
                )
                st.rerun()
        elif next_action == "closing":
            if st.button("See Results", type="primary"):
                st.session_state["interview_phase"] = "closing"
                st.rerun()
        else:
            if st.button("Next Question ➡️", type="primary"):
                st.session_state["current_q_index"] += 1
                st.session_state["interview_phase"] = "asking"
                st.rerun()

    # ─── Follow-up Phase ──────────────────────────────────────────────
    elif phase == "followup":
        followup = st.session_state.get("followup_question", {})
        st.markdown("### 🔄 Follow-up Question")
        st.warning(followup.get("question_text", ""))

        q_index = st.session_state.get("current_q_index", 0)
        answer_text = st.text_area("Your follow-up answer:", height=120, key=f"followup_{q_index}")

        if st.button("Submit Follow-up", type="primary"):
            if answer_text.strip():
                result = controller.process_followup_answer(answer_text)
                next_action = result.get("next_action")

                if next_action == "closing":
                    st.session_state["interview_phase"] = "closing"
                else:
                    st.session_state["current_q_index"] += 1
                    st.session_state["interview_phase"] = "asking"
                st.rerun()
            else:
                st.warning("Please provide an answer.")

        if st.button("Skip"):
            st.session_state["current_q_index"] += 1
            st.session_state["interview_phase"] = "asking"
            st.rerun()

    # ─── Closing Phase ────────────────────────────────────────────────
    elif phase == "closing":
        st.title("🎉 Interview Complete!")
        st.markdown("---")

        with st.spinner("Generating your report..."):
            result = controller.close_interview(candidate_name)

        closing_msg = result.get("closing_message", "Thank you for completing the interview!")
        st.success(closing_msg)

        if "report" in result and not result["report"].get("error"):
            st.markdown("### 📄 Your Report is Ready!")

        if st.button("📊 View Results", type="primary", use_container_width=True):
            st.session_state["interview_results"] = result
            st.session_state["current_page"] = "results"
            st.session_state["interview_started"] = False
            st.rerun()
