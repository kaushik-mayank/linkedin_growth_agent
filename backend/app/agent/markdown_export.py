"""Generates the downloadable Markdown weekly plan file."""
from datetime import datetime, timezone
from typing import Any


def plan_filename(project_id: str, week_number: int) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"plan_{project_id}_week{week_number:02d}_{ts}.md"


def build_markdown(project: dict[str, Any], week_number: int, state: dict[str, Any]) -> str:
    strategy = state.get("strategy", {})
    diagnosis = state.get("analyst_diagnosis", {})
    audience = state.get("audience_profile", {})
    research = state.get("research_findings", {})
    posts = state.get("posts", [])
    is_recovery = state.get("is_recovery_week", False)
    cadence = strategy.get("cadence_decision", {})

    lines: list[str] = []
    lines.append(f"# {project.get('name')} — Week {week_number} Plan")
    lines.append(f"_Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_")
    lines.append("")
    lines.append(f"**Growth stage:** {strategy.get('growth_stage', 'unknown')}")
    lines.append(f"**Theme:** {strategy.get('week_theme', '')}")
    lines.append("")

    lines.append("## Diagnosis")
    lines.append(f"**Account state:** {diagnosis.get('account_state', 'unknown')}")
    if diagnosis.get("fatigue_detected"):
        lines.append(f"**Audience fatigue detected:** {diagnosis.get('fatigue_evidence', '')}")
    lines.append("")
    lines.append(diagnosis.get("narrative", ""))
    if diagnosis.get("unknowns"):
        lines.append("")
        lines.append("**What we don't know yet:**")
        for u in diagnosis["unknowns"]:
            lines.append(f"- {u}")
    lines.append("")

    lines.append("## Audience")
    lines.append(audience.get("actual_audience_summary", ""))
    if audience.get("drift_detected"):
        lines.append("")
        lines.append(f"**Audience drift:** {audience.get('drift_explanation', '')}")
    lines.append("")

    lines.append("## Cadence Decision")
    lines.append(f"**Posts this week: {cadence.get('posts_this_week', 0)}**")
    lines.append("")
    lines.append(cadence.get("reasoning", ""))
    lines.append("")

    if research.get("findings"):
        lines.append("## This Week's Live Trends")
        for f in research["findings"]:
            date = f.get("published_date") or "undated"
            lines.append(f"- [{f.get('title')}]({f.get('url')}) ({date}) — {f.get('why_relevant')}")
        lines.append("")

    if is_recovery:
        lines.append("## Recovery / Repositioning Plan")
        lines.append(strategy.get("recovery_plan") or strategy.get("reasoning_summary", ""))
        lines.append("")
    else:
        lines.append("## Posts")
        for p in posts:
            lines.append(f"### {p.get('post_code')} — {p.get('scheduled_day')} at {p.get('best_time')}")
            lines.append(
                f"**Format:** {p.get('format')} | **Funnel job:** {p.get('funnel_job')} | "
                f"**Critic score:** {p.get('critic_score')}/10"
            )
            lines.append("")
            lines.append(f"**Hook:** {p.get('hook')}")
            lines.append("")
            lines.append("**Caption:**")
            lines.append("```")
            lines.append(p.get("caption", ""))
            lines.append("```")
            lines.append("")
            hashtags = p.get("hashtags") or []
            hashtags_str = " ".join("#" + h.lstrip("#") for h in hashtags)
            lines.append(f"**Hashtags:** {hashtags_str}")
            lines.append(f"**Tag suggestions:** {p.get('tag_suggestions', '')}")
            lines.append(f"**Image prompt:** {p.get('image_prompt', 'text-only')}")
            lines.append(f"**Psychology notes:** {p.get('psychology_notes', '')}")
            if p.get("critic_notes"):
                lines.append(f"**Critic notes:** {p.get('critic_notes')}")
            lines.append("")

    return "\n".join(lines)
