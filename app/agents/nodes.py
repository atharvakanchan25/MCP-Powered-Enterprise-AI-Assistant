"""
LangGraph node implementations for each agent role.
Each node receives AgentState, mutates it, and returns the updated state.
"""
from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.agents.state import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger
from app.mcp.client import MCPClient

logger = get_logger(__name__)
_mcp = MCPClient()


def _llm() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=get_settings().openai_api_key)


async def planner_node(state: AgentState) -> AgentState:
    """Decomposes the user query into a plan and selects relevant tools."""
    settings = get_settings()
    tools_info = json.dumps([t["function"]["name"] + ": " + t["function"]["description"]
                              for t in _mcp.list_tools()], indent=2)
    memories_ctx = "\n".join(f"- {m['key']}: {m['value']}" for m in state.get("memories", []))

    prompt = f"""You are a planner agent. Given the user query, create a step-by-step plan and select the minimal set of tools needed.

Available tools:
{tools_info}

User memory context:
{memories_ctx or 'None'}

User query: {state['query']}

Respond in JSON:
{{
  "plan": "step-by-step reasoning plan",
  "selected_tools": ["tool_name1", "tool_name2"],
  "reasoning": ["why tool1", "why tool2"]
}}"""

    client = _llm()
    resp = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.agent_temperature,
        response_format={"type": "json_object"},
    )
    try:
        data = json.loads(resp.choices[0].message.content or "{}")
    except json.JSONDecodeError:
        data = {}

    state["plan"] = data.get("plan", "Direct answer without tools")
    state["selected_tools"] = data.get("selected_tools", [])
    state["reasoning"] = data.get("reasoning", [])
    state.setdefault("iteration", 0)
    logger.info("planner.done", plan=state["plan"], tools=state["selected_tools"])
    return state


async def research_node(state: AgentState) -> AgentState:
    """Executes web search if needed to gather external context."""
    if "web_search" not in state.get("selected_tools", []):
        return state

    result = await _mcp.execute("web_search", query=state["query"])
    results = state.get("tool_results", [])
    results.append({"tool": "web_search", "success": result.success, "output": result.output, "error": result.error})
    state["tool_results"] = results
    return state


async def tool_node(state: AgentState) -> AgentState:
    """Executes all non-search, non-rag MCP tools selected by the planner."""
    skip = {"web_search", "rag_query"}
    tool_results = state.get("tool_results", [])

    for tool_name in state.get("selected_tools", []):
        if tool_name in skip:
            continue
        # Extract args from plan context via LLM
        settings = get_settings()
        client = _llm()
        arg_prompt = f"""Given this plan: {state.get('plan', '')}
Extract the JSON arguments for the tool '{tool_name}'. 
Tool parameters schema: {json.dumps(next((t['function']['parameters'] for t in _mcp.list_tools() if t['function']['name'] == tool_name), {}), indent=2)}
Respond ONLY with a valid JSON object of arguments."""
        resp = await client.chat.completions.create(
            model=settings.openai_chat_model,
            messages=[{"role": "user", "content": arg_prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        try:
            args = json.loads(resp.choices[0].message.content or "{}")
        except json.JSONDecodeError:
            args = {}

        result = await _mcp.execute(tool_name, **args)
        tool_results.append({
            "tool": tool_name,
            "args": args,
            "success": result.success,
            "output": result.output,
            "error": result.error,
            "duration_ms": result.duration_ms,
        })

    state["tool_results"] = tool_results
    return state


async def rag_node(state: AgentState) -> AgentState:
    """Queries the vector knowledge base for relevant context."""
    from app.services.rag.query import semantic_search

    hits = await semantic_search(state["query"], top_k=get_settings().rag_top_k)
    state["rag_context"] = [
        {"filename": c.filename, "page": c.page, "score": c.score, "excerpt": c.excerpt}
        for c in hits
    ]
    state["citations"] = state["rag_context"]
    return state


async def memory_node(state: AgentState) -> AgentState:
    """Stores key facts from this interaction into agent memory (fire-and-forget pattern)."""
    # Memory is stored by the orchestrator after full completion; here we just surface existing ones
    return state


async def report_node(state: AgentState) -> AgentState:
    """Synthesizes all gathered context into a final structured answer."""
    settings = get_settings()

    tool_summary = "\n".join(
        f"- [{r['tool']}]: {'SUCCESS' if r['success'] else 'FAILED'} → {json.dumps(r.get('output', r.get('error')))[:300]}"
        for r in state.get("tool_results", [])
    )
    rag_summary = "\n".join(
        f"- [{r['filename']} p.{r['page']}] (score: {r['score']}): {r['excerpt'][:200]}"
        for r in state.get("rag_context", [])
    )

    synthesis_prompt = f"""You are a report agent. Synthesize a clear, comprehensive answer.

User query: {state['query']}

Execution plan followed:
{state.get('plan', 'N/A')}

Tool results:
{tool_summary or 'No tools executed'}

Knowledge base context:
{rag_summary or 'No RAG context'}

Reasoning steps:
{chr(10).join(f'  {i+1}. {r}' for i, r in enumerate(state.get('reasoning', [])))}

Write a clear, well-structured answer with citations where available. Be concise."""

    client = _llm()
    resp = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[{"role": "user", "content": synthesis_prompt}],
        temperature=settings.agent_temperature,
    )
    state["final_answer"] = resp.choices[0].message.content or "Unable to generate answer."
    if resp.usage:
        state["token_usage"] = {
            "prompt_tokens": resp.usage.prompt_tokens,
            "completion_tokens": resp.usage.completion_tokens,
            "total_tokens": resp.usage.total_tokens,
        }
    return state
