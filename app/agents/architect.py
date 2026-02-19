import os
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY, temperature=0.2)

def fetch_trip_data(trip_id: str):
    """Fetches Trip Details, Places, and Votes from DB"""
    print(f"📥 Fetching data for Trip: {trip_id}...")
    
    # 1. Get Trip Info (Dates, Budget)
    trip = supabase.table("trips").select("*").eq("id", trip_id).execute()
    if not trip.data:
        return None
    trip_data = trip.data[0]

    # 2. Get Places
    places = supabase.table("places").select("*").eq("trip_id", trip_id).execute()
    
    # 3. Get Votes
    votes = supabase.table("votes").select("*").in_("place_id", [p['id'] for p in places.data]).execute()
    
    return {
        "trip": trip_data,
        "places": places.data,
        "votes": votes.data
    }

def generate_itinerary(trip_id: str):
    """The Main Orchestrator Function"""
    
    # --- Step 1: Get Data ---
    data = fetch_trip_data(trip_id)
    if not data:
        return {"error": "Trip not found"}
        
    trip = data['trip']
    places = data['places']
    votes = data['votes']
    
    print(f"📊 Analyzing {len(votes)} votes for {len(places)} places...")

    # --- Step 2: Calculate Scores ---
    # We want to send Gemini ONLY the places people actually liked.
    scored_places = []
    for place in places:
        # Count votes for this place
        place_votes = [v for v in votes if v['place_id'] == place['id']]
        score = sum(1 for v in place_votes if v['vote_value'] > 0) # Simple sum of likes
        
        if score > 0: # Only keep places with at least 1 vote
            scored_places.append({
                "name": place['name'],
                "category": place['category'],
                "score": score,
                "description": place['description'],
                "id": place['id']
            })
    
    # Sort by score (Highest first)
    scored_places.sort(key=lambda x: x['score'], reverse=True)
    
    # --- Step 3: The LLM Prompt ---
    # ... (Keep the top part of generate_itinerary the same) ...

    # --- Step 3: The LLM Prompt (UPDATED FOR STRICT TIMES) ---
    print("🤖 Asking Gemini to build the schedule...")
    
    prompt = f"""
    You are an expert Travel Architect. Create a day-by-day itinerary for a trip to {trip['destination']}.
    
    Constraints:
    - Trip Duration: {trip['start_date']} to {trip['end_date']}.
    - Budget Level: {trip['budget_limit']} USD.
    - The Group Voted for these places:
    {json.dumps(scored_places, indent=2)}
    
    Instructions:
    1. Organize the places into a logical flow.
    2. Add lunch/dinner suggestions.
    3. Return strict JSON format ONLY. Do not use markdown blocks.
    4. TIME FORMAT STRICT RULE: The 'time' field MUST be in 24-hour format like "09:00:00" or "14:30:00". Never use words like "Morning" or "Flexible".
    
    Output JSON Schema:
    [
      {{
        "day": 1,
        "activities": [
          {{ "time": "10:00:00", "activity": "Visit Baga Beach", "notes": "High priority" }},
          {{ "time": "13:00:00", "activity": "Lunch at Britto's", "notes": "Popular spot" }}
        ]
      }}
    ]
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    # Clean output
    content = response.content.replace("```json", "").replace("```", "").strip()
    try:
        itinerary_plan = json.loads(content)
    except:
        print("❌ LLM JSON Error")
        return {"error": "Failed to parse AI output into JSON."}

    # --- Step 4: Save to DB (UPDATED WITH FALLBACK LOGIC) ---
    print("💾 Saving final itinerary to Supabase...")
    
    supabase.table("itinerary_items").delete().eq("trip_id", trip_id).execute()
    
    import re # Make sure to import regex at the top of your file, or just use it here
    
    items_to_save = []
    for day in itinerary_plan:
        for activity in day['activities']:
            
            # Sanitization: Ensure time looks like HH:MM or HH:MM:SS
            raw_time = str(activity.get('time', '09:00:00'))
            # If the LLM hallucinated words, default to 09:00:00
            if not re.match(r"^\d{1,2}:\d{2}", raw_time):
                raw_time = "09:00:00"
                
            items_to_save.append({
                "trip_id": trip_id,
                "day_number": day['day'],
                "start_time": raw_time,
                "end_time": activity.get('end_time', "00:00:00"), 
                "notes": f"{activity.get('activity', 'Activity')} - {activity.get('notes', '')}"
            })
            
    if items_to_save:
        supabase.table("itinerary_items").insert(items_to_save).execute()
        
    print("✅ Itinerary Saved!")
    return itinerary_plan