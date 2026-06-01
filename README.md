# Autonomous Disaster Response Coordination System

> AI Agents to Analyze, Allocate and Alert

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Frontend   | Flask, Bootstrap 5, Leaflet.js    |
| Databases  | SQLite3 (users), MongoDB (reports)|
| AI Model   | Groq API / Ollama (Llama 3.2)     |
| Security   | Password Hashing, OTP (2FA)       |
| Maps       | Leaflet.js, OpenStreetMap         |

## Features

- **Secure Login with 2FA (OTP)** – username/password + 6-digit OTP
- **Disaster Reporting** – submit reports with location, description, and map pin
- **4 AI Agents** – Analysis, Resource Allocation, Route Optimization, Emergency Alert
- **Live Map** – Leaflet.js with OpenStreetMap showing all active incidents
- **Real-time Dashboard** – stats, recent reports, latest alert

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env
# Edit .env – set SECRET_KEY, MONGO_URI, and optionally GROQ_API_KEY
```

### 3. Start MongoDB

Make sure MongoDB is running locally on port 27017, or update `MONGO_URI` in `.env`.

### 4. Seed sample data (optional)

```bash
python seed_db.py
```

### 5. Run the app

```bash
python run.py
```

Open http://localhost:5000

### 6. Create your first user

Go to http://localhost:5000/register

## AI Agents

| Agent | Function |
|-------|----------|
| Disaster Analysis Agent | Detects type, severity (High/Medium/Low), risk score 1-10 |
| Resource Allocation Agent | Allocates rescue teams, ambulances, food packets from inventory |
| Route Optimization Agent | Finds safest route from disaster site to shelter |
| Emergency Alert Agent | Generates public alerts stored in MongoDB |

When `GROQ_API_KEY` is set, the Analysis Agent uses **Llama 3** via Groq API.
Without it, a rule-based fallback is used automatically.

## Database Structure

### SQLite3 – `users.db`
```
users (id, username, password [hashed], email, phone)
```

### MongoDB – `disaster_response`
```
disaster_reports  { location, type, severity, risk_score, status, timestamp, lat, lng, ... }
resources         { _id: 'inventory', ambulances, rescue_teams, food_packets, helicopters }
alerts            { location, disaster_type, severity, message, status, created_at }
allocations       { report_id, severity, allocated, insufficient }
```

## Project Structure

```
pp/
├── app/
│   ├── __init__.py          # App factory
│   ├── database.py          # SQLite + MongoDB helpers
│   ├── models.py            # User model (Flask-Login)
│   ├── otp.py               # In-memory OTP store
│   ├── agents/
│   │   ├── analysis_agent.py
│   │   ├── resource_agent.py
│   │   ├── route_agent.py
│   │   └── alert_agent.py
│   └── routes/
│       ├── auth.py
│       ├── dashboard.py
│       ├── reports.py
│       ├── resources.py
│       ├── alerts.py
│       ├── map_view.py
│       └── api.py
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   ├── reports/
│   ├── resources/
│   ├── alerts/
│   └── map/
├── static/css/style.css
├── run.py
├── seed_db.py
├── requirements.txt
└── .env.example
```
