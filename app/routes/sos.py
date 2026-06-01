"""
SOS Alert routes — with WhatsApp notifications.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from ..database import get_mongo_db
from ..whatsapp import send_whatsapp, send_whatsapp_bulk, format_sos_message
from datetime import datetime
from bson import ObjectId
import threading

sos_bp = Blueprint('sos', __name__)


def _get_all_phones():
    """Get all registered phone numbers from MongoDB users collection."""
    try:
        db   = get_mongo_db()
        rows = db.users.find(
            {'phone': {'$exists': True, '$ne': ''}},
            {'phone': 1}
        )
        return [r['phone'] for r in rows if r.get('phone')]
    except Exception:
        return []


def _send_sos_whatsapp_async(sos_doc: dict, phones: list):
    """Send WhatsApp SOS alerts in background thread."""
    msg = format_sos_message(sos_doc)
    for phone in phones:
        send_whatsapp(phone, msg)


@sos_bp.route('/sos', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        name     = request.form.get('name', '').strip() or current_user.username
        location = request.form.get('location', '').strip()
        message  = request.form.get('message', '').strip()
        people   = request.form.get('people', '1').strip()
        lat      = request.form.get('lat', '')
        lng      = request.form.get('lng', '')
        sos_type = request.form.get('sos_type', 'General Emergency')
        # Optional: recipient phone entered on form
        recipient_phone = request.form.get('recipient_phone', '').strip()

        if not location or not message:
            flash('Location and message are required.', 'danger')
            return render_template('sos/submit.html')

        sos_doc = {
            'name':        name,
            'location':    location,
            'message':     message,
            'people':      people,
            'sos_type':    sos_type,
            'lat':         float(lat) if lat else None,
            'lng':         float(lng) if lng else None,
            'reported_by': current_user.username,
            'status':      'Active',
            'created_at':  datetime.utcnow().isoformat(),
            'resolved_at': None,
            'resolved_by': None,
        }

        sos_id = 'demo'
        try:
            db = get_mongo_db()
            result = db.sos_alerts.insert_one(sos_doc.copy())
            sos_id = str(result.inserted_id)
        except Exception:
            pass

        # ── Send WhatsApp to all registered users + optional recipient ──────
        phones = _get_all_phones()
        if recipient_phone and recipient_phone not in phones:
            phones.append(recipient_phone)

        if phones:
            t = threading.Thread(
                target=_send_sos_whatsapp_async,
                args=(sos_doc, phones),
                daemon=True
            )
            t.start()
            flash(f'🆘 SOS Alert sent! WhatsApp notifications sent to {len(phones)} contact(s).', 'success')
        else:
            flash('🆘 SOS Alert sent successfully! Help is on the way.', 'success')

        return redirect(url_for('sos.confirmation', sos_id=sos_id))

    return render_template('sos/submit.html')


@sos_bp.route('/sos/confirmation/<sos_id>')
@login_required
def confirmation(sos_id):
    sos = None
    try:
        db = get_mongo_db()
        sos = db.sos_alerts.find_one({'_id': ObjectId(sos_id)})
        if sos:
            sos['_id'] = str(sos['_id'])
    except Exception:
        pass
    return render_template('sos/confirmation.html', sos=sos, sos_id=sos_id)


@sos_bp.route('/sos/all')
@login_required
def all_sos():
    sos_list = []
    active_count = 0
    try:
        db = get_mongo_db()
        sos_list = list(db.sos_alerts.find().sort('created_at', -1).limit(100))
        for s in sos_list:
            s['_id'] = str(s['_id'])
        active_count = sum(1 for s in sos_list if s.get('status') == 'Active')
    except Exception:
        flash('Could not load SOS alerts.', 'warning')
    return render_template('sos/all.html', sos_list=sos_list, active_count=active_count)


@sos_bp.route('/sos/<sos_id>/resolve', methods=['POST'])
@login_required
def resolve(sos_id):
    try:
        db = get_mongo_db()
        db.sos_alerts.update_one(
            {'_id': ObjectId(sos_id)},
            {'$set': {
                'status':      'Resolved',
                'resolved_at': datetime.utcnow().isoformat(),
                'resolved_by': current_user.username,
            }}
        )
        flash('SOS marked as resolved.', 'success')
    except Exception:
        flash('Could not update SOS status.', 'danger')
    return redirect(url_for('sos.all_sos'))


@sos_bp.route('/api/sos/count')
@login_required
def sos_count():
    count = 0
    try:
        db = get_mongo_db()
        count = db.sos_alerts.count_documents({'status': 'Active'})
    except Exception:
        pass
    return jsonify({'count': count})
