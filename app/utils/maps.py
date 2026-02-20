# app/utils/maps.py
import urllib.parse
from typing import List

def generate_google_maps_url(places: List[str], city: str) -> str:
    """
    Takes a geographically sorted list of places and generates a 
    100% free Google Maps Direction URL.
    """
    if len(places) < 2:
        return ""
        
    # 1. Clean and encode the start and end points
    origin = urllib.parse.quote_plus(f"{places[0]} {city}")
    destination = urllib.parse.quote_plus(f"{places[-1]} {city}")
    
    # 2. Encode the places in between as waypoints (separated by '|')
    if len(places) > 2:
        middle_places = places[1:-1]
        waypoints_str = "|".join([f"{p} {city}" for p in middle_places])
        waypoints = urllib.parse.quote_plus(waypoints_str)
    else:
        waypoints = ""
        
    # 3. Construct the final URL
    base_url = "https://www.google.com/maps/dir/?api=1"
    full_url = f"{base_url}&origin={origin}&destination={destination}"
    
    if waypoints:
        full_url += f"&waypoints={waypoints}"
        
    return full_url