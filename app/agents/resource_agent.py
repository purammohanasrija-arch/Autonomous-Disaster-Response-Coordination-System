"""
Resource Allocation Agent
Allocates available resources based on disaster severity.
"""
from ..database import get_mongo_db


ALLOCATION_RULES = {
    'High': {
        'rescue_teams': 2,
        'ambulances': 1,
        'food_packets': 200,
        'helicopters': 1,
    },
    'Medium': {
        'rescue_teams': 1,
        'ambulances': 1,
        'food_packets': 100,
        'helicopters': 0,
    },
    'Low': {
        'rescue_teams': 1,
        'ambulances': 0,
        'food_packets': 50,
        'helicopters': 0,
    },
}


def allocate_resources(severity: str, report_id: str) -> dict:
    """
    Deducts resources from MongoDB inventory and returns allocation summary.
    """
    needed = ALLOCATION_RULES.get(severity, ALLOCATION_RULES['Medium']).copy()
    allocated = {}
    insufficient = []

    try:
        db = get_mongo_db()
        inventory = db.resources.find_one({'_id': 'inventory'})

        if not inventory:
            # Seed default inventory
            inventory = {
                '_id': 'inventory',
                'ambulances': 10,
                'rescue_teams': 5,
                'food_packets': 1000,
                'helicopters': 2,
            }
            db.resources.insert_one(inventory)

        for resource, qty in needed.items():
            available = inventory.get(resource, 0)
            give = min(qty, available)
            allocated[resource] = give
            if give < qty:
                insufficient.append(resource)
            if give > 0:
                db.resources.update_one(
                    {'_id': 'inventory'},
                    {'$inc': {resource: -give}}
                )

        # Log allocation
        db.allocations.insert_one({
            'report_id': report_id,
            'severity': severity,
            'allocated': allocated,
            'insufficient': insufficient,
        })

    except Exception as e:
        # MongoDB unavailable – return rule-based allocation without DB ops
        allocated = needed
        insufficient = []

    return {
        'allocated': allocated,
        'insufficient': insufficient,
        'status': 'Partial' if insufficient else 'Allocated Successfully',
    }
