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
from utils.transport import get_transit_instruction

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

    # --- Step 2: Calculate Scores ---
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

    # Our updated routing function now returns a list of dictionaries with distances
    optimized_route_data = optimize_daily_route(place_names, trip['destination'])

    print("🏨 Running Accommodation Engine...")
    # Calculate how many days the trip is to find the daily budget
    start_dt = datetime.strptime(trip['start_date'], '%Y-%m-%d')
    end_dt = datetime.strptime(trip['end_date'], '%Y-%m-%d')
    days_count = max(1, (end_dt - start_dt).days + 1)
    
    # Allocate the per-person budget purely to daily hotel costs for this test
    daily_budget = int(trip['budget_limit'] / days_count)
    
    # We pass 0.0 for lat/lon so our Amadeus fallback logic naturally triggers for Indian cities
    hotel_options = search_hotels(lat=0.0, lon=0.0, daily_budget=daily_budget)

    # --- NEW: Generate Transit Instructions ---
    transit_log = []
    ordered_names = []
    for i, route_node in enumerate(optimized_route_data):
        ordered_names.append(route_node['name'])

        # If there is a next stop, calculate how to get there
        if route_node['distance_to_next'] > 0 and i < len(optimized_route_data) - 1:
            next_name = optimized_route_data[i+1]['name']
            instruction = get_transit_instruction(route_node['distance_to_next'], daily_budget)

            # Save this exact string to feed to the LLM
            transit_log.append(f"To get from '{route_node['name']}' to '{next_name}': {instruction}")

    # --- Step 3: The LLM Prompt ---
    print("🤖 Asking Gemini to build the schedule...")

    prompt = f"""
    You are an expert Travel Architect. Create a day-by-day itinerary for a trip to {trip['destination']}.

    Constraints:
    - Trip Duration: {trip['start_date']} to {trip['end_date']}.
    - Budget Level: {trip['budget_limit']} INR.
    - Top Hotel Options: {json.dumps([h['name'] for h in hotel_options])}

    CRITICAL SEQUENCE & TRANSIT INSTRUCTIONS:
    You MUST schedule the places in EXACTLY this sequence to prevent zigzagging:
    {json.dumps(ordered_names, indent=2)}

    Here is exactly how the user will travel between these stops. You MUST include these transit instructions as their own separate "activity" blocks between the locations.
    {json.dumps(transit_log, indent=2)}

    Instructions:
    1. Group the places day-by-day.
    2. Add lunch/dinner suggestions.
    3. Include Transit steps (e.g., "Take an Auto Rickshaw") as separate activities.
    4. Return strict JSON format ONLY. Do not use markdown blocks.
    5. TIME FORMAT STRICT RULE: The 'time' field MUST be in 24-hour format like "09:00:00". Never use words.

    Output JSON Schema:
    [
      {{
        "day": 1,
        "activities": [
          {{ "time": "10:00:00", "activity": "Visit [Place 1]", "notes": "Explore the history" }},
          {{ "time": "12:00:00", "activity": "Transit to [Place 2]", "notes": "🛺 Auto Rickshaw (3.5 km) - Est. ₹50" }},
          {{ "time": "12:30:00", "activity": "Visit [Place 2]", "notes": "Enjoy the views" }}
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
    
    # Generate the master Google Maps URL using the cleanly ordered names
    map_url = generate_google_maps_url(ordered_names, trip['destination'])
    
    # Return a rich dictionary instead of just the plan
    return {
        "plan": itinerary_plan,
        "map_url": map_url,
        "hotels": hotel_options
    }