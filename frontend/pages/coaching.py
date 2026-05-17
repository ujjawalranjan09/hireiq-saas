"""Coaching plan display page — post-interview improvement roadmap."""

import streamlit as st


def show():
    """Render the coaching plan page."""
    st.set_page_config(page_title="AI Coaching", page_icon="🎓", layout="wide")

    # Check for interview results
    results = st.session_state.get("interview_results")
    coaching_plan = st.session_state.get("coaching_plan")

    if not results and not coaching_plan:
        _render_no_data()
        return

    # Generate plan if not cached
    if not coaching_plan and results:
        coaching_plan = _generate_coaching_plan(results)
        if coaching_plan:
            st.session_state["coaching_plan"] = coaching_plan

    if not coaching_plan:
        _render_no_data()
        return

    _render_coaching_plan(coaching_plan)


def _render_no_data():
    """Render when no interview data is available."""
    st.title("🎓 AI Coaching Plan")
    st.markdown(
        "After completing an interview, this page will show a personalized "
        "improvement plan based on your performance."
    )
    st.markdown("---")
    st.info("📝 Complete an interview first to generate your coaching plan.")

    if st.button("🏠 Start Interview", type="primary"):
        st.session_state["current_page"] = "home"
        st.rerun()


def _generate_coaching_plan(results):
    """Generate coaching plan from interview results."""
    try:
        from modules.coaching.plan_generator import CoachingPlanGenerator
        from modules.coaching.resource_recommender import ResourceRecommender

        resource_rec = ResourceRecommender()
        generator = CoachingPlanGenerator(resource_recommender=resource_rec)

        # Extract data from results
        metrics = results.get("report", {}).get("metrics", results.get("metrics", {}))
        feedback = results.get("report", {}).get("feedback", results.get("feedback", {}))

        candidate_name = st.session_state.get("candidate_name", "Candidate")
        overall_score = metrics.get("average_score", results.get("average_score", 0))

        # Build question results
        interview_id = st.session_state.get("interview_id")
        question_results = []
        if interview_id:
            try:
                from database.queries import get_questions_for_interview
                db_questions = get_questions_for_interview(interview_id)
                question_results = [
                    {
                        "question_text": q.question_text,
                        "question_type": q.question_type,
                        "target_skill": getattr(q, "target_skill", q.question_type),
                        "answer_score": q.answer_score,
                    }
                    for q in db_questions
                ]
            except Exception:
                pass

        if not question_results:
            # Fallback: generate from feedback/weaknesses
            weaknesses = feedback.get("weaknesses", [])
            question_results = [
                {"question_type": "general", "target_skill": w, "answer_score": 40}
                for w in weaknesses
            ]

        strong_topics = feedback.get("strengths", [])

        plan = generator.generate_plan(
            candidate_name=candidate_name,
            question_results=question_results,
            overall_score=overall_score,
            strong_topics=strong_topics,
        )
        return plan.to_dict()

    except Exception as e:
        st.error(f"Error generating coaching plan: {e}")
        return None


def _render_coaching_plan(plan):
    """Render the complete coaching plan."""
    name = plan.get("candidate_name", "Candidate")
    score = plan.get("overall_score", 0)

    # Header
    st.title(f"🎓 Coaching Plan for {name}")

    # Score-based message
    if score >= 75:
        st.success(f"🎉 **Overall Score: {score:.0f}/100** — Strong performance! Fine-tune your weaker areas to reach excellence.")
    elif score >= 50:
        st.info(f"📊 **Overall Score: {score:.0f}/100** — Good foundation with clear areas for growth.")
    else:
        st.warning(f"📈 **Overall Score: {score:.0f}/100** — Significant growth opportunities. Let's build a plan.")

    st.markdown("---")

    # Tab layout
    tab_overview, tab_details, tab_timeline, tab_resources = st.tabs([
        "📋 Overview",
        "🎯 Topic Breakdown",
        "📅 Study Timeline",
        "📚 Resources",
    ])

    # ── Overview Tab ──────────────────────────────────────────────────
    with tab_overview:
        _render_overview(plan)

    # ── Topic Breakdown Tab ───────────────────────────────────────────
    with tab_details:
        _render_topic_breakdown(plan)

    # ── Study Timeline Tab ────────────────────────────────────────────
    with tab_timeline:
        _render_timeline(plan)

    # ── Resources Tab ─────────────────────────────────────────────────
    with tab_resources:
        _render_resources(plan)

    # Navigation
    st.markdown("---")
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    with col_nav1:
        if st.button("📊 View Results", use_container_width=True):
            st.session_state["current_page"] = "results"
            st.rerun()
    with col_nav2:
        if st.button("📥 Download Plan", use_container_width=True):
            _download_plan(plan)
    with col_nav3:
        if st.button("🏠 New Interview", use_container_width=True, type="primary"):
            for key in ["interview_results", "coaching_plan", "interview_id"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["current_page"] = "home"
            st.rerun()


def _render_overview(plan):
    """Render the coaching overview section."""
    strong = plan.get("strong_topics", [])
    weak = plan.get("weak_topics", [])
    advice = plan.get("coaching_advice", "")

    col_str, col_weak = st.columns(2)

    with col_str:
        st.markdown("### 💪 Your Strengths")
        if strong:
            for topic in strong:
                st.success(f"✅ {topic}")
        else:
            st.caption("No strong areas identified yet.")

    with col_weak:
        st.markdown("### 📈 Areas to Improve")
        if weak:
            for tp in weak[:6]:
                topic_name = tp.get("topic", "") if isinstance(tp, dict) else tp
                level = tp.get("current_level", "beginner") if isinstance(tp, dict) else ""
                st.warning(f"⚠️ **{topic_name}** — {level}")
        else:
            st.caption("No weak areas identified — great job!")

    # Coaching advice
    if advice:
        st.markdown("---")
        st.markdown("### 🗣️ Personalized Coaching Advice")
        st.markdown(advice)

    # Match stats
    st.markdown("---")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Strong Topics", len(strong))
    with col_s2:
        st.metric("Growth Areas", len(weak))
    with col_s3:
        total = len(strong) + len(weak)
        match = len(strong) / total * 100 if total > 0 else 0
        st.metric("Strength Ratio", f"{match:.0f}%")


def _render_topic_breakdown(plan):
    """Render detailed topic-by-topic breakdown."""
    weak_topics = plan.get("weak_topics", [])

    if not weak_topics:
        st.info("🎉 No weak areas identified — keep up the excellent work!")
        return

    for i, tp in enumerate(weak_topics):
        topic = tp.get("topic", f"Topic {i+1}")
        current = tp.get("current_level", "beginner")
        target = tp.get("target_level", "intermediate")
        description = tp.get("gap_description", "")
        exercises = tp.get("practice_exercises", [])
        estimated = tp.get("estimated_time", "2-4 weeks")
        resources = tp.get("resources", [])

        with st.expander(f"📖 {topic} — {current} → {target} ({estimated})"):
            # Progress bar
            level_map = {"beginner": 0.25, "intermediate": 0.5, "advanced": 0.75, "expert": 1.0}
            current_pct = level_map.get(current, 0.25)
            target_pct = level_map.get(target, 0.5)

            col_cur, col_tar = st.columns(2)
            with col_cur:
                st.markdown(f"**Current Level:** {current.capitalize()}")
                st.progress(current_pct)
            with col_tar:
                st.markdown(f"**Target Level:** {target.capitalize()}")
                st.progress(target_pct)

            if description:
                st.markdown(f"**Gap:** {description}")

            # Practice exercises
            if exercises:
                st.markdown("**🏋️ Practice Exercises:**")
                for ex in exercises:
                    st.markdown(f"- {ex}")

            # Resources for this topic
            if resources:
                st.markdown("**📚 Top Resources:**")
                for r in resources[:3]:
                    if isinstance(r, dict):
                        title = r.get("title", "")
                        rtype = r.get("type", "")
                        url = r.get("url", "")
                        platform = r.get("platform", "")
                        if url:
                            st.markdown(f"- [{title}]({url}) ({rtype} — {platform})")
                        else:
                            st.markdown(f"- {title} ({rtype} — {platform})")

            st.markdown(f"**⏱️ Estimated Time:** {estimated}")


def _render_timeline(plan):
    """Render the study timeline."""
    st.markdown("### 📅 Your Improvement Roadmap")

    one_week = plan.get("one_week_plan", "")
    one_month = plan.get("one_month_plan", "")
    three_month = plan.get("three_month_plan", "")

    tab_1w, tab_1m, tab_3m = st.tabs(["1 Week Sprint", "1 Month Plan", "3 Month Roadmap"])

    with tab_1w:
        if one_week:
            st.markdown(one_week)
        else:
            st.info("No 1-week plan generated.")

    with tab_1m:
        if one_month:
            st.markdown(one_month)
        else:
            st.info("No 1-month plan generated.")

    with tab_3m:
        if three_month:
            st.markdown(three_month)
        else:
            st.info("No 3-month plan generated.")


def _render_resources(plan):
    """Render all recommended resources organized by topic."""
    st.markdown("### 📚 All Recommended Resources")

    weak_topics = plan.get("weak_topics", [])
    if not weak_topics:
        st.info("No resources needed — you're doing great!")
        return

    # Collect all resources
    all_resources = []
    for tp in weak_topics:
        topic = tp.get("topic", "")
        for r in tp.get("resources", []):
            if isinstance(r, dict):
                all_resources.append({"topic": topic, **r})

    if not all_resources:
        st.caption("No specific resources available.")
        return

    # Group by type
    by_type = {}
    for r in all_resources:
        rtype = r.get("type", "other")
        if rtype not in by_type:
            by_type[rtype] = []
        by_type[rtype].append(r)

    type_icons = {
        "course": "🎓",
        "book": "📚",
        "video": "🎬",
        "article": "📄",
        "practice_problem": "💻",
    }

    for rtype, resources in by_type.items():
        icon = type_icons.get(rtype, "📌")
        st.markdown(f"#### {icon} {rtype.replace('_', ' ').title()}s")

        for r in resources:
            title = r.get("title", "")
            url = r.get("url", "")
            platform = r.get("platform", "")
            difficulty = r.get("difficulty", "")
            topic = r.get("topic", "")
            desc = r.get("description", "")

            col_title, col_meta = st.columns([3, 1])
            with col_title:
                if url:
                    st.markdown(f"**[{title}]({url})**")
                else:
                    st.markdown(f"**{title}**")
                if desc:
                    st.caption(desc)
            with col_meta:
                st.markdown(f"*{topic}*")
                st.caption(f"{platform} | {difficulty}")

        st.markdown("")

    # Quick links to practice platforms
    st.markdown("---")
    st.markdown("### 🏃 Practice Platforms")
    platform_col1, platform_col2, platform_col3, platform_col4 = st.columns(4)
    platforms = [
        ("LeetCode", "https://leetcode.com/"),
        ("HackerRank", "https://www.hackerrank.com/"),
        ("Pramp", "https://www.pramp.com/"),
        ("Interviewing.io", "https://interviewing.io/"),
    ]
    for (name, url), col in zip(platforms, [platform_col1, platform_col2, platform_col3, platform_col4]):
        with col:
            st.link_button(f"🔗 {name}", url, use_container_width=True)


def _download_plan(plan):
    """Generate a downloadable text version of the plan."""
    name = plan.get("candidate_name", "Candidate")
    score = plan.get("overall_score", 0)

    lines = [
        f"AI COACHING PLAN — {name}",
        f"Overall Score: {score:.0f}/100",
        "=" * 50,
        "",
    ]

    # Strengths
    strong = plan.get("strong_topics", [])
    if strong:
        lines.append("STRENGTHS:")
        for s in strong:
            lines.append(f"  ✅ {s}")
        lines.append("")

    # Weak areas
    weak = plan.get("weak_topics", [])
    if weak:
        lines.append("AREAS TO IMPROVE:")
        for tp in weak:
            topic = tp.get("topic", "")
            current = tp.get("current_level", "")
            target = tp.get("target_level", "")
            lines.append(f"  📖 {topic} ({current} → {target})")
            for ex in tp.get("practice_exercises", []):
                lines.append(f"     - {ex}")
            for r in tp.get("resources", []):
                if isinstance(r, dict):
                    lines.append(f"     📚 {r.get('title', '')} [{r.get('url', '')}]")
        lines.append("")

    # Timeline
    for label, key in [("1-WEEK PLAN", "one_week_plan"), ("1-MONTH PLAN", "one_month_plan"), ("3-MONTH PLAN", "three_month_plan")]:
        content = plan.get(key, "")
        if content:
            lines.append(f"{label}:")
            lines.append(content)
            lines.append("")

    # Coaching advice
    advice = plan.get("coaching_advice", "")
    if advice:
        lines.append("COACHING ADVICE:")
        lines.append(advice)

    text = "\n".join(lines)
    st.download_button(
        label="📥 Download Plan as Text",
        data=text,
        file_name=f"coaching_plan_{name.replace(' ', '_').lower()}.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True,
    )
