from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..database import get_mongo_db
from ..agents.analysis_agent import analyze_disaster
from ..agents.resource_agent import allocate_resources
from ..agents.route_agent import optimize_route
from ..agents.alert_agent import generate_alert
from datetime import datetime
from bson import ObjectId

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/reports')
@login_required
def index():
    reports = []
    try:
        db = get_mongo_db()
        reports = list(db.disaster_reports.find().sort('timestamp', -1).limit(50))
        for r in reports:
            r['_id'] = str(r['_id'])
    except Exception:
        flash('Could not connect to database.', 'warning')
    return render_template('reports/index.html', reports=reports)


@reports_bp.route('/reports/new', methods=['GET', 'POST'])
@login_required
def new_report():
    if request.method == 'POST':
        location    = request.form.get('location', '').strip()
        description = request.form.get('description', '').strip()
        lat         = request.form.get('lat', '')
        lng         = request.form.get('lng', '')

        if not location or not description:
            flash('Location and description are required.', 'danger')
            return render_template('reports/new.html')

        # ── Run AI Agents ──────────────────────────────────────────────────
        analysis   = analyze_disaster(location, description)
        report_doc = {
            'location':    location,
            'description': description,
            'type':        analysis['type'],
            'severity':    analysis['severity'],
            'risk_score':  analysis['risk_score'],
            'summary':     analysis['summary'],
            'status':      'Active',
            'reported_by': current_user.username,
            'timestamp':   datetime.utcnow().isoformat(),
            'lat':         float(lat) if lat else None,
            'lng':         float(lng) if lng else None,
        }

        report_id = 'demo'
        try:
            db = get_mongo_db()
            result = db.disaster_reports.insert_one(report_doc.copy())
            report_id = str(result.inserted_id)
        except Exception:
            pass

        allocation = allocate_resources(analysis['severity'], report_id)
        route      = optimize_route(location, analysis['type'])
        alert      = generate_alert(location, analysis['type'], analysis['severity'], report_id)

        return render_template(
            'reports/result.html',
            report=report_doc,
            report_id=report_id,
            analysis=analysis,
            allocation=allocation,
            route=route,
            alert=alert,
        )

    return render_template('reports/new.html')


@reports_bp.route('/reports/<report_id>')
@login_required
def view_report(report_id):
    report = None
    try:
        db = get_mongo_db()
        report = db.disaster_reports.find_one({'_id': ObjectId(report_id)})
        if report:
            report['_id'] = str(report['_id'])
    except Exception:
        pass
    if not report:
        flash('Report not found.', 'warning')
        return redirect(url_for('reports.index'))
    return render_template('reports/view.html', report=report)
