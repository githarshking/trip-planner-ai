from app.agents.scout import run_scout_agent
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Create a Fake Trip in DB to attach places to
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Create a dummy trip for "Goa"
print("Creating test trip...")
trip = supabase.table("trips").insert({
    "destination": "Goa",
    "start_date": "2024-12-01",
    "end_date": "2024-12-05",
    "budget_limit": 500
}).execute()

trip_id = trip.data[0]['id']
print(f"Test Trip ID: {trip_id}")

# 2. Run the Agent
print("🚀 Launching Scout Agent...")
run_scout_agent(trip_id, "Goa")

print("🎉 Done! Check your Supabase 'places' table.")