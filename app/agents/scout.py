import os
import json
import re
from typing import List, TypedDict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from tavily import TavilyClient
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

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
# Slightly higher temperature (0.2) allows Gemini to tap into its own knowledge if web search is thin
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.2)

# --- State Definition ---
class ScoutState(TypedDict):
    trip_id: str
    location: str
    raw_results: List[dict]
    curated_places: List[dict]

# --- Node 1: The Researcher (Tavily) ---
def search_places(state: ScoutState) -> ScoutState:
    print(f"🔎 Searching for top places in {state['location']}...")
    
    combined_results = []
    
    # FIX: Run searches individually so if one fails, the other still works.
    # FIX: Increased max_results to 20 to ensure Gemini has enough raw data to choose from.
    try:
        query1 = f"top tourist attractions and landmarks in {state['location']} with ticket price"
        response1 = tavily.search(query=query1, search_depth="advanced", max_results=20)
        combined_results.extend(response1.get('results', []))
    except Exception as e:
        print(f"⚠️ Tavily Search 1 Error: {e}")

    try:
        query2 = f"best highly-rated restaurants, cafes, and hidden gems in {state['location']}"
        response2 = tavily.search(query=query2, search_depth="advanced", max_results=20)
        combined_results.extend(response2.get('results', []))
    except Exception as e:
        print(f"⚠️ Tavily Search 2 Error: {e}")
        
    state['raw_results'] = combined_results
    return state

# --- Node 2: The Curator (Gemini) ---
def curate_places(state: ScoutState) -> ScoutState:
    print("🧠 Curating and cleaning list with dynamic Gemini math...")
    
    # --- 1. Fetch Trip Details for Dynamic Math ---
    try:
        trip_res = supabase.table("trips").select("*").eq("id", state['trip_id']).execute()
        trip = trip_res.data[0]
        
        start_dt = datetime.strptime(trip['start_date'], '%Y-%m-%d')
        end_dt = datetime.strptime(trip['end_date'], '%Y-%m-%d')
        days_count = max(1, (end_dt - start_dt).days + 1)
        total_budget = trip['budget_limit']
        
    except Exception as e:
        print(f"⚠️ Error fetching trip dates, using defaults: {e}")
        days_count = 1
        total_budget = 15000
        
    # --- 2. Calculate the Constraints ---
    target_places = 10 + (3 * (days_count - 1))
    max_restaurants = 2 * days_count
    daily_budget = int(total_budget / days_count)

    print(f"📊 Trip Math: {days_count} Days | {target_places} Places Needed | Max {max_restaurants} Restaurants | ₹{daily_budget}/day")

    # --- 3. The ENHANCED Dynamic Prompt ---
    # Give it up to 40 results to pick from
    raw_data_str = json.dumps(state.get('raw_results', [])[:40]) 
    
    prompt = f"""
    You are an elite Travel Scout. I am providing you with raw web search results for {state['location']}.
    
    TRIP CONSTRAINTS:
    - Trip Duration: {days_count} days
    - Daily Budget per person: ₹{daily_budget} INR
    
    YOUR GOAL: 
    Create a highly curated list of EXACTLY {target_places} unique, top-tier places for the group to vote on.
    
    STRICT RULES:
    1. CATEGORIES: Categorize EVERY place strictly as: 'Attraction', 'Restaurant', 'Activity', or 'Relaxation'.
    2. RESTAURANT LIMIT: You MUST NOT include more than {max_restaurants} places categorized as 'Restaurant'. 
    3. BUDGET MATCH: Filter places to fit within the ₹{daily_budget} daily budget. (0 = Free, 1 = Cheap, 2 = Expensive, 3 = Luxury).
    4. DESCRIPTIONS: Provide a punchy, exciting 1-sentence description that makes people want to go there.
    5. REAL RATINGS: You MUST extract the real Google/TripAdvisor rating (e.g., 4.2, 4.8) from the raw data. If missing, use your expert knowledge to estimate the real-world rating. DO NOT use generic placeholders like 4.5.
    6. FALLBACK KNOWLEDGE: If the raw data does not contain exactly {target_places} good places, you MUST use your own internal knowledge to suggest highly-rated places in {state['location']} to hit the exact target number.
    7. FORMAT: Return ONLY a valid JSON array. No markdown, no explanations.
    
    Raw Data:
    {raw_data_str}
    
    Output Format Example:
    [
        {{
            "name": "Central Park",
            "description": "A sprawling green oasis perfect for a leisurely afternoon stroll.",
            "category": "Relaxation",
            "estimated_cost": 0,
            "rating": 4.8
        }}
    ]
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        
        # FIX: Bulletproof JSON parsing using Regex
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            content = match.group(0)
            
        curated_list = json.loads(content)
        state['curated_places'] = curated_list
        return state
        
    except Exception as e:
        print(f"❌ Error in Curation/JSON Parsing: {e}")
        state['curated_places'] = []
        return state

# --- Node 3: The Database Saver (Supabase) ---
def save_to_db(state: ScoutState) -> ScoutState:
    print("💾 Saving places to Supabase...")
    
    if not state.get('curated_places'):
        print("⚠️ No places to save.")
        return state

    places_to_insert = []
    for place in state['curated_places']:
        
        # FIX: Coerce data types safely so Supabase doesn't crash
        try:
            rating_val = float(place.get('rating', 4.5))
        except (ValueError, TypeError):
            rating_val = 4.5
            
        try:
            cost_val = int(place.get('estimated_cost', 1))
        except (ValueError, TypeError):
            cost_val = 1

        places_to_insert.append({
            "trip_id": state['trip_id'],
            "name": str(place.get('name', 'Unknown Place')),
            "description": str(place.get('description', '')),
            "category": str(place.get('category', 'Activity')),
            "estimated_cost": cost_val,
            "rating": rating_val,
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
    state: ScoutState = {
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