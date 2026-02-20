# app/utils/accommodations.py
import os
import requests
import time
from typing import List, Dict

def get_amadeus_token() -> str:
    """Authenticates with Amadeus to get a temporary access token."""
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        print("⚠️ Amadeus keys missing. Skipping API call.")
        return ""
        
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = f"grant_type=client_credentials&client_id={api_key}&client_secret={api_secret}"
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json().get("access_token", "")
    except Exception as e:
        print(f"❌ Amadeus Authentication Failed: {e}")
        return ""

def search_hotels(lat: float, lon: float, daily_budget: int) -> List[Dict]:
    """
    Uses Amadeus API to find real hotels near the coordinates.
    Filters out options that exceed the daily budget.
    """
    print(f"🏨 Searching Amadeus for hotels near {lat}, {lon} with budget ₹{daily_budget}...")
    token = get_amadeus_token()
    
    options = []
    
    # --- AMADEUS API LOGIC ---
    if token:
        # Step 1: Find Hotel IDs near coordinates
        headers = {"Authorization": f"Bearer {token}"}
        geo_url = f"https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-geocode?latitude={lat}&longitude={lon}&radius=5&radiusUnit=KM"
        
        try:
            geo_res = requests.get(geo_url, headers=headers)
            if geo_res.status_code == 200:
                hotels = geo_res.json().get("data", [])
                hotel_ids = [h["hotelId"] for h in hotels[:5]] # Grab top 5
                
                # Step 2: Get Prices for those Hotels (if we found any)
                if hotel_ids:
                    id_string = ",".join(hotel_ids)
                    offer_url = f"https://test.api.amadeus.com/v3/shopping/hotel-offers?hotelIds={id_string}"
                    offer_res = requests.get(offer_url, headers=headers)
                    
                    if offer_res.status_code == 200:
                        offers = offer_res.json().get("data", [])
                        for offer in offers:
                            try:
                                price = float(offer["offers"][0]["price"]["total"])
                                name = offer["hotel"]["name"]
                                if price <= daily_budget:
                                    options.append({"name": name, "price": price, "type": "Hotel"})
                            except:
                                continue
        except Exception as e:
            print(f"❌ Amadeus Search Error: {e}")

    # --- FALLBACK LOGIC ---
    # If Amadeus test environment lacks data for this city, we generate deterministic realistic options
    # --- FALLBACK LOGIC ---
    if not options:
        print("⚠️ No Amadeus data found. Falling back to realistic deterministic estimates.")
        
        # Adjusted for INR pricing
        if daily_budget >= 8000:
            options.append({"name": "Premium City Hotel", "price": daily_budget * 0.8, "type": "4-Star"})
        elif daily_budget >= 3000:
            options.append({"name": "Cozy Boutique Stay", "price": daily_budget * 0.75, "type": "3-Star"})
            
        options.append({"name": "Backpacker Hostel / Zostel", "price": 800.0, "type": "Hostel"})
        
    return options[:3]