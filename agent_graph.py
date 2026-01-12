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
MODEL_NAME = "qwen3-vl" # Standard Int4 version for speed/VRAM
# Increase context to Avoid VRAM overflow but allow RAG
llm = ChatOllama(model=MODEL_NAME, temperature=0, num_ctx=32768) 
worker_llm = ChatOllama(model=MODEL_NAME, temperature=0, num_ctx=32768)

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
    "thought": "Reasoning",
    "next": "Librarian" OR "Analyst" OR "FINISH",
    "final_answer": "Final response (if FINISH)"
}}

CRITICAL RULES:
1. If a worker (Librarian/Analyst) asks a clarifying question (like "Which city?"), YOU MUST CHOOSE "FINISH" and ask the user. DO NOT send it back to the worker.
2. If the worker cannot find the answer, CHOOSE "FINISH" and report the negative result.
3. IF LIBRARIAN RETURNS A LIST OF ARTICLES: Do NOT summarize it. Do NOT say "found one article". Copy the list EXACTLY as provided by the Librarian into your final_answer. TRUST THE WORKER REPORT.
"""

def parse_output(content: str):
    """Clean and parse JSON from LLM output, handling <think> tags."""
    import re
    content = content.strip()
    
    # Extract <think> content
    thought_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
    extracted_thought = ""
    if thought_match:
        extracted_thought = thought_match.group(1).strip()
        # Remove the <think> block from content
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        
    # Remove markdown code blocks if present
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1]
            if content.startswith("json"):
                content = content[4:]
    content = content.strip()
    
    try:
        parsed = json.loads(content)
        # Append extracted thought to the JSON's 'thought' field if it exists
        if extracted_thought:
            existing_thought = parsed.get("thought", "")
            if existing_thought:
                parsed["thought"] = f"{extracted_thought}\n\n{existing_thought}"
            else:
                parsed["thought"] = extracted_thought
        return parsed
        
    except json.JSONDecodeError:
        # Fallback: Assume the model just spoke the answer
        # If we extracted thoughts, we return them too, although the interface might only use 'thought' in JSON flow.
        # But here we are returning a dict for the graph.
        result = {"next": "FINISH", "final_answer": content}
        if extracted_thought:
            result["thought"] = extracted_thought
        return result

def supervisor_node(state):
    print("DEBUG: Entering supervisor_node")
    messages = state["messages"]

    # --- DIRECT OUTPUT OPTIMIZATION ---
    # If the last message is from the Librarian, we assume it's the answer.
    # We skip the Supervisor LLM (which might summarize/hallucinate) and return the raw report.
    last_msg = messages[-1]
    print(f"DEBUG: Last Message Type: {type(last_msg)}")
    print(f"DEBUG: Last Message Content: {last_msg.content[:50]}...")
    if hasattr(last_msg, 'name'):
        print(f"DEBUG: Last Message Name: {last_msg.name}")
    
    if isinstance(last_msg, HumanMessage) and getattr(last_msg, 'name', '') == "Librarian":
        print("DEBUG: Fast-tracking Librarian Report to Output")
        # Strip the "LIBRARIAN REPORT: " prefix if preferred, or keep it for context.
        # We will keep it clean.
        clean_content = last_msg.content.replace("LIBRARIAN REPORT: ", "", 1)
        return {
            "next": "FINISH", 
            "thought": "Librarian provided search results. Returning directly to user.", 
            "messages": [AIMessage(content=clean_content)]
        }
    # ----------------------------------
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", supervisor_system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    chain = prompt | llm
    
    try:
        print("DEBUG: Invoking Supervisor LLM...", flush=True)
        response = chain.invoke({"messages": messages})
        try:
            print(f"DEBUG: Supervisor LLM Response: {response.content[:100]}...", flush=True)
        except:
             print("DEBUG: Supervisor LLM Response: [Encoding Error in Print]", flush=True)
        
        # Robust Parsing
        decision = parse_output(response.content)
        try:
             print(f"DEBUG: Parsed Decision: {decision}", flush=True)
        except:
             pass
        
        target = decision.get("next", "FINISH").upper() # Handle case sensitivity
        thought = decision.get("thought", "Determining next step...")
        
        # Validate target
        if target not in ["LIBRARIAN", "ANALYST", "FINISH"]:
             # If model hallucinates a step, default to FINISH to avoid Graph Error
             target = "FINISH"

        if target == "FINISH":
            final_ans = decision.get("final_answer", response.content)
            return {"next": "FINISH", "thought": thought, "messages": [AIMessage(content=final_ans)]}
        else:
            # Map UPPERCASE back to Capitalized for consistency with Node Names if needed
            # But our Node names are Capitalized. "Librarian", "Analyst".
            # FIX: Our node names are Title Case. "Librarian", "Analyst".
            # So we should map "LIBRARIAN" -> "Librarian".
            camel_target = target.capitalize() 
            return {"next": camel_target, "thought": thought}
            
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
