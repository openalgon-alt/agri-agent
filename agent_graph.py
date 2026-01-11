import json
import operator
from typing import Annotated, Sequence, TypedDict, Literal, Union

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import create_react_agent

from tools import librarian_tools, analyst_tools

# --- CONFIGURATION ---
# --- CONFIGURATION ---
import os

# --- CONFIGURATION ---
MODEL_NAME = "qwen3-vl" # Standard Int4 version for speed/VRAM
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Increase context to Avoid VRAM overflow but allow RAG
llm = ChatOllama(model=MODEL_NAME, temperature=0, num_ctx=2048, base_url=OLLAMA_URL) 
worker_llm = ChatOllama(model=MODEL_NAME, temperature=0, num_ctx=2048, base_url=OLLAMA_URL)

# --- STATE ---
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    thought: str

# --- WORKERS ---
librarian_agent = create_react_agent(worker_llm, librarian_tools)

def librarian_node(state):
    result = librarian_agent.invoke(state)
    last_msg = result["messages"][-1]
    return {"messages": [HumanMessage(content=f"LIBRARIAN REPORT: {last_msg.content}", name="Librarian")]}

analyst_agent = create_react_agent(worker_llm, analyst_tools)

def analyst_node(state):
    result = analyst_agent.invoke(state)
    last_msg = result["messages"][-1]
    return {"messages": [HumanMessage(content=f"ANALYST REPORT: {last_msg.content}", name="Analyst")]}

# --- SUPERVISOR ---
supervisor_system_prompt = """You are the Manager.
Team:
1. Librarian: Local RAG (PDFs) and Web Search.
2. Analyst: Weather and Market Prices.

Goal: Route the query or Answer.
ALWAYS Output JSON:
{{
    "thought": "Reasoning (Explain WHY you chose this step)",
    "next": "Librarian" OR "Analyst" OR "FINISH",
    "final_answer": "Final response (if FINISH)"
}}
"""

def parse_output(content: str):
    """Clean and parse JSON from LLM output."""
    content = content.strip()
    # Remove markdown code blocks if present
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: Assume the model just spoke the answer
        return {"next": "FINISH", "final_answer": content}

def supervisor_node(state):
    messages = state["messages"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", supervisor_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({"messages": messages})
        
        # Robust Parsing
        decision = parse_output(response.content)
        
        target = decision.get("next", "FINISH")
        thought = decision.get("thought", "Determining next step...")
        
        if target == "FINISH":
            final_ans = decision.get("final_answer", response.content)
            return {"next": "FINISH", "thought": thought, "messages": [AIMessage(content=final_ans)]}
        else:
            return {"next": target, "thought": thought}
            
    except Exception as e:
        print(f"Supervisor Error: {e}")
        return {"next": "FINISH", "messages": [AIMessage(content=f"Error: {str(e)}")]}

# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Librarian", librarian_node)
workflow.add_node("Analyst", analyst_node)

# Entry point
workflow.add_edge(START, "Supervisor")

# Conditional edges from Supervisor
workflow.add_conditional_edges(
    "Supervisor",
    lambda x: x["next"],
    {
        "Librarian": "Librarian",
        "Analyst": "Analyst",
        "FINISH": END
    }
)

# Workers always report back to Supervisor
workflow.add_edge("Librarian", "Supervisor")
workflow.add_edge("Analyst", "Supervisor")

graph = workflow.compile()
