from app.agent.markdown_export import build_markdown, plan_filename


def test_plan_filename_includes_project_id_and_week_and_is_unique_by_timestamp():
    name1 = plan_filename("abc-123", 3)
    name2 = plan_filename("abc-123", 3)
    assert "abc-123" in name1
    assert "week03" in name1
    assert name1.endswith(".md")


def test_recovery_week_markdown_shows_recovery_plan_not_posts():
    project = {"name": "Test Account"}
    state = {
        "strategy": {
            "growth_stage": "foundation",
            "week_theme": "Reset positioning",
            "cadence_decision": {"posts_this_week": 0, "reasoning": "Account is dormant."},
            "recovery_plan": "Fix your bio and headline before posting again.",
        },
        "analyst_diagnosis": {"account_state": "dormant", "narrative": "No activity this period."},
        "audience_profile": {"actual_audience_summary": "Mostly data analysts."},
        "research_findings": {},
        "posts": [],
        "is_recovery_week": True,
    }
    md = build_markdown(project, 1, state)
    assert "Recovery / Repositioning Plan" in md
    assert "Fix your bio and headline" in md
    assert "## Posts" not in md


def test_normal_week_markdown_includes_post_details():
    project = {"name": "Test Account"}
    state = {
        "strategy": {
            "growth_stage": "signal",
            "week_theme": "Test formats",
            "cadence_decision": {"posts_this_week": 1, "reasoning": "Engagement is trending up."},
        },
        "analyst_diagnosis": {"account_state": "growing", "narrative": "Steady growth."},
        "audience_profile": {"actual_audience_summary": "Founders and PMs."},
        "research_findings": {"findings": [{"title": "AI news", "url": "https://x.com", "published_date": "2026-07-10", "why_relevant": "audience cares about this"}]},
        "posts": [
            {
                "post_code": "W01-01", "scheduled_day": "Tuesday", "best_time": "9am",
                "format": "text", "funnel_job": "trust", "hook": "Here's what nobody tells you...",
                "caption": "Full caption body here.", "hashtags": ["growth", "linkedin"],
                "tag_suggestions": "Tag other founders", "image_prompt": "text-only",
                "psychology_notes": "Uses open loop.", "critic_score": 8, "critic_notes": "Strong hook.",
            }
        ],
        "is_recovery_week": False,
    }
    md = build_markdown(project, 1, state)
    assert "W01-01" in md
    assert "Full caption body here." in md
    assert "#growth" in md
    assert "AI news" in md
