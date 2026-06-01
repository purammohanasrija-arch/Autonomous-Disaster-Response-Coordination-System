"""
Route Optimization Agent
Finds the safest and fastest rescue route using a simple heuristic.
In production this would call OpenRouteService or OSRM.
"""

# Simulated waypoint graph (location -> nearest safe shelter)
ROUTE_MAP = {
    'default': {
        'waypoints': ['Disaster Station', 'Highway 1', 'Relief Shelter'],
        'estimated_time_mins': 15,
        'distance_km': 8.5,
        'notes': 'Avoid flooded underpasses. Use Highway 1 bypass.',
    }
}

LOCATION_ROUTES = {
    'river road': {
        'waypoints': ['River Road Station', 'Highway 4', 'Highland Shelter'],
        'estimated_time_mins': 12,
        'distance_km': 6.2,
        'notes': 'River Road bridge closed. Use Highway 4.',
    },
    'green park': {
        'waypoints': ['Green Park Gate', 'Main Avenue', 'City Relief Center'],
        'estimated_time_mins': 8,
        'distance_km': 3.1,
        'notes': 'Main Avenue clear. Direct route available.',
    },
    'hill zone': {
        'waypoints': ['Hill Zone Base', 'Mountain Road', 'Valley Shelter'],
        'estimated_time_mins': 25,
        'distance_km': 14.0,
        'notes': 'Mountain Road may have debris. Proceed with caution.',
    },
}


def optimize_route(location: str, disaster_type: str) -> dict:
    """
    Returns route information for the given location.
    """
    loc_key = location.lower().strip()
    route = None
    for key, val in LOCATION_ROUTES.items():
        if key in loc_key:
            route = val
            break

    if not route:
        route = ROUTE_MAP['default'].copy()
        route['waypoints'][0] = f'{location} Station'

    return {
        'origin': location,
        'destination': route['waypoints'][-1],
        'waypoints': route['waypoints'],
        'estimated_time_mins': route['estimated_time_mins'],
        'distance_km': route['distance_km'],
        'notes': route['notes'],
        'route_summary': ' → '.join(route['waypoints']),
    }
