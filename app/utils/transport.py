# app/utils/transport.py

def get_transit_instruction(distance_meters: float, daily_budget: int) -> str:
    """
    Deterministic rule engine to calculate transit mode and estimated cost.
    distance_meters: The distance from OSRM.
    daily_budget: The available budget (INR).
    """
    if distance_meters <= 0:
        return ""
        
    km = distance_meters / 1000.0
    
    # Rule 1: Less than 2km is walkable
    if km < 2.0:
        mins = int(km * 12) # Avg walking speed: 12 mins per km
        return f"🚶 Walk ({km:.1f} km, ~{mins} mins) - Free"
        
    # Rule 2: Greater than 2km, check the budget
    else:
        # If daily budget is high (> 4000 INR), take an Uber
        if daily_budget > 4000:
            cost = int(km * 25) # Approx ₹25/km for Uber/Taxi
            mins = int(km * 3)  # Approx 3 mins/km driving in city traffic
            return f"🚕 Uber/Cab ({km:.1f} km, ~{mins} mins) - Est. ₹{cost}"
            
        # If daily budget is lower, take an Auto Rickshaw or Public Transit
        else:
            cost = int(km * 15) # Approx ₹15/km for Auto Rickshaw
            mins = int(km * 4)  # Slightly slower
            return f"🛺 Auto Rickshaw ({km:.1f} km, ~{mins} mins) - Est. ₹{cost}"