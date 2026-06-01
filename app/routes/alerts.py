from flask import Blueprint, render_template, flash
from flask_login import login_required
from ..database import get_mongo_db

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('/alerts')
@login_required
def index():
    alerts = []
    try:
        db = get_mongo_db()
        alerts = list(db.alerts.find().sort('created_at', -1).limit(50))
        for a in alerts:
            a['_id'] = str(a['_id'])
    except Exception:
        flash('Could not load alerts from database.', 'warning')
    return render_template('alerts/index.html', alerts=alerts)
