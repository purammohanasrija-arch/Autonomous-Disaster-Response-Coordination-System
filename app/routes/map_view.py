from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from ..database import get_mongo_db

map_bp = Blueprint('map_view', __name__)


@map_bp.route('/map')
@login_required
def index():
    markers  = []
    sos_pins = []
    try:
        db = get_mongo_db()
        reports = list(db.disaster_reports.find(
            {'lat': {'$ne': None}, 'lng': {'$ne': None}},
            {'location':1,'type':1,'severity':1,'lat':1,'lng':1,'status':1,'timestamp':1,'description':1}
        ).limit(200))
        for r in reports:
            r['_id'] = str(r['_id'])
            markers.append(r)

        sos_list = list(db.sos_alerts.find(
            {'lat': {'$ne': None}, 'lng': {'$ne': None}},
            {'location':1,'sos_type':1,'status':1,'lat':1,'lng':1,'created_at':1,'message':1,'name':1}
        ).limit(100))
        for s in sos_list:
            s['_id'] = str(s['_id'])
            sos_pins.append(s)
    except Exception:
        pass

    return render_template('map/index.html', markers=markers, sos_pins=sos_pins)


@map_bp.route('/api/map/data')
@login_required
def map_data():
    """Live map data endpoint for auto-refresh."""
    markers  = []
    sos_pins = []
    try:
        db = get_mongo_db()
        for r in db.disaster_reports.find(
            {'lat': {'$ne': None}, 'lng': {'$ne': None}},
            {'location':1,'type':1,'severity':1,'lat':1,'lng':1,'status':1,'timestamp':1}
        ).limit(200):
            r['_id'] = str(r['_id'])
            markers.append(r)
        for s in db.sos_alerts.find(
            {'lat': {'$ne': None}, 'lng': {'$ne': None}},
            {'location':1,'sos_type':1,'status':1,'lat':1,'lng':1,'created_at':1,'name':1}
        ).limit(100):
            s['_id'] = str(s['_id'])
            sos_pins.append(s)
    except Exception:
        pass
    return jsonify({'markers': markers, 'sos': sos_pins})
