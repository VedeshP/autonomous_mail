# backend/app/agent/graph.py

from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from app.agent.llm import get_llm
from app.agent.tools.email_tools import search_tools_list
from app.agent.tools.action_tools import action_tools_list

# --- 1. Define the Custom State ---
class AgentState(TypedDict):
    """The memory object passed between nodes."""
    # add_messages tells LangGraph to append to the list, not overwrite it
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # We add the user_id to the state!
    user_id: str

# --- 2. Combine all tools ---
all_tools = search_tools_list + action_tools_list

# --- 3. The System Prompt ---
SYSTEM_PROMPT = """
You are AetherMail, a highly intelligent personal executive assistant.
You have the power to read, organize, and draft emails for the user.

CRITICAL RULES:
1. If the user asks you to organize, label, delete, or archive, YOU MUST execute it using the `organize_email` tool.
2. If the user asks you to draft a reply, YOU MUST execute it using the `create_draft_reply` tool.
3. If you need to find an email before acting on it, use the `search_emails_semantic` tool first.
4. When calling a tool that requires a `user_id`, ALWAYS pass the user_id provided in your state context.
5. If the user asks for bulk analytics, counting, or historical trends over thousands of emails, DO NOT search Qdrant. You MUST use the `analyze_historical_data_with_spark` tool to delegate the task to the Big Data cluster.

Be precise, confirm your actions, and provide the draft ID or confirmation details to the user.
"""

def build_agent():
    """Builds the Agentic State Machine."""
    
    llm = get_llm()
    llm_with_tools = llm.bind_tools(all_tools)

    def chatbot_node(state: AgentState):
        """The AI Brain."""
        # Inject the user_id into the system prompt context so the AI knows it
        context_prompt = f"{SYSTEM_PROMPT}\n\nThe current user_id you are acting on behalf of is: {state['user_id']}"
        
        messages = [SystemMessage(content=context_prompt)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState):
        """Routing logic."""
        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", chatbot_node)
    
    # ToolNode automatically executes the tool the AI requested
    workflow.add_node("tools", ToolNode(all_tools)) 

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["tools", END])
    workflow.add_edge("tools", "agent")

    return workflow.compile()