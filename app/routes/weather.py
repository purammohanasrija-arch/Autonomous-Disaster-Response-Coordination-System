"""
Weather route — OpenWeatherMap API (current + 5-day forecast).
API key: stored in OPENWEATHER_APIKEY env var.
"""
import os
import requests
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

weather_bp = Blueprint('weather', __name__)

OWM_KEY = None   # loaded lazily

def _key():
    return os.environ.get('OPENWEATHER_APIKEY', '').strip()

# ── Weather condition → icon + color ─────────────────────────────────────────
ICON_MAP = {
    '01': ('bi-sun-fill',               'text-warning',   'Clear Sky'),
    '02': ('bi-cloud-sun-fill',         'text-warning',   'Few Clouds'),
    '03': ('bi-clouds-fill',            'text-secondary', 'Scattered Clouds'),
    '04': ('bi-clouds-fill',            'text-secondary', 'Overcast'),
    '09': ('bi-cloud-drizzle-fill',     'text-info',      'Drizzle'),
    '10': ('bi-cloud-rain-fill',        'text-primary',   'Rain'),
    '11': ('bi-cloud-lightning-rain-fill','text-danger',  'Thunderstorm'),
    '13': ('bi-cloud-snow-fill',        'text-info',      'Snow'),
    '50': ('bi-cloud-fog2-fill',        'text-secondary', 'Mist / Fog'),
}

HIGH_RISK_IDS = set(range(200, 233))   # thunderstorm
HIGH_RISK_IDS.update(range(502, 532))  # heavy rain / extreme
HIGH_RISK_IDS.update(range(600, 623))  # snow

SAFETY_TIPS = {
    'Thunderstorm': '⛈️ Thunderstorm active. Stay indoors. Unplug electronics. Avoid trees.',
    'Rain':         '🌧️ Heavy rain possible. Risk of flooding. Avoid low-lying areas.',
    'Snow':         '❄️ Snow conditions. Roads may be icy. Drive carefully.',
    'Drizzle':      '🌦️ Drizzle expected. Carry an umbrella.',
}

def _icon(code: str):
    prefix = code[:2] if code else '01'
    return ICON_MAP.get(prefix, ('bi-question-circle', 'text-muted', 'Unknown'))


def _geocode(location: str):
    """Convert city name → lat/lon using OWM Geocoding API."""
    key = _key()
    if not key:
        return None, None, location
    try:
        r = requests.get(
            'https://api.openweathermap.org/geo/1.0/direct',
            params={'q': location, 'limit': 1, 'appid': key},
            timeout=8
        )
        data = r.json()
        if data:
            d = data[0]
            name = f"{d.get('name','')}, {d.get('state','')}, {d.get('country','')}".strip(', ')
            return float(d['lat']), float(d['lon']), name
    except Exception:
        pass
    return None, None, location


def _current_weather(lat: float, lon: float) -> dict:
    key = _key()
    if not key:
        return {}
    try:
        r = requests.get(
            'https://api.openweathermap.org/data/2.5/weather',
            params={
                'lat': lat, 'lon': lon,
                'appid': key, 'units': 'metric',
            },
            timeout=8
        )
        return r.json()
    except Exception:
        return {}


def _forecast(lat: float, lon: float) -> dict:
    key = _key()
    if not key:
        return {}
    try:
        r = requests.get(
            'https://api.openweathermap.org/data/2.5/forecast',
            params={
                'lat': lat, 'lon': lon,
                'appid': key, 'units': 'metric', 'cnt': 40,
            },
            timeout=8
        )
        return r.json()
    except Exception:
        return {}


def _wind_dir(deg):
    if deg is None:
        return '—'
    dirs = ['N','NE','E','SE','S','SW','W','NW']
    return dirs[round(deg / 45) % 8]


@weather_bp.route('/weather')
@login_required
def index():
    return render_template('weather/index.html', weather=None, location='', error=None)


@weather_bp.route('/weather/search')
@login_required
def search():
    location = request.args.get('location', '').strip()
    if not location:
        return render_template('weather/index.html', weather=None, location='',
                               error='Please enter a location.')

    if not _key():
        return render_template('weather/index.html', weather=None, location=location,
                               error='OpenWeatherMap API key not configured. Add OPENWEATHER_APIKEY to .env')

    lat, lon, display_name = _geocode(location)
    if lat is None:
        return render_template('weather/index.html', weather=None, location=location,
                               error=f'Location "{location}" not found. Try a city name like "Mumbai".')

    cur = _current_weather(lat, lon)
    if not cur or cur.get('cod') != 200:
        return render_template('weather/index.html', weather=None, location=location,
                               error='Weather data unavailable. Please try again.')

    fc_raw = _forecast(lat, lon)

    # ── Current conditions ────────────────────────────────────────────────
    weather_id   = cur.get('weather', [{}])[0].get('id', 800)
    icon_code    = cur.get('weather', [{}])[0].get('icon', '01d')
    desc_raw     = cur.get('weather', [{}])[0].get('description', '').title()
    icon, color, _ = _icon(icon_code)
    high_risk    = weather_id in HIGH_RISK_IDS
    safety_tip   = ''
    for k, v in SAFETY_TIPS.items():
        if k.lower() in desc_raw.lower():
            safety_tip = v
            break

    main  = cur.get('main', {})
    wind  = cur.get('wind', {})
    sys   = cur.get('sys', {})
    vis   = cur.get('visibility', None)

    # ── 5-day forecast (one entry per day at noon) ────────────────────────
    forecast = []
    seen_days = set()
    for item in fc_raw.get('list', []):
        day = item['dt_txt'][:10]
        if day in seen_days:
            continue
        seen_days.add(day)
        ic = item.get('weather', [{}])[0].get('icon', '01d')
        fi, fc, _ = _icon(ic)
        forecast.append({
            'date':    day,
            'desc':    item.get('weather', [{}])[0].get('description', '').title(),
            'icon':    fi,
            'color':   fc,
            'max':     round(item['main']['temp_max'], 1),
            'min':     round(item['main']['temp_min'], 1),
            'humidity':item['main']['humidity'],
            'wind':    round(item['wind']['speed'] * 3.6, 1),  # m/s → km/h
            'rain':    round(item.get('rain', {}).get('3h', 0), 1),
        })
        if len(forecast) >= 7:
            break

    # ── Hourly next 8 entries ─────────────────────────────────────────────
    hourly = []
    for item in fc_raw.get('list', [])[:8]:
        hourly.append({
            'time': item['dt_txt'][11:16],
            'temp': round(item['main']['temp'], 1),
            'rain': round(item.get('rain', {}).get('3h', 0), 1),
            'desc': item.get('weather', [{}])[0].get('description', '').title(),
        })

    import math
    sunrise = cur.get('sys', {}).get('sunrise')
    sunset  = cur.get('sys', {}).get('sunset')

    def fmt_time(ts):
        if not ts:
            return '—'
        from datetime import datetime, timezone
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%H:%M')

    weather = {
        'location':   display_name,
        'lat':        lat,
        'lon':        lon,
        'temp':       round(main.get('temp', 0), 1),
        'feels_like': round(main.get('feels_like', 0), 1),
        'temp_min':   round(main.get('temp_min', 0), 1),
        'temp_max':   round(main.get('temp_max', 0), 1),
        'humidity':   main.get('humidity'),
        'pressure':   main.get('pressure'),
        'visibility': round(vis / 1000, 1) if vis else None,
        'wind_speed': round(wind.get('speed', 0) * 3.6, 1),  # m/s → km/h
        'wind_dir':   _wind_dir(wind.get('deg')),
        'wind_gust':  round(wind.get('gust', 0) * 3.6, 1) if wind.get('gust') else None,
        'clouds':     cur.get('clouds', {}).get('all'),
        'rain_1h':    round(cur.get('rain', {}).get('1h', 0), 1),
        'desc':       desc_raw,
        'icon':       icon,
        'color':      color,
        'high_risk':  high_risk,
        'safety_tip': safety_tip,
        'sunrise':    fmt_time(sunrise),
        'sunset':     fmt_time(sunset),
        'country':    sys.get('country', ''),
        'forecast':   forecast,
        'hourly':     hourly,
        # Google Maps link
        'gmaps_url':  f'https://maps.google.com/maps?q={lat},{lon}&z=12',
    }

    return render_template('weather/index.html', weather=weather, location=location, error=None)


@weather_bp.route('/api/weather')
@login_required
def api_weather():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    if not lat or not lon:
        return jsonify({'error': 'lat and lon required'}), 400
    cur = _current_weather(lat, lon)
    if not cur or cur.get('cod') != 200:
        return jsonify({'error': 'unavailable'}), 503
    icon_code = cur.get('weather', [{}])[0].get('icon', '01d')
    icon, _, desc = _icon(icon_code)
    weather_id = cur.get('weather', [{}])[0].get('id', 800)
    return jsonify({
        'temp':      round(cur['main']['temp'], 1),
        'humidity':  cur['main']['humidity'],
        'wind':      round(cur['wind']['speed'] * 3.6, 1),
        'desc':      cur['weather'][0]['description'].title(),
        'icon':      icon,
        'high_risk': weather_id in HIGH_RISK_IDS,
    })
