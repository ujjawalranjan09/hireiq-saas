"""Main entry point for the AI Multimodal Interview Agent."""

import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_page_config():
    """Configure the Streamlit page."""
    st.set_page_config(
        page_title="AI Interview Agent",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "current_page": "home",
        "interview_started": False,
        "interview_controller": None,
        "candidate_name": "",
        "candidate_email": "",
        "candidate_id": "",
        "interview_id": "",
        "session_id": "",
        "questions": [],
        "interview_results": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default


def ensure_directories():
    """Ensure output directories exist."""
    from app.config import OUTPUTS_DIR, REPORTS_DIR, RECORDINGS_DIR, GRAPHS_DIR
    for d in [OUTPUTS_DIR, REPORTS_DIR, RECORDINGS_DIR, GRAPHS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def sidebar_navigation():
    """Render sidebar navigation."""
    with st.sidebar:
        st.title("🎯 AI Interview Agent")
        st.markdown("---")

        page = st.session_state.get("current_page", "home")

        st.markdown("### Navigation")
        if st.button("🏠 Home", use_container_width=True):
            st.session_state["current_page"] = "home"
            st.rerun()

        if st.session_state.get("interview_started"):
            if st.button("📝 Interview", use_container_width=True):
                st.session_state["current_page"] = "interview"
                st.rerun()

        if st.session_state.get("interview_results"):
            if st.button("📊 Results", use_container_width=True):
                st.session_state["current_page"] = "results"
                st.rerun()
            if st.button("🔄 Replay", use_container_width=True):
                st.session_state["current_page"] = "replay"
                st.rerun()

        st.markdown("---")
        st.markdown("### Status")
        status = "🟢 Active" if st.session_state.get("interview_started") else "⚪ Idle"
        st.markdown(f"Interview: {status}")

        candidate = st.session_state.get("candidate_name", "None")
        st.markdown(f"Candidate: {candidate}")

        st.markdown("---")
        st.caption("Powered by AI | v1.0.0")


def main():
    """Main application entry point."""
    setup_page_config()
    init_session_state()
    ensure_directories()
    sidebar_navigation()

    # Route to the correct page
    page = st.session_state.get("current_page", "home")

    try:
        if page == "home":
            from frontend.pages.home import show
            show()
        elif page == "interview":
            from frontend.pages.interview import show
            show()
        elif page == "results":
            from frontend.pages.results import show
            show()
        elif page == "replay":
            from frontend.pages.replay import show
            show()
        else:
            st.error(f"Unknown page: {page}")
            from frontend.pages.home import show
            show()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logger.exception("Page rendering error")
        if st.button("🔄 Reset"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


if __name__ == "__main__":
    main()
