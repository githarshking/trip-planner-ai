from app.utils.routing import optimize_daily_route

# A totally scrambled list of places in Bangalore
scrambled_places = [
    "Nandi Hills",           # Far North
    "Lalbagh Botanical Garden", # Central/South
    "Bangalore Palace",      # Central/North
    "Wonderla Amusement Park"  # Far South/West
]

print("Original (Zig-Zag) Order:")
print(scrambled_places)
print("\n" + "="*40 + "\n")

# Run the Engine
perfect_order = optimize_daily_route(scrambled_places, "Bangalore")