import streamlit as st
import pandas as pd
from datetime import date
from agents.architect import generate_itinerary
import uuid
import time
import urllib.parse
import json
import os

# Import your modules
from database.connection import get_db
from agents.scout import run_scout_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Initialize DB
supabase = get_db()

# --- NEW: DYNAMIC HYPE GENERATOR ---
@st.cache_data(ttl=3600) # Cache this so it doesn't run every time someone clicks a button
def get_destination_hype(destination):
    """Uses AI to generate a glorifying description and top experiences for the destination."""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"), temperature=0.7)
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
        content = res.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        # Fallback if AI quota is hit
        return {
            "hype_description": f"Get ready for an unforgettable adventure in {destination}! Prepare for amazing sights, incredible food, and lifelong memories.",
            "experiences": [
                {"title": "Iconic Sights", "description": "Explore the famous landmarks that make this destination globally renowned."},
                {"title": "Local Culture", "description": "Immerse yourself in the unique vibe, traditions, and nightlife."},
                {"title": "Culinary Delights", "description": "Taste the legendary local flavors everyone talks about."}
            ]
        }


# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Group Trip Planner", page_icon="✈️", layout="centered")

# --- CSS FOR STYLING (UPDATED FOR BETTER READABILITY) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    .place-card {
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FF4B4B;
        margin-bottom: 15px;
        /* Using rgba makes it adapt beautifully to both Light and Dark mode */
        background-color: rgba(128, 128, 128, 0.1); 
    }
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

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("✈️ Navigation")
page = st.sidebar.radio("Go to", ["Create New Trip", "Vote on Trip", "View Final Plan"])

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
        
        if st.button("Plan a Different Trip"):
            del st.session_state["created_trip_id"]
            st.rerun()
            
    else:
        st.markdown("Use AI to scout the best locations and generate a voting link for your friends.")
        with st.form("create_trip_form"):
            destination = st.text_input("Where do you want to go?", "Goa")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", date.today())
            with col2:
                end_date = st.date_input("End Date", date.today())
            
            budget = st.number_input("Budget per person (USD)", min_value=100, value=500)
            submitted = st.form_submit_button("🚀 Launch AI Scout")

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

                    run_scout_agent(trip_id, destination)
                    
                    st.session_state["created_trip_id"] = trip_id
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error creating trip: {e}")

# ==========================================
# PAGE 2: VOTE (MEMBER VIEW)
# ==========================================
elif page == "Vote on Trip":
    
    if "current_trip_id" not in st.session_state:
        st.title("🎟️ Join the Adventure")
        trip_id_input = st.text_input("Paste the Trip ID here:")
        member_name = st.text_input("Your Name:")
        
        if st.button("Enter Voting Booth") and trip_id_input and member_name:
            try:
                trip_check = supabase.table("trips").select("*").eq("id", trip_id_input).execute()
                if not trip_check.data:
                    st.error("Trip ID not found!")
                else:
                    member_data = {"trip_id": trip_id_input, "name": member_name}
                    member_res = supabase.table("members").insert(member_data).execute()
                    
                    st.session_state["current_trip_id"] = trip_id_input
                    st.session_state["current_member_id"] = member_res.data[0]['id']
                    st.session_state["member_name"] = member_name
                    # Save destination for the Hype Engine
                    st.session_state["destination"] = trip_check.data[0]['destination'] 
                    st.rerun()
            except Exception as e:
                st.error(f"Error joining: {e}")

    else:
        trip_id = st.session_state["current_trip_id"]
        dest = st.session_state.get("destination", "this destination")
        
        # --- NEW: GLORIFIED WELCOME & HYPE ---
        st.markdown(f"<h1 style='text-align: center;'>🌟 Welcome to {dest.upper()}!</h1>", unsafe_allow_html=True)
        
        with st.spinner(f"Loading the vibe for {dest}..."):
            hype_data = get_destination_hype(dest)
            
        st.markdown(f"<div class='hype-text'>\"{hype_data['hype_description']}\"</div>", unsafe_allow_html=True)
        
        # --- NEW: THINGS TO EXPERIENCE ---
        st.subheader("💡 Why People Love It Here")
        for exp in hype_data['experiences']:
            st.info(f"**{exp['title']}**\n\n{exp['description']}")
            
        st.divider()

        # User Switcher
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.write(f"Alright **{st.session_state['member_name']}**, time to cast your votes!")
        with col_btn:
            if st.button("🔄 Switch User"):
                del st.session_state["current_trip_id"]
                del st.session_state["current_member_id"]
                del st.session_state["member_name"]
                del st.session_state["destination"]
                st.rerun()
        
        # Fetch Members (so we can translate member_id to their real name)
        members_res = supabase.table("members").select("*").eq("trip_id", trip_id).execute()
        member_map = {m['id']: m['name'] for m in members_res.data}
        
        # Fetch Places
        places_res = supabase.table("places").select("*").eq("trip_id", trip_id).execute()
        places = places_res.data
        
        # Fetch Votes (to show the live leaderboard)
        votes_by_place = {}
        if places:
            place_ids = [p['id'] for p in places]
            votes_res = supabase.table("votes").select("*").in_("place_id", place_ids).execute()
            
            # Organize the votes into a dictionary: { place_id: ["Raaj", "Simran"] }
            for pid in place_ids:
                votes_by_place[pid] = []
                
            for v in votes_res.data:
                if v['vote_value'] > 0: # Only count positive votes
                    voter_name = member_map.get(v['member_id'], "Unknown")
                    votes_by_place[v['place_id']].append(voter_name)

        if not places:
            st.warning("No places found. Ask the leader to run the Scout!")
        else:
            with st.form("voting_form"):
                st.subheader("📍 Choose Your Must-Do Activities")
                selected_places = []
                
                for place in places:
                    # Create two columns: 75% for the card, 25% for the vote tally
                    col_main, col_votes = st.columns([3, 1])
                    
                    with col_main:
                        cost_val = place.get('estimated_cost', 1)
                        cost_display = "Free / Very Cheap" if cost_val == 0 else '$' * cost_val
                        
                        rating_val = place.get('rating', 0.0)
                        rating_display = f"⭐ {rating_val} / 5.0" if rating_val > 0 else "⭐ Rating N/A"
                        
                        search_query = urllib.parse.quote_plus(f"{place['name']} {dest}")
                        google_link = f"https://www.google.com/search?q={search_query}"
                        
                        st.markdown(f"""
                        <div class="place-card">
                            <h4 style="margin-bottom: 5px;">{place['name']} <span style="font-size: 14px; font-weight: normal; color: gray;">({place['category']})</span></h4>
                            <p style="margin-bottom: 10px; line-height: 1.4;">{place['description']}</p>
                            <p style="margin-bottom: 10px; font-weight: bold;">💰 {cost_display} | {rating_display}</p>
                            <a href="{google_link}" target="_blank" style="text-decoration: none; color: #1E90FF; font-weight: bold;">🔍 See photos & details on Google</a>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # The voting checkbox
                        if st.checkbox(f"Add {place['name']} to my wishlist", key=place['id']):
                            selected_places.append(place['id'])
                    
                    with col_votes:
                        # --- NEW: Live Vote Tally UI ---
                        voters = votes_by_place.get(place['id'], [])
                        st.markdown(f"<div style='padding-top: 15px;'><b>Current Votes: {len(voters)}</b></div>", unsafe_allow_html=True)
                        
                        if voters:
                            for name in voters:
                                st.markdown(f"✅ <span style='color: gray; font-style: italic;'>{name}</span>", unsafe_allow_html=True)
                        else:
                            st.caption("No votes yet. Be the first!")
                    
                    st.write("---") # Spacing line below the row

                # Global Vibe Check
                st.subheader("✨ What's your overarching vibe?")
                vibe = st.select_slider("Select your travel style", options=["Extremely Chill", "Balanced", "Non-stop Adventure"])
                comment = st.text_area("Any specific requests? (e.g., 'No seafood', 'I want to hike')")

                if st.form_submit_button("Submit My Votes"):
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
                            # Use upsert to handle if they resubmit to change votes
                            supabase.table("votes").upsert(vote_inserts).execute()
                            st.success("🎉 Votes locked in! Click 'Switch User' if someone else needs to vote.")
                        except Exception as e:
                            st.error(f"Error saving votes: {e}")
                    else:
                        st.warning("You didn't select any places! Don't be boring, pick something!")
                        
# ==========================================
# PAGE 3: VIEW FINAL PLAN (THE ARCHITECT)
# ==========================================
elif page == "View Final Plan":
    st.title("📅 Your Perfect Itinerary")
    
    trip_id_input = st.text_input("Enter Trip ID to see the plan:")
    
    if st.button("Generate / View Plan"):
        if trip_id_input:
            with st.spinner("🧠 The Architect is resolving conflicts and building the schedule..."):
                plan = generate_itinerary(trip_id_input)
                
                if "error" in plan:
                    st.error(plan["error"])
                else:
                    st.success("✨ Itinerary Generated!")
                    
                    for day in plan:
                        st.subheader(f"Day {day['day']}")
                        for activity in day['activities']:
                            st.markdown(f"**{activity['time']}** — {activity['activity']}")
                            st.caption(f"_{activity.get('notes', '')}_")
                        st.divider()
                        
                    st.markdown("### 🗺️ Navigate")
                    st.info("Click here to open today's route on Google Maps (Coming soon!)")