from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from ..database import get_mongo_db
from ..models import User
from ..otp import generate_and_send_otp, verify_otp
from .. import login_manager

auth_bp = Blueprint('auth', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


def _flash_otp_result(result: dict, email: str):
    if result['method'] == 'email':
        parts  = email.split('@')
        masked = parts[0][:2] + '***@' + parts[1] if len(parts) == 2 else '***'
        flash(f'OTP sent to your email <strong>{masked}</strong>.', 'success')
    else:
        flash(
            f'Email not configured. Your OTP is: <strong>{result["otp"]}</strong>',
            'warning'
        )


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        row = User.get_by_username(username)
        if not row or not check_password_hash(row['password'], password):
            flash('Invalid username or password.', 'danger')
            return render_template('auth/login.html')

        email  = row.get('email', '')
        result = generate_and_send_otp(username, email=email)

        session['pending_user'] = username
        _flash_otp_result(result, email)
        return redirect(url_for('auth.verify_otp_view'))

    return render_template('auth/login.html')


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp_view():
    if 'pending_user' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        otp      = request.form.get('otp', '').strip()
        username = session['pending_user']

        if verify_otp(username, otp):
            row  = User.get_by_username(username)
            user = User(row['_id'], row['username'], row['email'], row.get('phone'))
            login_user(user)
            session.pop('pending_user', None)
            flash('Login successful. Welcome back!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')

    return render_template('auth/verify_otp.html')


@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    username = session.get('pending_user')
    if not username:
        return redirect(url_for('auth.login'))

    row = User.get_by_username(username)
    if not row:
        return redirect(url_for('auth.login'))

    email  = row.get('email', '')
    result = generate_and_send_otp(username, email=email)
    _flash_otp_result(result, email)
    return redirect(url_for('auth.verify_otp_view'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email    = request.form.get('email', '').strip()
        phone    = request.form.get('phone', '').strip()

        if not username or not password or not email:
            flash('Username, email and password are required.', 'danger')
            return render_template('auth/register.html')

        hashed = generate_password_hash(password)
        try:
            db = get_mongo_db()
            db.users.insert_one({
                'username': username,
                'password': hashed,
                'email':    email,
                'phone':    phone,
            })
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception:
            flash('Username or email already exists.', 'danger')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# ── Voice test page (no login required for debugging) ────────────────────────
@auth_bp.route('/voice-test')
def voice_test():
    from flask import render_template_string
    with open('templates/voice_test.html', encoding='utf-8') as f:
        return f.read()
