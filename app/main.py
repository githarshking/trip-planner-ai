import streamlit as st
import pandas as pd
from datetime import date
from agents.architect import generate_itinerary
import uuid
import time
import urllib.parse
import json
import os

# --- PAGE CONFIG MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(page_title="AI Group Trip Planner", page_icon="✈️", layout="centered")

# Import your modules
from database.connection import get_db
from agents.scout import run_scout_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Initialize DB
supabase = get_db()

# --- HELPER: UUID VALIDATOR ---
def is_valid_uuid(val: str) -> bool:
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

# --- DYNAMIC HYPE GENERATOR ---
@st.cache_data(ttl=3600) 
def get_destination_hype(destination):
    """Uses AI to generate a glorifying description and top experiences for the destination."""
    fallback_data = {
        "hype_description": f"Get ready for an unforgettable adventure in {destination}! Prepare for amazing sights, incredible food, and lifelong memories.",
        "experiences": [
            {"title": "Iconic Sights", "description": "Explore the famous landmarks that make this destination globally renowned."},
            {"title": "Local Culture", "description": "Immerse yourself in the unique vibe, traditions, and nightlife."},
            {"title": "Culinary Delights", "description": "Taste the legendary local flavors everyone talks about."}
        ]
    }
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0.7)
        prompt = f"""
        You are a hype-man travel guide. For the destination '{destination}':
        1. Write a 2-sentence exciting, glorifying description to hype up travelers.
        2. List 3 famous, iconic reasons why people visit this place and what they do there.
        Return ONLY valid JSON:
        {{
            "hype_description": "...",
            "experiences": [
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}},
                {{"title": "...", "description": "..."}}
            ]
        }}
        """
        res = llm.invoke([HumanMessage(content=prompt)])
        
        # Robust JSON cleaning
        content = res.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
            
        return json.loads(content)
    except Exception as e:
        print(f"Hype Engine Error: {e}")
        return fallback_data

# --- CSS FOR STYLING ---
st.markdown("""
    <style>
    /* Expand the main container width */
    .block-container {
        max-width: 1000px !important;
    }
    
    /* Standard button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    
    /* Hype text styling */
    .hype-text {
        font-size: 1.25rem;
        font-style: italic;
        color: #FF4B4B;
        margin-bottom: 25px;
        text-align: center;
        padding: 10px;
        background-color: rgba(255, 75, 75, 0.1);
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- BIG RECTANGULAR NAVIGATION BUTTONS ---
# Initialize session state for tracking the current page
if "current_page" not in st.session_state:
    st.session_state.current_page = "Create New Trip"

st.sidebar.title("✈️ Navigation")
st.sidebar.markdown("Select a page below:")

# Creating 3 giant, full-width buttons. The active one turns red (primary).
if st.sidebar.button("🌍 Create New Trip", type="primary" if st.session_state.current_page == "Create New Trip" else "secondary", use_container_width=True):
    st.session_state.current_page = "Create New Trip"
    st.rerun()

if st.sidebar.button("🗳️ Vote on Trip", type="primary" if st.session_state.current_page == "Vote on Trip" else "secondary", use_container_width=True):
    st.session_state.current_page = "Vote on Trip"
    st.rerun()

if st.sidebar.button("📅 View Final Plan", type="primary" if st.session_state.current_page == "View Final Plan" else "secondary", use_container_width=True):
    st.session_state.current_page = "View Final Plan"
    st.rerun()

# Set the page variable so the rest of the script knows what to render
page = st.session_state.current_page

# ==========================================
# PAGE 1: CREATE TRIP (LEADER VIEW)
# ==========================================
if page == "Create New Trip":
    st.title("🌍 Plan a New Group Trip")
    
    if "created_trip_id" in st.session_state:
        st.success("✅ Trip Created & Places Scouted!")
        st.info("📋 **Copy this Trip ID and share it with your group:**")
        st.code(st.session_state["created_trip_id"], language="text")
        st.markdown("They will need this ID to vote on the next tab.")
        
        if st.button("Plan a Different Trip", type="primary"):
            del st.session_state["created_trip_id"]
            st.rerun()
            
    else:
        st.markdown("Use AI to scout the best locations and generate a voting link for your friends.")
        with st.form("create_trip_form"):
            destination = st.text_input("Where do you want to go?", "e.g., Paris, Tokyo, New York").strip()
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", date.today())
            with col2:
                end_date = st.date_input("End Date", date.today())
            
            budget = st.number_input("Budget per person (INR ₹)", min_value=1000, value=15000, step=1000)
            submitted = st.form_submit_button("🚀 Launch AI Scout", type="primary")

        if submitted:
            with st.spinner(f"🤖 AI is scouting top places in {destination}..."):
                try:
                    trip_data = {
                        "destination": destination,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "budget_limit": budget,
                        "status": "VOTING"
                    }
                    response = supabase.table("trips").insert(trip_data).execute()
                    trip_id = response.data[0]['id']

                    # Run Scout
                    run_scout_agent(trip_id, destination)
                    
                    # Update session state
                    st.session_state['created_trip_id'] = trip_id
                    
                    st.success("Trip Curated! Get ready to vote.")
                    st.balloons()    # 🎈 Trigger the balloons!
                    time.sleep(2.5)  # ⏱️ Pause for 2.5 seconds to let the animation play
                    st.rerun()

                except Exception as e:
                    st.error(f"Error creating trip: {e}")

# ==========================================
# PAGE 2: VOTE (MEMBER VIEW)
# ==========================================
elif page == "Vote on Trip":
    
    if "current_trip_id" not in st.session_state:
        st.title("🎟️ Join the Adventure")
        trip_id_input = st.text_input("Paste the Trip ID here:").strip()
        member_name = st.text_input("Your Name:").strip()
        
        if st.button("Enter Voting Booth", type="primary"):
            if not trip_id_input or not member_name:
                st.warning("Please enter both a Trip ID and your name.")
            elif not is_valid_uuid(trip_id_input):
                st.error("Invalid Trip ID format. Please make sure you copied the exact code.")
            else:
                try:
                    trip_check = supabase.table("trips").select("*").eq("id", trip_id_input).execute()
                    if not trip_check.data:
                        st.error("Trip ID not found in the database!")
                    else:
                        member_data = {"trip_id": trip_id_input, "name": member_name}
                        member_res = supabase.table("members").insert(member_data).execute()
                        
                        st.session_state["current_trip_id"] = trip_id_input
                        st.session_state["current_member_id"] = member_res.data[0]['id']
                        st.session_state["member_name"] = member_name
                        st.session_state["destination"] = trip_check.data[0]['destination'] 
                        st.rerun()
                except Exception as e:
                    st.error(f"Error joining: {e}")

    else:
        trip_id = st.session_state["current_trip_id"]
        dest = st.session_state.get("destination", "this destination")
        
        st.markdown(f"<h1 style='text-align: center;'>🌟 Welcome to {dest.upper()}!</h1>", unsafe_allow_html=True)
        
        with st.spinner(f"Loading the vibe for {dest}..."):
            hype_data = get_destination_hype(dest)
            
        st.markdown(f"<div class='hype-text'>\"{hype_data.get('hype_description', '')}\"</div>", unsafe_allow_html=True)
        
        st.subheader("💡 Why People Love It Here")
        for exp in hype_data.get('experiences', []):
            st.info(f"**{exp.get('title', 'Experience')}**\n\n{exp.get('description', '')}")
            
        st.divider()

        # User Switcher
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.write(f"Alright **{st.session_state.get('member_name', 'Traveler')}**, time to cast your votes!")
        with col_btn:
            if st.button("🔄 Switch User"):
                for key in ["current_trip_id", "current_member_id", "member_name", "destination"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # Fetch Data
        try:
            members_res = supabase.table("members").select("*").eq("trip_id", trip_id).execute()
            member_map = {m['id']: m['name'] for m in members_res.data}
            
            places_res = supabase.table("places").select("*").eq("trip_id", trip_id).execute()
            places = places_res.data
            
            # Global Voter Tracker
            voted_members = set()
            if places:
                place_ids = [p['id'] for p in places]
                votes_res = supabase.table("votes").select("member_id").in_("place_id", place_ids).execute()
                for v in votes_res.data:
                    voted_members.add(v['member_id'])
                    
            voter_names = [member_map.get(m_id, "Unknown") for m_id in voted_members]
            
            if not places:
                st.warning("No places found. Ask the leader to run the Scout again!")
            else:
                with st.form("voting_form"):
                    st.subheader("📍 Choose Your Must-Do Activities")
                    
                    if voter_names:
                        st.info(f"👥 **{len(voter_names)} people have cast their votes so far:** {', '.join(voter_names)}")
                    else:
                        st.info("👥 **No one has voted yet. Be the first!**")
                    
                    st.write("---")
                    selected_places = []
                    
                    for place in places:
                        cost_val = place.get('estimated_cost', 1)
                        cost_display = "Free / Very Cheap" if cost_val == 0 else '₹' * cost_val
                        
                        rating_val = place.get('rating', 0.0)
                        rating_display = f"⭐ {rating_val} / 5.0" if rating_val > 0 else "⭐ Rating N/A"
                        
                        search_query = urllib.parse.quote_plus(f"{place.get('name', '')} {dest}")
                        google_link = f"https://www.google.com/search?q={search_query}"
                        
                        with st.container(border=True):
                            st.markdown(f"### {place.get('name', 'Unknown')}  <span style='font-size: 16px; font-weight: normal; color: gray;'>({place.get('category', 'Activity')})</span>", unsafe_allow_html=True)
                            st.write(place.get('description', ''))
                            st.caption(f"**💰 {cost_display} | {rating_display}** &nbsp;&nbsp;•&nbsp;&nbsp; [🔍 See photos & details on Google]({google_link})")
                            
                            if st.checkbox("✅ Add to my wishlist", key=place['id']):
                                selected_places.append(place['id'])

                    st.write("---")
                    st.subheader("✨ What's your overarching vibe?")
                    vibe = st.select_slider("Select your travel style", options=["Extremely Chill", "Balanced", "Non-stop Adventure"])
                    comment = st.text_area("Any specific requests? (e.g., 'No seafood', 'I want to hike')")

                    if st.form_submit_button("Submit My Votes", type="primary"):
                        vote_inserts = []
                        for pid in selected_places:
                            vote_inserts.append({
                                "place_id": pid,
                                "member_id": st.session_state["current_member_id"],
                                "vote_value": 1, 
                                "comment": comment
                            })
                        
                        if vote_inserts:
                            try:
                                supabase.table("votes").upsert(vote_inserts).execute()
                                st.success("🎉 Votes locked in! Click 'Switch User' above if someone else needs to vote.")
                            except Exception as e:
                                st.error(f"Error saving votes: {e}")
                        else:
                            st.warning("You didn't select any places! Don't be boring, pick something!")
        except Exception as e:
            st.error(f"Database error while loading voting page: {e}")

# ==========================================
# PAGE 3: VIEW FINAL PLAN (THE ARCHITECT)
# ==========================================
elif page == "View Final Plan":
    st.title("📅 Your Perfect Itinerary")
    
    trip_id_input = st.text_input("Enter Trip ID to see the plan:").strip()
    
    if st.button("Generate / View Plan", type="primary"):
        if not trip_id_input:
            st.warning("Please enter a Trip ID.")
        elif not is_valid_uuid(trip_id_input):
            st.error("Invalid Trip ID format.")
        else:
            with st.spinner("🧠 The Architect is resolving conflicts and building the schedule..."):
                try:
                    trip_check = supabase.table("trips").select("destination").eq("id", trip_id_input).execute()
                    dest = trip_check.data[0]['destination'] if trip_check.data else ""
                except Exception:
                    dest = ""

                # Run the Architect Agent
                architect_data = generate_itinerary(trip_id_input)
                
                if "error" in architect_data:
                    st.error(architect_data["error"])
                else:
                    st.success("✨ Itinerary Generated!")
                    st.balloons()  # 🎈 Celebrate the final itinerary!
                    time.sleep(1.5)  # ⏱️ Pause to let the animation play
                    
                    # --- DYNAMIC HOTEL COLUMNS ---
                    st.markdown("### 🏨 Your Accommodation Options")
                    st.caption("We crunched your daily budget. Here are the best places to stay:")
                    
                    hotels = architect_data.get('hotels', [])
                    if hotels:
                        # Create exactly as many columns as there are hotels (max 3)
                        num_cols = min(len(hotels), 3)
                        cols = st.columns(num_cols)
                        
                        for i, hotel in enumerate(hotels[:3]):
                            with cols[i]:
                                price_val = int(hotel.get('price', 0))
                                type_val = hotel.get('type', 'Hotel')
                                name_val = hotel.get('name', 'Unknown Location')
                                st.info(f"**{name_val}**\n\nType: {type_val}\n\nPrice: ₹{price_val}/night")
                    else:
                        st.info("No hotel options found for this criteria.")
                            
                    st.divider()
                    
                    # --- DISPLAY THE TIMELINE ---
                    for day in architect_data.get('plan', []):
                        st.subheader(f"Day {day.get('day', 1)}")
                        for activity in day.get('activities', []):
                            
                            clean_name = activity.get('activity', 'Activity').replace("Visit ", "").replace("Lunch at ", "").replace("Dinner at ", "")
                            search_query = urllib.parse.quote_plus(f"{clean_name} {dest}")
                            google_link = f"https://www.google.com/search?q={search_query}"
                            
                            st.markdown(f"**{activity.get('time', '00:00')}** — <a href='{google_link}' target='_blank' style='text-decoration: none; color: #FF4B4B; font-weight: bold;'>{activity.get('activity', 'Activity')} 🔍</a>", unsafe_allow_html=True)
                            
                            if activity.get('notes'):
                                st.caption(f"_{activity['notes']}_")
                                
                        st.divider()
                    
                    # --- GOOGLE MAPS LINK ---
                    st.markdown("### 🗺️ Master Navigation")
                    st.markdown("We provide you with the most optimized route for traveling and saves time.")
                    
                    map_url = architect_data.get('map_url')
                    if map_url:
                        st.link_button("📍 Open Full Optimized Route in Google Maps", map_url, type="primary")
                    else:
                        st.warning("Not enough map data to generate a route.")