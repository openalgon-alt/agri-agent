import os
import requests
import json
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
from rag_engine import RAGEngine

# Initialize RAG Engine globally for the tool
rag_engine = RAGEngine()
# Ensure DB is loaded (lazy load, but we need it ready for the tool)
if not rag_engine.vector_db:
    # Try to load existing without rebuilding
    if os.path.exists(rag_engine.db_dir) and os.listdir(rag_engine.db_dir):
        from langchain_chroma import Chroma
        rag_engine.vector_db = Chroma(persist_directory=rag_engine.db_dir, embedding_function=rag_engine.embeddings)

# --- LIBRARIAN AGENT TOOLS ---

@tool
def library_search(query: str):
    """
    Primary Search Tool. Use this to find information in the local PDF archives 
    and agricultural magazine database (AgriCatalogues 2025).
    Always use this BEFORE searching the web.
    """
    if not rag_engine.vector_db:
        return "The library is closed (Vector DB not initialized). Please check Admin Dashboard."
    
    # 1. Handle "List All" Intent
    q_lower = query.lower()
    if "list" in q_lower and ("all" in q_lower or "article" in q_lower or "pdf" in q_lower):
        all_docs = rag_engine.list_documents()
        if not all_docs:
            return "The library is empty."
        
        # Determine strictness: if just "list all", return everything. 
        # But to be safe for Context Window, limiting to 50 titles or using a summarized format.
        response = "**Master Catalog of Articles:**\n\n"
        for idx, doc in enumerate(all_docs):
            title = doc.get('title', 'Unknown Title')
            authors = ", ".join(doc.get('authors', ['Unknown']))
            response += f"{idx+1}. **{title}** by {authors}\n"
        return response

    # 2. Semantic Search (Increased k=5 for better recall)
    docs = rag_engine.search(query, k=5)
    if not docs:
        return "No relevant documents found in the local archives."
    
    return "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])

@tool
def web_search(query: str):
    """
    Fallback Search Tool. Use this ONLY if 'library_search' yields no results 
    or for general internet knowledge.
    """
    search = DuckDuckGoSearchRun()
    return search.invoke(query)

# --- ANALYST AGENT TOOLS ---

@tool
def fetch_weather(location: str):
    """
    Fetches the current weather and 3-day forecast for a specific location.
    Usage: fetch_weather("Hyderabad")
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY", "DEMO_KEY") # Use env var or demo
    
    # Mocking for now as we don't have a real key in the environment yet.
    # In production, replace with:
    # url = f"http://api.openweathermap.org/data/2.5/forecast?q={location}&appid={api_key}&units=metric"
    # response = requests.get(url)
    
    # Return simulated Real-Time Data (since we are in dev mode without user API key)
    return json.dumps({
        "location": location,
        "current": {"temp": "28C", "condition": "Sunny", "humidity": "45%"},
        "forecast": [
            {"day": "Tomorrow", "temp": "29C", "condition": "Cloudy"},
            {"day": "Day+2", "temp": "30C", "condition": "Rain"},
            {"day": "Day+3", "temp": "27C", "condition": "Storm"}
        ]
    })

@tool
def fetch_market_prices(commodity: str, market: str = "All"):
    """
    Fetches current market prices (Mandi Prices) for a commodity from Agmarknet.
    Usage: fetch_market_prices("Tomato", "Kothapet")
    """
    # Mocking Agmarknet data
    return json.dumps([
        {"market": "Kothapet", "commodity": commodity, "min_price": 1200, "max_price": 1500, "modal_price": 1350, "date": "2025-01-08"},
        {"market": "Bowenpally", "commodity": commodity, "min_price": 1100, "max_price": 1400, "modal_price": 1250, "date": "2025-01-08"},
        {"market": "Gudimalkapur", "commodity": commodity, "min_price": 1300, "max_price": 1600, "modal_price": 1450, "date": "2025-01-08"}
    ])

# Export list for LangGraph
librarian_tools = [library_search, web_search]
analyst_tools = [fetch_weather, fetch_market_prices]
