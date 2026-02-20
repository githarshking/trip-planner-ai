# app/utils/routing.py
import time
import requests
from geopy.geocoders import Nominatim
from typing import List, Dict

def fetch_coordinates(place_names: list[str], city: str) -> list[dict]:
    """
    Step 1: Converts place names into Lat/Lon using a Dual-Engine approach.
    """
    from geopy.geocoders import Nominatim, Photon
    import time
    
    # Engine 1: Strict & Precise
    geo_nom = Nominatim(user_agent="trip_planner_ai_strict")
    # Engine 2: Fuzzy & Regional (Ignores strict city borders)
    geo_pho = Photon(user_agent="trip_planner_ai_fuzzy")
    
    results = []
    
    print(f"🌍 Geocoding {len(place_names)} places in/around {city}...")
    for name in place_names:
        location = None
        try:
            # Attempt 1: Strict search with Nominatim
            location = geo_nom.geocode(f"{name}, {city}", timeout=10)
            
            # Attempt 2: Fuzzy search with Photon (finds places outside city limits)
            if not location:
                print(f"   ↳ Strict search failed. Trying fuzzy regional search for '{name}'...")
                # Photon is smart enough to find "Wonderla" near "Bangalore" without strict borders
                location = geo_pho.geocode(f"{name} {city}", timeout=10)
                
            # Attempt 3: Global Fuzzy search (Last resort)
            if not location:
                location = geo_pho.geocode(name, timeout=10)

            if location:
                results.append({
                    "name": name,
                    "lat": location.latitude,
                    "lon": location.longitude
                })
            else:
                print(f"⚠️ Warning: Completely failed to find coordinates for '{name}'.")
                
        except Exception as e:
            print(f"❌ Geocoding error for {name}: {e}")
            
        # Respect free API limits
        time.sleep(1.5) 
        
    return results

def get_osrm_matrix(coordinates: List[Dict]) -> List[List[float]]:
    """
    Step 2: Fetches the distance matrix from OSRM.
    Returns a 2D grid of driving distances (in meters).
    """
    if len(coordinates) < 2:
        return []
    
    # OSRM requires coordinates in Longitude,Latitude format
    coord_strings = [f"{c['lon']},{c['lat']}" for c in coordinates]
    coord_uri = ";".join(coord_strings)
    
    # Call the free OSRM Table Service
    url = f"http://router.project-osrm.org/table/v1/driving/{coord_uri}?annotations=distance"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("code") == "Ok":
            return data["distances"]
        else:
            print(f"⚠️ OSRM API Error: {data.get('message')}")
            return []
    except Exception as e:
        print(f"❌ Request to OSRM failed: {e}")
        return []

def solve_tsp(places: List[Dict], distance_matrix: List[List[float]], start_index: int = 0) -> List[Dict]:
    """
    Step 3: The Greedy Nearest-Neighbor Algorithm.
    Mathmatically sorts the places to prevent zigzagging.
    """
    if not places or not distance_matrix:
        return places
        
    n = len(places)
    visited = [False] * n
    optimized_route = []
    
    current_index = start_index
    visited[current_index] = True
    optimized_route.append(places[current_index])
    
    # Find the nearest unvisited neighbor until all are visited
    for _ in range(n - 1):
        nearest_dist = float('inf')
        nearest_index = -1
        
        for j in range(n):
            if not visited[j]:
                dist = distance_matrix[current_index][j]
                
                # --- FIX: Ensure dist is not None before comparing ---
                if dist is not None and dist < nearest_dist:
                    nearest_dist = dist
                    nearest_index = j
                    
        if nearest_index != -1:
            visited[nearest_index] = True
            optimized_route.append(places[nearest_index])
            current_index = nearest_index # Move to the new place
        else:
            # --- FIX: Fallback if a place is completely unreachable by car ---
            # Just grab the first unvisited place to prevent infinite loops
            for j in range(n):
                if not visited[j]:
                    visited[j] = True
                    optimized_route.append(places[j])
                    current_index = j
                    break
            
    return optimized_route
def optimize_daily_route(place_names: List[str], city: str) -> List[str]:
    """
    MASTER FUNCTION: The only function the AI Architect needs to call.
    """
    print(f"🗺️ Starting Route Optimization for {city}...")
    
    # 1. Get Lat/Lon
    coords = fetch_coordinates(place_names, city)
    if len(coords) < 2:
        print("⏭️ Not enough valid coordinates to optimize. Skipping math.")
        return place_names
        
    # 2. Get Distance Grid
    matrix = get_osrm_matrix(coords)
    if not matrix:
        print("⏭️ Distance matrix failed. Skipping math.")
        return [c['name'] for c in coords]
        
    # 3. Sort the Route
    sorted_coords = solve_tsp(coords, matrix)
    
    # 4. Return just the names in the new, perfect order
    sorted_names = [place['name'] for place in sorted_coords]
    
    print(f"✅ Route Optimized: {' ➔ '.join(sorted_names)}")
    return sorted_names