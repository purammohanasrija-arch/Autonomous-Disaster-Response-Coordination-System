"""
Analytics route – disaster trends, severity breakdown, resource usage charts.
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from ..database import get_mongo_db
from collections import Counter
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)


def _safe_db(fn, default):
    try:
        return fn()
    except Exception:
        return default


@analytics_bp.route('/analytics')
@login_required
def index():
    return render_template('analytics/index.html')


@analytics_bp.route('/api/analytics/summary')
@login_required
def summary():
    db = None
    try:
        db = get_mongo_db()
    except Exception:
        return jsonify(_demo_data())

    # ── Severity breakdown ──────────────────────────────────────────────
    severity_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    for doc in _safe_db(lambda: list(db.disaster_reports.find({}, {'severity': 1})), []):
        s = doc.get('severity', 'Low')
        severity_counts[s] = severity_counts.get(s, 0) + 1

    # ── Disaster type breakdown ─────────────────────────────────────────
    type_counts = Counter()
    for doc in _safe_db(lambda: list(db.disaster_reports.find({}, {'type': 1})), []):
        type_counts[doc.get('type', 'Other')] += 1

    # ── Reports per day (last 7 days) ───────────────────────────────────
    daily = {}
    today = datetime.utcnow()
    for i in range(6, -1, -1):
        day = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        daily[day] = 0

    for doc in _safe_db(lambda: list(db.disaster_reports.find({}, {'timestamp': 1})), []):
        ts = doc.get('timestamp', '')
        if ts:
            day = ts[:10]
            if day in daily:
                daily[day] += 1

    # ── SOS stats ───────────────────────────────────────────────────────
    sos_total    = _safe_db(lambda: db.sos_alerts.count_documents({}), 0)
    sos_active   = _safe_db(lambda: db.sos_alerts.count_documents({'status': 'Active'}), 0)
    sos_resolved = _safe_db(lambda: db.sos_alerts.count_documents({'status': 'Resolved'}), 0)

    sos_type_counts = Counter()
    for doc in _safe_db(lambda: list(db.sos_alerts.find({}, {'sos_type': 1})), []):
        sos_type_counts[doc.get('sos_type', 'General')] += 1

    # ── Resource usage ──────────────────────────────────────────────────
    inv = _safe_db(lambda: db.resources.find_one({'_id': 'inventory'}) or {}, {})
    resource_used = {
        'ambulances':    10 - inv.get('ambulances', 10),
        'rescue_teams':  5  - inv.get('rescue_teams', 5),
        'food_packets':  1000 - inv.get('food_packets', 1000),
        'helicopters':   2  - inv.get('helicopters', 2),
    }

    # ── Totals ──────────────────────────────────────────────────────────
    total_reports = _safe_db(lambda: db.disaster_reports.count_documents({}), 0)
    total_alerts  = _safe_db(lambda: db.alerts.count_documents({}), 0)

    return jsonify({
        'severity':       severity_counts,
        'types':          dict(type_counts.most_common(8)),
        'daily':          daily,
        'sos':            {'total': sos_total, 'active': sos_active, 'resolved': sos_resolved},
        'sos_types':      dict(sos_type_counts),
        'resource_used':  resource_used,
        'totals':         {'reports': total_reports, 'alerts': total_alerts, 'sos': sos_total},
    })


def _demo_data():
    """Fallback demo data when MongoDB is unavailable."""
    today = datetime.utcnow()
    daily = {(today - timedelta(days=i)).strftime('%Y-%m-%d'): [3,5,2,7,4,6,3][i]
             for i in range(6, -1, -1)}
    return {
        'severity':      {'High': 5, 'Medium': 8, 'Low': 3},
        'types':         {'Flood': 6, 'Fire': 4, 'Earthquake': 3, 'Storm': 2, 'Other': 1},
        'daily':         daily,
        'sos':           {'total': 7, 'active': 2, 'resolved': 5},
        'sos_types':     {'Medical Emergency': 3, 'Trapped / Stuck': 2, 'Flood': 2},
        'resource_used': {'ambulances': 3, 'rescue_teams': 2, 'food_packets': 450, 'helicopters': 1},
        'totals':        {'reports': 16, 'alerts': 12, 'sos': 7},
    }
