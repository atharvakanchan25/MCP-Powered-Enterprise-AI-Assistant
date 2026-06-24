"""
LangGraph multi-agent workflow:

  START
    └─► planner_node
          └─► research_node   (parallel-ish via sequential but fast)
                └─► tool_node
                      └─► rag_node
                            └─► memory_node
                                  └─► report_node
                                        └─► END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.nodes import (
    memory_node,
    planner_node,
    rag_node,
    report_node,
    research_node,
    tool_node,
)
from app.agents.state import AgentState


def build_workflow() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("research", research_node)
    graph.add_node("tool", tool_node)
    graph.add_node("rag", rag_node)
    graph.add_node("memory", memory_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "research")
    graph.add_edge("research", "tool")
    graph.add_edge("tool", "rag")
    graph.add_edge("rag", "memory")
    graph.add_edge("memory", "report")
    graph.add_edge("report", END)

    return graph


# Compiled singleton reused across requests
_compiled = None


def get_workflow():
    global _compiled
    if _compiled is None:
        _compiled = build_workflow().compile()
    return _compiled
