import streamlit as st
import pandas as pd
from datetime import date
from agents.architect import generate_itinerary
import uuid
import time

# Import your modules
from database.connection import get_db
from agents.scout import run_scout_agent

# Initialize DB
supabase = get_db()

# --- PAGE CONFIG ---
st.set_page_config(page_title="AI Group Trip Planner", page_icon="✈️", layout="centered")

# --- CSS FOR STYLING ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
    }
    .place-card {
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        background-color: #f9f9f9;
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
    
    # LOCK: If a trip was just created, hide the form and show the ID
    if "created_trip_id" in st.session_state:
        st.success("✅ Trip Created & Places Scouted!")
        st.info("📋 **Copy this Trip ID and share it with your group:**")
        st.code(st.session_state["created_trip_id"], language="text")
        st.markdown("They will need this ID to vote on the next tab.")
        
        # Give them a way to reset if they actually want a new trip
        if st.button("Plan a Different Trip"):
            del st.session_state["created_trip_id"]
            st.rerun()
            
    # Show the form only if a trip hasn't been created yet
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
                    # 1. Create Trip in DB
                    trip_data = {
                        "destination": destination,
                        "start_date": str(start_date),
                        "end_date": str(end_date),
                        "budget_limit": budget,
                        "status": "VOTING"
                    }
                    response = supabase.table("trips").insert(trip_data).execute()
                    trip_id = response.data[0]['id']

                    # 2. Run the Scout Agent
                    run_scout_agent(trip_id, destination)
                    
                    # 3. Lock the state and trigger a UI refresh
                    st.session_state["created_trip_id"] = trip_id
                    st.balloons()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error creating trip: {e}")

# ==========================================
# PAGE 2: VOTE (MEMBER VIEW)
# ==========================================
elif page == "Vote on Trip":
    st.title("🗳️ Vote for Your Favorites")
    
    # 1. Login / Join Trip
    if "current_trip_id" not in st.session_state:
        trip_id_input = st.text_input("Paste the Trip ID here:")
        member_name = st.text_input("Your Name:")
        
        if st.button("Join Trip") and trip_id_input and member_name:
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
                    st.rerun()
            except Exception as e:
                st.error(f"Error joining: {e}")

    # 2. Voting Interface
    else:
        trip_id = st.session_state["current_trip_id"]
        
        # --- NEW: Quick Switch User Button (No reload required!) ---
        col_text, col_btn = st.columns([3, 1])
        with col_text:
            st.write(f"Welcome, **{st.session_state['member_name']}**! Select the places you'd love to visit.")
        with col_btn:
            if st.button("🔄 Switch User"):
                del st.session_state["current_trip_id"]
                del st.session_state["current_member_id"]
                del st.session_state["member_name"]
                st.rerun()
        
        # Fetch Places from DB
        places_res = supabase.table("places").select("*").eq("trip_id", trip_id).execute()
        places = places_res.data
        
        if not places:
            st.warning("No places found for this trip yet. Ask the leader to run the Scout!")
        else:
            with st.form("voting_form"):
                st.subheader("📍 Places to Visit")
                selected_places = []
                
                for place in places:
                    st.markdown(f"""
                    <div class="place-card">
                        <b>{place['name']}</b> ({place['category']})<br>
                        <span style="color:gray">{place['description']}</span><br>
                        💰 Cost Level: {'$' * place['estimated_cost']} | ⭐ {place['rating']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.checkbox(f"Vote for {place['name']}", key=place['id']):
                        selected_places.append(place['id'])
                    
                    st.write("---")

                st.subheader("✨ What's your vibe for this trip?")
                vibe = st.select_slider("Balance", options=["Chill / Relaxing", "Balanced", "Adventure / Party"])
                comment = st.text_area("Any specific requests? (e.g., 'No seafood', 'I want to hike')")

                if st.form_submit_button("Submit Votes"):
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
                            supabase.table("votes").insert(vote_inserts).execute()
                            st.success("🎉 Votes Saved! Click 'Switch User' above to let the next person vote.")
                        except Exception as e:
                            st.error(f"Error saving votes: {e}")
                    else:
                        st.warning("You didn't select any places!")
# ==========================================
# PAGE 3: VIEW FINAL PLAN (THE ARCHITECT)
# ==========================================
elif page == "View Final Plan":
    st.title("📅 Your Perfect Itinerary")
    
    trip_id_input = st.text_input("Enter Trip ID to see the plan:")
    
    if st.button("Generate / View Plan"):
        if trip_id_input:
            with st.spinner("🧠 The Architect is resolving conflicts and building the schedule..."):
                # 1. Run the Architect Agent
                plan = generate_itinerary(trip_id_input)
                
                if "error" in plan:
                    st.error(plan["error"])
                else:
                    st.success("✨ Itinerary Generated!")
                    
                    # 2. Display the Plan nicely
                    for day in plan:
                        st.subheader(f"Day {day['day']}")
                        for activity in day['activities']:
                            st.markdown(f"**{activity['time']}** — {activity['activity']}")
                            st.caption(f"_{activity.get('notes', '')}_")
                        st.divider()
                        
                    # 3. (Optional) Show Map Link
                    st.markdown("### 🗺️ Navigate")
                    st.info("Click here to open today's route on Google Maps (Coming soon!)")