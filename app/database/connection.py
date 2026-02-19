# app/database/connection.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    raise ValueError("Supabase credentials not found. Check your .env file.")

# Create the connection object
supabase: Client = create_client(url, key)

def get_db():
    """Helper to get the database client in other files"""
    return supabase