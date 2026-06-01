"""
Disaster Analysis Agent
Analyzes a disaster report and returns type, severity, and risk score.
Uses Groq API (llama3) when available, falls back to rule-based logic.
"""
import os
import json
import re

try:
    from groq import Groq
    _groq = Groq(api_key=os.environ.get('GROQ_API_KEY', ''))
    GROQ_AVAILABLE = bool(os.environ.get('GROQ_API_KEY'))
except Exception:
    GROQ_AVAILABLE = False

SEVERITY_KEYWORDS = {
    'High':   ['flood', 'earthquake', 'tsunami', 'hurricane', 'tornado', 'wildfire', 'explosion', 'collapse'],
    'Medium': ['fire', 'landslide', 'storm', 'accident', 'chemical', 'gas leak'],
    'Low':    ['power outage', 'minor', 'small', 'low'],
}

DISASTER_TYPES = [
    'Flood', 'Earthquake', 'Fire', 'Tsunami', 'Hurricane', 'Tornado',
    'Landslide', 'Wildfire', 'Explosion', 'Chemical Spill', 'Gas Leak',
    'Storm', 'Accident', 'Other'
]


def _rule_based_analysis(description: str) -> dict:
    desc_lower = description.lower()

    # Detect type
    detected_type = 'Other'
    for dtype in DISASTER_TYPES:
        if dtype.lower() in desc_lower:
            detected_type = dtype
            break

    # Detect severity
    severity = 'Medium'
    risk_score = 5
    for level, keywords in SEVERITY_KEYWORDS.items():
        if any(kw in desc_lower for kw in keywords):
            severity = level
            break

    risk_map = {'High': 9, 'Medium': 6, 'Low': 3}
    risk_score = risk_map.get(severity, 5)

    return {
        'type': detected_type,
        'severity': severity,
        'risk_score': risk_score,
        'summary': f'{detected_type} detected. Severity: {severity}. Immediate attention required.'
    }


def analyze_disaster(location: str, description: str) -> dict:
    """
    Returns:
        {
            type: str,
            severity: 'High' | 'Medium' | 'Low',
            risk_score: int (1-10),
            summary: str
        }
    """
    if GROQ_AVAILABLE:
        try:
            prompt = f"""You are a disaster analysis AI agent.
Analyze the following disaster report and respond ONLY with valid JSON.

Location: {location}
Description: {description}

Respond with this exact JSON structure:
{{
  "type": "<disaster type>",
  "severity": "<High|Medium|Low>",
  "risk_score": <integer 1-10>,
  "summary": "<one sentence summary>"
}}"""
            response = _groq.chat.completions.create(
                model='llama3-8b-8192',
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.2,
                max_tokens=200,
            )
            text = response.choices[0].message.content.strip()
            # Extract JSON from response
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass

    return _rule_based_analysis(description)
