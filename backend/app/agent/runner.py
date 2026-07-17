"""Orchestrates a full weekly agent run: load data -> run the graph -> persist -> export markdown."""
from pathlib import Path
from typing import Any, Optional

from app.agent.graph import build_graph
from app.agent.markdown_export import build_markdown, plan_filename
from app.agent.state import WeekState
from app.db.supabase_client import get_supabase

PLANS_DIR = Path(__file__).resolve().parent.parent.parent / "generated_plans"


class AgentRunError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _load_project(project_id: str) -> dict[str, Any]:
    resp = get_supabase().table("projects").select("*").eq("id", project_id).execute()
    if not resp.data:
        raise AgentRunError(f"Project {project_id} not found")
    return resp.data[0]


def _load_snapshot(snapshot_id: str) -> dict[str, Any]:
    resp = get_supabase().table("analytics_snapshots").select("*").eq("id", snapshot_id).execute()
    if not resp.data:
        raise AgentRunError(f"Analytics snapshot {snapshot_id} not found")
    return resp.data[0]


def _load_latest_snapshot(project_id: str) -> Optional[dict[str, Any]]:
    resp = (
        get_supabase()
        .table("analytics_snapshots")
        .select("*")
        .eq("project_id", project_id)
        .order("period_end", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def _load_prior_snapshot(project_id: str, before_period_end: str) -> Optional[dict[str, Any]]:
    resp = (
        get_supabase()
        .table("analytics_snapshots")
        .select("*")
        .eq("project_id", project_id)
        .lt("period_end", before_period_end)
        .order("period_end", desc=True)
        .limit(1)
        .execute()
    )
    return resp.data[0] if resp.data else None


def _next_week_number(project_id: str) -> int:
    resp = get_supabase().table("weeks").select("id", count="exact").eq("project_id", project_id).execute()
    return (resp.count or 0) + 1


def _load_last_week_posts(project_id: str) -> list[dict[str, Any]]:
    resp = (
        get_supabase()
        .table("weeks")
        .select("id")
        .eq("project_id", project_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not resp.data:
        return []
    last_week_id = resp.data[0]["id"]
    posts_resp = get_supabase().table("posts").select("*").eq("week_id", last_week_id).execute()
    return posts_resp.data or []


def _prepare_run(project_id: str, snapshot_id: Optional[str]) -> tuple[dict[str, Any], int, WeekState]:
    project = _load_project(project_id)

    current_snapshot = _load_snapshot(snapshot_id) if snapshot_id else _load_latest_snapshot(project_id)
    if current_snapshot is None:
        raise AgentRunError("No analytics snapshot found for this project — upload an export first.")

    prior_snapshot = _load_prior_snapshot(project_id, current_snapshot["period_end"])
    last_week_posts = _load_last_week_posts(project_id)
    week_number = _next_week_number(project_id)

    initial_state: WeekState = {
        "project": project,
        "week_number": week_number,
        "current_snapshot": current_snapshot,
        "prior_snapshot": prior_snapshot,
        "last_week_posts": last_week_posts,
        "revision_count": 0,
        "warnings": [],
    }
    return project, week_number, initial_state


def _finalize_run(
    project_id: str, project: dict[str, Any], week_number: int, final_state: dict[str, Any]
) -> dict[str, Any]:
    snapshot_id = final_state["current_snapshot"]["id"]
    week_row = _persist_week(project_id, week_number, snapshot_id, final_state)
    post_rows = _persist_posts(project_id, week_row["id"], final_state.get("posts", []))
    _update_project_strategy(project_id, final_state.get("strategy", {}))

    markdown = build_markdown(project, week_number, final_state)
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    filename = plan_filename(project_id, week_number)
    (PLANS_DIR / filename).write_text(markdown, encoding="utf-8")

    return {
        "week": week_row,
        "posts": post_rows,
        "plan_filename": filename,
        "is_recovery_week": final_state.get("is_recovery_week", False),
        "warnings": final_state.get("warnings", []),
    }


async def run_weekly_agent(project_id: str, snapshot_id: Optional[str] = None) -> dict[str, Any]:
    project, week_number, initial_state = _prepare_run(project_id, snapshot_id)

    graph = build_graph()
    final_state = await graph.ainvoke(initial_state, config={"recursion_limit": 50})

    return _finalize_run(project_id, project, week_number, final_state)


# Human-friendly labels streamed to the UI so it can show which specialist is working.
NODE_LABELS = {
    "analyst": "Analyst reading your export…",
    "profiler": "Audience Profiler studying who actually follows you…",
    "researcher": "Researcher scanning this week's news…",
    "historian": "Historian recalling past learnings…",
    "strategist": "Strategist deciding this week's plan…",
    "copywriter": "Copywriter drafting your posts…",
    "creative_director": "Creative Director designing image prompts…",
    "critic": "Critic scoring and refining drafts…",
    "librarian": "Librarian saving what it learned…",
}


async def stream_weekly_agent(project_id: str, snapshot_id: Optional[str] = None):
    """Async generator yielding progress dicts as each node finishes, then a final 'done' event.

    Uses LangGraph's astream in 'updates' mode; each chunk is {node_name: partial_state}. Since
    every node returns only the keys it changed (no reducers), merging updates last-write-wins
    reconstructs the same final state ainvoke would produce.
    """
    project, week_number, initial_state = _prepare_run(project_id, snapshot_id)

    graph = build_graph()
    accumulated: dict[str, Any] = dict(initial_state)

    async for chunk in graph.astream(initial_state, config={"recursion_limit": 50}, stream_mode="updates"):
        for node_name, update in chunk.items():
            if isinstance(update, dict):
                accumulated.update(update)
            yield {
                "type": "progress",
                "node": node_name,
                "label": NODE_LABELS.get(node_name, node_name),
            }

    result = _finalize_run(project_id, project, week_number, accumulated)
    yield {"type": "done", "result": result}


def _persist_week(
    project_id: str, week_number: int, snapshot_id: str, final_state: dict[str, Any]
) -> dict[str, Any]:
    strategy = final_state.get("strategy", {})
    row = {
        "project_id": project_id,
        "week_number": week_number,
        "snapshot_id": snapshot_id,
        "theme": strategy.get("week_theme"),
        "diagnosis": {
            "analyst": final_state.get("analyst_diagnosis"),
            "audience_profile": final_state.get("audience_profile"),
        },
        "cadence_decision": strategy.get("cadence_decision"),
        "research": final_state.get("research_findings"),
        "reasoning": (
            strategy.get("recovery_plan")
            if final_state.get("is_recovery_week")
            else strategy.get("reasoning_summary")
        ),
    }
    resp = get_supabase().table("weeks").insert(row).execute()
    if not resp.data:
        raise AgentRunError("Supabase returned no data after inserting the week")
    return resp.data[0]


def _persist_posts(project_id: str, week_id: str, posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not posts:
        return []
    rows = [
        {
            "project_id": project_id,
            "week_id": week_id,
            "post_code": p.get("post_code"),
            "scheduled_day": p.get("scheduled_day"),
            "best_time": p.get("best_time"),
            "format": p.get("format"),
            "funnel_job": p.get("funnel_job"),
            "hook": p.get("hook"),
            "caption": p.get("caption"),
            "hashtags": p.get("hashtags"),
            "tag_suggestions": p.get("tag_suggestions"),
            "image_prompt": p.get("image_prompt"),
            "psychology_notes": p.get("psychology_notes"),
            "critic_score": p.get("critic_score"),
            "critic_notes": p.get("critic_notes"),
        }
        for p in posts
    ]
    resp = get_supabase().table("posts").insert(rows).execute()
    if not resp.data:
        raise AgentRunError("Supabase returned no data after inserting posts")
    return resp.data


def _update_project_strategy(project_id: str, strategy: dict[str, Any]) -> None:
    if not strategy:
        return
    get_supabase().table("projects").update(
        {
            "growth_stage": strategy.get("growth_stage"),
            "current_cadence": strategy.get("cadence_decision"),
            "strategy": strategy,
        }
    ).eq("id", project_id).execute()
