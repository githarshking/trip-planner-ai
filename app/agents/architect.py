import os
import json
import re
from datetime import datetime 
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from supabase import create_client
from dotenv import load_dotenv

from utils.routing import optimize_daily_route
from utils.accommodations import search_hotels
from utils.maps import generate_google_maps_url 

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

    # --- Step 2: Calculate Scores (THIS WAS MISSING!) ---
    scored_places = []
    for place in places:
        place_votes = [v for v in votes if v['place_id'] == place['id']]
        score = sum(1 for v in place_votes if v['vote_value'] > 0)
        
        if score > 0:
            scored_places.append({
                "name": place['name'],
                "category": place['category'],
                "score": score,
                "description": place['description'],
                "id": place['id']
            })
            
    # Sort by score initially to drop the lowest ones
    scored_places.sort(key=lambda x: x['score'], reverse=True)
    top_places = scored_places[:6]
    
    # --- Step 2.5: The Math & Logistics Engine ---
    print("🗺️ Running the OSRM Routing Engine...")
    place_names = [p['name'] for p in top_places]
    optimized_names_order = optimize_daily_route(place_names, trip['destination'])
    
    ordered_places = []
    for name in optimized_names_order:
        for p in top_places:
            if p['name'] == name:
                ordered_places.append(p)
                break

    print("🏨 Running Accommodation Engine...")
    # Calculate how many days the trip is to find the daily budget
    start_dt = datetime.strptime(trip['start_date'], '%Y-%m-%d')
    end_dt = datetime.strptime(trip['end_date'], '%Y-%m-%d')
    days_count = max(1, (end_dt - start_dt).days + 1)
    
    # Allocate the per-person budget purely to daily hotel costs for this test
    daily_budget = int(trip['budget_limit'] / days_count)
    
    # We pass 0.0 for lat/lon so our Amadeus fallback logic naturally triggers for Indian cities
    hotel_options = search_hotels(lat=0.0, lon=0.0, daily_budget=daily_budget)

    # --- Step 3: The LLM Prompt ---
    print("🤖 Asking Gemini to build the schedule...")
    
    prompt = f"""
    You are an expert Travel Architect. Create a day-by-day itinerary for a trip to {trip['destination']}.
    
    Constraints:
    - Trip Duration: {trip['start_date']} to {trip['end_date']}.
    - Budget Level: {trip['budget_limit']} INR.
    - Here are 3 Hotel/Accommodation options that fit their budget:
    {json.dumps(hotel_options, indent=2)}
    
    CRITICAL INSTRUCTION:
    I have already calculated the geographically perfect route for these places. 
    You MUST schedule them in EXACTLY this sequence to prevent zigzagging across the map:
    {json.dumps([p['name'] for p in ordered_places], indent=2)}
    
    Instructions:
    1. Group the places day-by-day following the exact sequence above.
    2. Add lunch/dinner suggestions.
    3. Include the best Hotel Option as a "Check-in" activity on Day 1.
    4. Return strict JSON format ONLY. Do not use markdown blocks.
    5. TIME FORMAT STRICT RULE: The 'time' field MUST be in 24-hour format like "09:00:00". Never use words.
    
    Output JSON Schema:
    [
      {{
        "day": 1,
        "activities": [
          {{ "time": "10:00:00", "activity": "Visit [Place 1 from sequence]", "notes": "High priority" }}
        ]
      }}
    ]
    """
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.replace("```json", "").replace("```", "").strip()
    
    try:
        itinerary_plan = json.loads(content)
    except:
        print("❌ LLM JSON Error")
        return {"error": "Failed to parse AI output into JSON."}

    # --- Step 4: Save to DB and Generate URLs ---
    print("💾 Saving final itinerary to Supabase...")
    supabase.table("itinerary_items").delete().eq("trip_id", trip_id).execute()
    
    items_to_save = []
    for day in itinerary_plan:
        for activity in day['activities']:
            raw_time = str(activity.get('time', '09:00:00'))
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
    
    # Generate the master Google Maps URL
    map_url = generate_google_maps_url(optimized_names_order, trip['destination'])
    
    # Return a rich dictionary instead of just the plan
    return {
        "plan": itinerary_plan,
        "map_url": map_url,
        "hotels": hotel_options
    }