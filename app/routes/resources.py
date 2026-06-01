from flask import Blueprint, render_template, flash
from flask_login import login_required
from ..database import get_mongo_db

resources_bp = Blueprint('resources', __name__)

DEFAULT_INVENTORY = {
    'ambulances': 10,
    'rescue_teams': 5,
    'food_packets': 1000,
    'helicopters': 2,
}


@resources_bp.route('/resources')
@login_required
def index():
    inventory = DEFAULT_INVENTORY.copy()
    allocations = []
    try:
        db = get_mongo_db()
        inv = db.resources.find_one({'_id': 'inventory'})
        if inv:
            inventory = {k: v for k, v in inv.items() if k != '_id'}
        allocations = list(db.allocations.find().sort('_id', -1).limit(20))
        for a in allocations:
            a['_id'] = str(a['_id'])
    except Exception:
        flash('Could not load live inventory. Showing defaults.', 'warning')

    return render_template('resources/index.html', inventory=inventory, allocations=allocations)
