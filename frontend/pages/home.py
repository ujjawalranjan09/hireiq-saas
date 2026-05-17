"""Home page - Welcome, resume upload, candidate info form."""

import streamlit as st
import os
import tempfile
from datetime import datetime


def show():
    """Render the home page."""
    st.title("🎯 AI Multimodal Interview Agent")
    st.markdown("---")

    st.markdown("""
    Welcome to the **AI-Powered Interview System**. This tool conducts 
    adaptive technical interviews with real-time emotion analysis, 
    voice evaluation, and comprehensive performance reports.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📋 Candidate Information")
        name = st.text_input("Full Name", placeholder="Enter your full name")
        email = st.text_input("Email Address", placeholder="your.email@example.com")

    with col2:
        st.markdown("### Features")
        st.markdown("""
        - 🎤 Voice-based answers
        - 📹 Facial emotion tracking
        - 🧠 Adaptive difficulty
        - 📊 Detailed analytics
        - 📄 PDF report generation
        """)

    st.markdown("---")
    st.subheader("📄 Upload Your Resume")

    resume_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        help="Upload your resume in PDF format for personalized questions",
    )

    # Interview settings
    st.subheader("⚙️ Interview Settings")
    col_a, col_b = st.columns(2)
    with col_a:
        question_count = st.slider("Number of Questions", 5, 20, 10)
    with col_b:
        st.info("Difficulty adapts automatically based on your performance.")

    st.markdown("---")

    # Start button
    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        if not name:
            st.error("Please enter your name.")
            return
        if not email:
            st.error("Please enter your email address.")
            return

        with st.spinner("Preparing your interview..."):
            try:
                # Save uploaded file
                resume_path = ""
                if resume_file:
                    resume_dir = os.path.join(
                        os.path.dirname(__file__), "..", "..", "outputs", "temp"
                    )
                    os.makedirs(resume_dir, exist_ok=True)
                    resume_path = os.path.join(resume_dir, f"resume_{email}.pdf")
                    with open(resume_path, "wb") as f:
                        f.write(resume_file.getbuffer())

                # Create or get candidate
                from database.queries import get_candidate_by_email, create_candidate, update_candidate
                from database.models import Candidate

                candidate = get_candidate_by_email(email)
                if candidate:
                    candidate_id = str(candidate._id)
                    if resume_path:
                        update_candidate(candidate_id, {"name": name, "resume_path": resume_path})
                else:
                    cand = Candidate(name=name, email=email, resume_path=resume_path)
                    candidate_id = create_candidate(cand)

                # Start interview
                from modules.orchestrator.interview_controller import InterviewController
                controller = InterviewController()
                result = controller.start_interview(
                    candidate_id=candidate_id,
                    resume_path=resume_path,
                    question_count=question_count,
                )

                if result.get("success"):
                    st.session_state["interview_controller"] = controller
                    st.session_state["candidate_name"] = name
                    st.session_state["candidate_email"] = email
                    st.session_state["candidate_id"] = candidate_id
                    st.session_state["interview_id"] = result["interview_id"]
                    st.session_state["session_id"] = result["session_id"]
                    st.session_state["questions"] = result["questions"]
                    st.session_state["current_page"] = "interview"
                    st.session_state["interview_started"] = True
                    st.success("Interview ready! Redirecting...")
                    st.rerun()
                else:
                    st.error(f"Failed to start interview: {result.get('error', 'Unknown error')}")

            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.exception(e)
