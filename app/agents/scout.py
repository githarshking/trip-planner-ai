import os
import json
from typing import List, TypedDict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from tavily import TavilyClient
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0)

# --- State Definition ---
class ScoutState(TypedDict):
    trip_id: str
    location: str
    raw_results: List[dict]
    curated_places: List[dict]

# --- Node 1: The Researcher (Tavily) ---
def search_places(state: ScoutState) -> ScoutState:
    print(f"🔎 Searching for top places in {state['location']}...")
    
    # We run 2 searches to get variety: "Top attractions" and "Hidden gems"
    try:
        query1 = f"top tourist attractions in {state['location']} with ticket price"
        query2 = f"best restaurants and hidden gems in {state['location']} for young people"
        
        # Run searches
        response1 = tavily.search(query=query1, search_depth="advanced", max_results=5)
        response2 = tavily.search(query=query2, search_depth="advanced", max_results=5)
        
        combined_results = response1.get('results', []) + response2.get('results', [])
        
        # --- FIX: Update state instead of replacing it ---
        state['raw_results'] = combined_results
        return state
        
    except Exception as e:
        print(f"❌ Error in Search: {e}")
        state['raw_results'] = []
        return state

# --- Node 2: The Curator (Gemini) ---
# app/agents/scout.py

# ... keep imports and search_places function as is ...

# --- REPLACE ONLY THIS FUNCTION ---
def curate_places(state: ScoutState) -> ScoutState:
    print("🧠 Curating and cleaning list with Gemini...")
    
    if not state['raw_results']:
        print("⚠️ No raw results to curate.")
        state['curated_places'] = []
        return state

    # Limit data size to avoid token limits
    raw_data_str = json.dumps(state['raw_results'][:10]) 
    
    prompt = f"""
    You are an expert Travel Scout. I will give you a list of raw search results for a trip to {state['location']}.
    
    Your Goal: Create a clean list of 10 unique, high-quality places.
    
    Rules:
    1. Remove duplicates.
    2. Categorize them exactly as: 'Attraction', 'Restaurant', 'Activity', or 'Relaxation'.
    3. Estimate cost (0 = Free, 1 = Cheap, 2 = Expensive, 3 = Luxury).
    4. Provide a short, exciting description (1 sentence).
    5. Return ONLY valid JSON. Do not write markdown.
    
    Raw Data:
    {raw_data_str}
    
    Output Format (List of Objects):
    [
        {{
            "name": "Place Name",
            "description": "Short description...",
            "category": "Attraction",
            "estimated_cost": 1,
            "rating": 4.5
        }}
    ]
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        
        # Simple cleaning of code blocks if Gemini adds them
        content = response.content.replace("```json", "").replace("```", "").strip()
        curated_list = json.loads(content)
        
        # --- FIX: Update state ---
        state['curated_places'] = curated_list
        return state
        
    except Exception as e:
        print(f"❌ Error in Curation: {e}")
        state['curated_places'] = []
        return state
# --- Node 3: The Database Saver (Supabase) ---
def save_to_db(state: ScoutState) -> ScoutState:
    print("💾 Saving places to Supabase...")
    
    if not state['curated_places']:
        print("⚠️ No places to save.")
        return state

    places_to_insert = []
    for place in state['curated_places']:
        places_to_insert.append({
            "trip_id": state['trip_id'],
            "name": place['name'],
            "description": place.get('description', ''),
            "category": place.get('category', 'Activity'),
            "estimated_cost": place.get('estimated_cost', 1),
            "rating": place.get('rating', 0.0),
            "metadata": {} 
        })
        
    try:
        # Batch insert into Supabase
        data = supabase.table("places").insert(places_to_insert).execute()
        print(f"✅ Successfully saved {len(places_to_insert)} places to Supabase!")
    except Exception as e:
        print(f"❌ Database Error: {e}")
        
    return state

# --- Main Execution Function ---
def run_scout_agent(trip_id: str, location: str):
    # Initialize State
    state = {
        "trip_id": trip_id, 
        "location": location, 
        "raw_results": [], 
        "curated_places": []
    }
    
    # Execute Linear Chain
    state = search_places(state)
    state = curate_places(state)
    state = save_to_db(state)
    
    return state