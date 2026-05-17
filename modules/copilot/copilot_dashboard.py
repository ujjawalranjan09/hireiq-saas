"""Streamlit copilot dashboard — split-screen view for human interviewers."""

import logging
import time
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


def render_copilot_dashboard(
    suggestion_engine: Any,
    candidate_name: str = "Candidate",
    current_question: str = "",
    current_answer: str = "",
    video_frame_url: Optional[str] = None,
    topic_list: Optional[List[str]] = None,
) -> None:
    """Render the split-screen copilot dashboard in Streamlit.

    Layout:
        Left column: candidate video/question context
        Right column: live AI suggestions, scorecard, quick actions

    Args:
        suggestion_engine: SuggestionEngine instance with current state.
        candidate_name: Display name for the candidate.
        current_question: The question currently being asked.
        current_answer: The candidate's latest answer (live transcription).
        video_frame_url: Optional URL/path to the current video frame.
        topic_list: List of interview topics for the sidebar.
    """
    st.markdown(
        """
        <style>
        .copilot-header {
            background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
            padding: 12px 24px; border-radius: 12px; margin-bottom: 16px;
        }
        .suggestion-card {
            background: rgba(255,255,255,0.04); border-left: 4px solid #667eea;
            border-radius: 0 8px 8px 0; padding: 12px 16px; margin-bottom: 8px;
        }
        .suggestion-card.priority-1 { border-left-color: #e74c3c; }
        .suggestion-card.priority-2 { border-left-color: #e67e22; }
        .suggestion-card.priority-3 { border-left-color: #f39c12; }
        .scorecard { background: rgba(102,126,234,0.08); border-radius: 12px; padding: 20px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        f'<div class="copilot-header">'
        f"<h3 style='margin:0;color:#fff;'>🎯 Copilot Mode — Assisting with {candidate_name}'s Interview</h3>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Split layout
    col_left, col_right = st.columns([3, 2])

    # ── Left: Candidate Context ───────────────────────────────────────
    with col_left:
        _render_candidate_panel(
            candidate_name=candidate_name,
            current_question=current_question,
            current_answer=current_answer,
            video_frame_url=video_frame_url,
            topic_list=topic_list or [],
            coverage=suggestion_engine.coverage_stats if hasattr(suggestion_engine, "coverage_stats") else {},
        )

    # ── Right: AI Suggestions + Actions ───────────────────────────────
    with col_right:
        _render_suggestions_panel(suggestion_engine)


def _render_candidate_panel(
    candidate_name: str,
    current_question: str,
    current_answer: str,
    video_frame_url: Optional[str],
    topic_list: List[str],
    coverage: Dict[str, Any],
) -> None:
    """Render the left panel with candidate context."""
    # Video / placeholder
    if video_frame_url:
        st.image(video_frame_url, use_container_width=True)
    else:
        st.markdown(
            '<div style="background:#1a1a2e;border-radius:12px;padding:60px;text-align:center;'
            'color:#667eea;font-size:48px;">📹</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Current question
    st.markdown("#### 📋 Current Question")
    if current_question:
        st.info(current_question)
    else:
        st.caption("No question active")

    # Live transcription
    st.markdown("#### 🎙️ Live Answer")
    if current_answer:
        st.text_area(
            "Transcription",
            value=current_answer,
            height=150,
            disabled=True,
            label_visibility="collapsed",
            key="copilot_live_answer",
        )
    else:
        st.caption("Waiting for candidate response...")

    # Topic coverage
    st.markdown("#### 📊 Topic Coverage")
    total = coverage.get("total_required", 0)
    covered = coverage.get("covered", 0)

    if total > 0:
        progress = covered / total
        st.progress(progress, text=f"{covered}/{total} topics covered ({coverage.get('coverage_pct', 0):.0f}%)")

        remaining = coverage.get("topics_remaining", [])
        if remaining:
            with st.expander(f"⏳ {len(remaining)} topics remaining"):
                for topic in remaining:
                    st.markdown(f"- {topic}")
    else:
        st.caption("No required topics configured")


def _render_suggestions_panel(suggestion_engine: Any) -> None:
    """Render the right panel with suggestions and actions."""
    # Scorecard
    st.markdown("#### 🎯 Candidate Scorecard")
    scorecard = suggestion_engine.get_candidate_scorecard() if hasattr(suggestion_engine, "get_candidate_scorecard") else {}

    avg = scorecard.get("average", 0)
    trend = scorecard.get("trend", "neutral")
    assessment = scorecard.get("assessment", "")

    # Color based on score
    if avg >= 75:
        color = "#2ecc71"
    elif avg >= 50:
        color = "#f39c12"
    else:
        color = "#e74c3c"

    trend_icon = {"improving": "📈 Improving", "declining": "📉 Declining", "neutral": "➡️ Stable"}.get(trend, "➡️")

    st.markdown(
        f'<div class="scorecard">'
        f'<div style="font-size:48px;text-align:center;color:{color};font-weight:700;">{avg:.0f}</div>'
        f'<div style="text-align:center;color:#aaa;font-size:14px;">Average Score</div>'
        f'<div style="text-align:center;margin-top:8px;">{trend_icon}</div>'
        f'<div style="margin-top:8px;font-size:13px;color:#ccc;">{assessment}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

    # Strong / Weak topics
    col_s, col_w = st.columns(2)
    with col_s:
        strong = scorecard.get("strong_topics", [])
        if strong:
            st.markdown("**💪 Strong**")
            for t in strong[-5:]:
                st.success(f"✅ {t}", icon="✅")
    with col_w:
        weak = scorecard.get("weak_topics", [])
        if weak:
            st.markdown("**📈 Growth Areas**")
            for t in weak[-5:]:
                st.warning(f"⚠️ {t}", icon="⚠️")

    st.markdown("---")

    # Quick actions
    st.markdown("#### ⚡ Quick Actions")
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button("💪 Mark Strong", use_container_width=True, key="copilot_mark_strong"):
            topic = _get_current_topic(suggestion_engine)
            if topic:
                suggestion_engine.mark_topic_strong(topic)
                st.toast(f"Marked '{topic}' as strong", icon="💪")
                st.rerun()

    with btn_col2:
        if st.button("🚩 Flag Concern", use_container_width=True, key="copilot_flag"):
            topic = _get_current_topic(suggestion_engine)
            if topic:
                suggestion_engine.flag_concern(topic, reason="Flagged by human interviewer")
                st.toast(f"Flagged concern on '{topic}'", icon="🚩")
                st.rerun()

    with btn_col3:
        if st.button("⏭️ Skip Topic", use_container_width=True, key="copilot_skip"):
            topic = _get_current_topic(suggestion_engine)
            if topic:
                suggestion_engine.skip_topic(topic)
                st.toast(f"Skipped '{topic}'", icon="⏭️")
                st.rerun()

    st.markdown("---")

    # Suggestions
    st.markdown("#### 💡 AI Suggestions")
    suggestions = suggestion_engine.suggestions if hasattr(suggestion_engine, "suggestions") else []

    if not suggestions:
        st.caption("No suggestions yet — analyzing interview in real time...")
    else:
        for i, sug in enumerate(suggestions):
            sug_type = sug.suggestion_type.value if hasattr(sug, "suggestion_type") else sug.get("type", "")
            message = sug.message if hasattr(sug, "message") else sug.get("message", "")
            detail = sug.detail if hasattr(sug, "detail") else sug.get("detail", "")
            priority = sug.priority if hasattr(sug, "priority") else sug.get("priority", 5)

            # Priority styling
            pri_class = f"priority-{min(priority, 3)}" if priority <= 3 else ""
            type_icons = {
                "follow_up": "🔄",
                "probe_deeper": "🔍",
                "rephrase": "💬",
                "star_method": "⭐",
                "gap_fill": "🎯",
                "encourage": "👏",
                "redirect": "🔀",
                "skip": "⏭️",
                "strong_area": "💪",
            }
            icon = type_icons.get(sug_type, "💡")

            st.markdown(
                f'<div class="suggestion-card {pri_class}">'
                f'<div style="font-weight:600;font-size:14px;">{icon} {message}</div>'
                f'<div style="font-size:12px;color:#aaa;margin-top:4px;">{detail}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )

    # Next question suggestion
    if hasattr(suggestion_engine, "suggest_next_question"):
        next_q = suggestion_engine.suggest_next_question()
        if next_q:
            st.markdown("---")
            st.markdown("#### 🎯 Recommended Next Topic")
            st.info(f"**{next_q.message}**\n\n{next_q.detail}")


def _get_current_topic(suggestion_engine: Any) -> str:
    """Get the most recently covered topic from the engine."""
    topics = suggestion_engine.topics_covered if hasattr(suggestion_engine, "topics_covered") else []
    if topics:
        return topics[-1]
    # Fallback: check suggestions
    suggestions = suggestion_engine.suggestions if hasattr(suggestion_engine, "suggestions") else []
    for sug in suggestions:
        topic = sug.topic if hasattr(sug, "topic") else sug.get("topic", "")
        if topic:
            return topic
    return ""
