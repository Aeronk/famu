"""LangGraph agent: detect language -> classify -> act -> respond.

The graph is pure orchestration; side effects happen via injected ``AgentDeps``
and the data-capture tools. Persisting conversation history is the caller's job
(WhatsApp pipeline / AI router), keeping the graph reusable.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.advisory.service import AdvisoryService
from app.ai.agents.extraction import extract
from app.ai.agents.schemas import AgentDeps, AgentReply
from app.ai.agents.tools import dispatch
from app.shared.enums import Language
from app.shared.i18n import detect_language, translate


class AgentState(TypedDict, total=False):
    text: str
    language: str
    intent: str
    entities: dict
    deps: AgentDeps
    tool_result: Any
    advisory: dict
    reply: str
    record_id: str | None
    follow_up: bool


async def _detect(state: AgentState) -> AgentState:
    return {"language": detect_language(state["text"]).value}


async def _classify(state: AgentState) -> AgentState:
    result = await extract(state["text"], lang=Language(state["language"]))
    return {"intent": result.intent, "entities": result.entities}


async def _act(state: AgentState) -> AgentState:
    deps: AgentDeps = state["deps"]
    intent = state["intent"]
    entities = state.get("entities", {})

    tool_result = await dispatch(intent, entities, deps)
    if tool_result is not None:
        return {"tool_result": tool_result, "record_id": tool_result.record_id}

    if intent == "ask_question":
        advisory = await AdvisoryService(deps.session).ask(
            entities.get("query", state["text"]),
            tenant_id=deps.tenant_id,
            language=Language(state["language"]),
        )
        return {"advisory": advisory}
    return {}


async def _respond(state: AgentState) -> AgentState:
    lang = state["language"]
    tool_result = state.get("tool_result")
    advisory = state.get("advisory")
    follow_up = False

    if tool_result is not None and tool_result.success:
        reply = translate(tool_result.reply_key, lang, **tool_result.reply_kwargs)
        if tool_result.follow_up_key:
            reply = f"{reply} {translate(tool_result.follow_up_key, lang)}"
            follow_up = True
    elif tool_result is not None and not tool_result.success:
        reply = translate("not_understood", lang)
    elif advisory is not None:
        reply = advisory["answer"]
    elif state["intent"] == "greeting":
        reply = translate("greeting", lang)
    else:
        reply = translate("not_understood", lang)

    return {"reply": reply, "follow_up": follow_up}


def _build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("detect", _detect)
    graph.add_node("classify", _classify)
    graph.add_node("act", _act)
    graph.add_node("respond", _respond)
    graph.add_edge(START, "detect")
    graph.add_edge("detect", "classify")
    graph.add_edge("classify", "act")
    graph.add_edge("act", "respond")
    graph.add_edge("respond", END)
    return graph.compile()


agent_app = _build_graph()


async def run_agent(text: str, deps: AgentDeps) -> AgentReply:
    final: AgentState = await agent_app.ainvoke({"text": text, "deps": deps})
    return AgentReply(
        reply=final.get("reply", ""),
        intent=final.get("intent", "unknown"),
        entities=final.get("entities", {}),
        language=Language(final.get("language", "en")),
        record_id=final.get("record_id"),
        follow_up=final.get("follow_up", False),
    )
