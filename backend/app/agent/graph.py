"""Builds and compiles the weekly LangGraph agent.

Edges: analyst -> profiler -> researcher -> historian -> strategist -> (conditional)
  - cadence = 0 posts -> straight to librarian (recovery/repositioning plan, no posts)
  - otherwise -> copywriter -> creative_director -> critic -> (conditional)
      - any post scored < 7 and revision budget remains -> back to copywriter
      - otherwise -> librarian -> END
"""
from langgraph.graph import END, StateGraph

from app.agent.nodes.analyst import analyst_node
from app.agent.nodes.copywriter import copywriter_node
from app.agent.nodes.creative_director import creative_director_node
from app.agent.nodes.critic import critic_node
from app.agent.nodes.historian import historian_node
from app.agent.nodes.librarian import librarian_node
from app.agent.nodes.profiler import profiler_node
from app.agent.nodes.researcher import researcher_node
from app.agent.nodes.strategist import strategist_node
from app.agent.state import WeekState


def _route_after_strategist(state: WeekState) -> str:
    return "librarian" if state.get("is_recovery_week") else "copywriter"


def _route_after_critic(state: WeekState) -> str:
    if any(r.get("needs_revision") for r in state.get("critic_reviews", [])):
        return "copywriter"
    return "librarian"


def build_graph():
    graph = StateGraph(WeekState)

    graph.add_node("analyst", analyst_node)
    graph.add_node("profiler", profiler_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("historian", historian_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("copywriter", copywriter_node)
    graph.add_node("creative_director", creative_director_node)
    graph.add_node("critic", critic_node)
    graph.add_node("librarian", librarian_node)

    graph.set_entry_point("analyst")
    graph.add_edge("analyst", "profiler")
    graph.add_edge("profiler", "researcher")
    graph.add_edge("researcher", "historian")
    graph.add_edge("historian", "strategist")
    graph.add_conditional_edges(
        "strategist", _route_after_strategist, {"librarian": "librarian", "copywriter": "copywriter"}
    )
    graph.add_edge("copywriter", "creative_director")
    graph.add_edge("creative_director", "critic")
    graph.add_conditional_edges(
        "critic", _route_after_critic, {"copywriter": "copywriter", "librarian": "librarian"}
    )
    graph.add_edge("librarian", END)

    return graph.compile()
