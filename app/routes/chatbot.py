"""
ARIA – AI Chatbot with rich FAQ + comprehensive Telugu content.
"""
import os
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

chatbot_bp = Blueprint('chatbot', __name__)

SYSTEM_PROMPT = """You are ARIA (Autonomous Response Intelligence Assistant), an expert AI for
the Disaster Response Coordination System. You provide detailed, accurate, life-saving information.
Rules:
- Give detailed, practical, actionable advice with bullet points
- Always mention emergency numbers (Police:100, Fire:101, Ambulance:108, NDRF:011-24363260)
- Be calm, authoritative, and compassionate
- Responses up to 400 words, well-organized"""

# ── English FAQ ───────────────────────────────────────────────────────────────
FAQ_EN = {
'flood': """🌊 **Flood Emergency Guide**
**Immediate Actions:**
• Move to higher ground immediately
• Never walk through moving water
• Do not drive through flooded roads
• Turn off electricity at main breaker
• Move valuables to upper floors

**During Flood:**
• Stay tuned to emergency broadcasts
• If trapped, go to roof and signal for help
• Avoid floodwater — may be contaminated

**After Flood:**
• Do not return until authorities declare safe
• Boil all drinking water
• Document damage for insurance

**Emergency:** 🚑 108 | 🚔 100 | NDRF: 011-24363260""",

'earthquake': """🏚️ **Earthquake Emergency Guide**
**During Shaking — DROP, COVER, HOLD ON:**
• DROP to hands and knees
• COVER under sturdy desk/table
• HOLD ON until shaking stops
• Stay away from windows and heavy furniture
• If outdoors: move away from buildings

**After Shaking:**
• Expect aftershocks
• Check for gas leaks — evacuate if detected
• Do not use elevators
• Call 108 for injuries

**Emergency:** 🚑 108 | 🚔 100 | NDRF: 011-24363260""",

'fire': """🔥 **Fire Emergency Guide**
• Call 101 immediately — give exact address
• Evacuate — do not use elevators
• Stay LOW to avoid smoke
• Close doors to slow fire spread
• Feel doors before opening — if hot, use another exit

**PASS for Fire Extinguisher:**
• Pull pin | Aim at base | Squeeze | Sweep

**Emergency:** 🚒 101 | 🚑 108""",

'cyclone': """🌀 **Cyclone Emergency Guide**
**Before:** Prepare 3-day kit, reinforce windows, know evacuation route
**During:** Stay indoors, away from windows, do not go out during eye
**After:** Wait for all-clear, avoid downed power lines, boil water

**Emergency:** 🚔 100 | 🚑 108 | IMD: 1800-180-1717""",

'tsunami': """🌊 **Tsunami Emergency Guide**
**Warning Signs:** Strong earthquake, ocean recedes, loud roaring sound
**Action:** Move INLAND to HIGH GROUND immediately — at least 30m above sea level
**Do not** wait to see the wave — multiple waves can come hours apart

**Emergency:** 🚔 100 | 🚑 108 | INCOIS: 040-23895000""",

'first aid': """🩺 **First Aid Quick Reference**
• **Bleeding:** Firm pressure, elevate limb, tourniquet if severe
• **Burns:** Cool running water 10-20 min, no ice/butter
• **Fractures:** Immobilize, do not straighten, call 108
• **CPR:** 30 compressions + 2 breaths, repeat
• **Choking:** 5 back blows + 5 abdominal thrusts
• **Shock:** Lay flat, elevate legs, keep warm, call 108

**Emergency:** 🚑 108""",

'preparedness': """🎒 **Emergency Kit (72-Hour)**
• Water: 1 gallon/person/day
• Non-perishable food
• First aid kit + medicines
• Torch + batteries
• Battery radio
• Important documents (waterproof bag)
• Cash, phone charger, whistle
• Know evacuation routes and meeting points""",

'mental health': """🧠 **Mental Health After Disaster**
**Normal reactions:** Shock, fear, sadness, anger, sleep problems
**Coping:** Connect with family, limit news, maintain routine, exercise
**Help children:** Reassure safety, maintain routine, answer questions honestly
**Seek help if:** Symptoms persist 4+ weeks, unable to function
**Helpline:** iCall: 9152987821 | Vandrevala: 1860-2662-345""",

'sos': """🆘 **How to Send SOS**
1. Click red SOS button (bottom-right of any page)
2. Select emergency type
3. Search your location or use GPS
4. Describe your situation
5. Click SEND SOS ALERT NOW
**Emergency:** 🚔 100 | 🚒 101 | 🚑 108 | NDRF: 011-24363260""",

'hello': """👋 **Hello! I'm ARIA**
I help with disaster safety, first aid, preparedness and system usage.
Ask me about: Flood, Earthquake, Fire, Cyclone, Tsunami, First Aid, SOS
**Emergency:** 🚔 100 | 🚒 101 | 🚑 108""",
}

# ── Telugu FAQ ────────────────────────────────────────────────────────────────
FAQ_TE = {
'వరద': """🌊 **వరద అత్యవసర మార్గదర్శకం**

**వెంటనే చేయవలసినవి:**
• వెంటనే ఎత్తైన ప్రదేశానికి వెళ్ళండి — ఆలస్యం చేయకండి
• నీటిలో నడవకండి — 6 అంగుళాల నీరు కూడా మిమ్మల్ని పడగొట్టవచ్చు
• వరద రోడ్లపై వాహనం నడపకండి
• విద్యుత్ మెయిన్ స్విచ్ ఆపివేయండి
• విలువైన వస్తువులు, పత్రాలు పై అంతస్తుకు తరలించండి

**వరద సమయంలో:**
• అత్యవసర ప్రసారాలు వినండి
• చిక్కుకుపోతే పైకప్పుపైకి వెళ్ళి సహాయం కోసం సంకేతాలు ఇవ్వండి
• వరద నీటిని తాకకండి — మురుగు కలిసి ఉండవచ్చు

**వరద తర్వాత:**
• అధికారులు సురక్షితమని ప్రకటించే వరకు తిరిగి వెళ్ళకండి
• తాగునీటిని మరిగించండి
• నష్టాన్ని ఫోటోలు తీసి నమోదు చేయండి

**అత్యవసర నంబర్లు:** 🚑 108 | 🚔 100 | NDRF: 011-24363260""",

'భూకంపం': """🏚️ **భూకంప అత్యవసర మార్గదర్శకం**

**కంపన సమయంలో — వంగు, కప్పుకో, పట్టుకో:**
• వెంటనే వంగి మోకాళ్ళపై కూర్చోండి
• బల్ల లేదా డెస్క్ కింద ఆశ్రయం తీసుకోండి
• కంపన ఆగే వరకు పట్టుకోండి
• కిటికీలు, బయటి గోడలకు దూరంగా ఉండండి
• బయట ఉంటే భవనాలు, చెట్ల నుండి దూరంగా వెళ్ళండి

**కంపన ఆగిన తర్వాత:**
• అఫ్టర్‌షాక్‌లు రావచ్చు — జాగ్రత్తగా ఉండండి
• గ్యాస్ లీక్ తనిఖీ చేయండి — వాసన వస్తే వెంటనే బయటకు వెళ్ళండి
• లిఫ్ట్ వాడకండి
• గాయాలకు 108 కి కాల్ చేయండి

**అత్యవసర నంబర్లు:** 🚑 108 | 🚔 100 | NDRF: 011-24363260""",

'అగ్ని': """🔥 **అగ్ని అత్యవసర మార్గదర్శకం**

**అగ్ని అంటుకుంటే:**
• వెంటనే 101 కి కాల్ చేయండి — ఖచ్చితమైన చిరునామా చెప్పండి
• వెంటనే బయటకు వెళ్ళండి — లిఫ్ట్ వాడకండి
• పొగ నుండి తప్పించుకోవడానికి వంగి నడవండి
• తలుపులు మూసివేయండి — అగ్ని వ్యాప్తి తగ్గుతుంది
• తలుపు తెరవడానికి ముందు వేడిగా ఉందా అని తనిఖీ చేయండి

**చిక్కుకుపోతే:**
• తలుపు సందులు బట్టలతో మూసివేయండి
• కిటికీ నుండి సహాయం కోసం సంకేతాలు ఇవ్వండి

**అగ్నిమాపక యంత్రం వాడటం (PASS):**
• పిన్ లాగండి | అడుగు భాగానికి గురిపెట్టండి | నొక్కండి | ఊపండి

**అత్యవసర నంబర్లు:** 🚒 101 | 🚑 108""",

'తుఫాను': """🌀 **తుఫాను అత్యవసర మార్గదర్శకం**

**తుఫాను ముందు:**
• వాతావరణ హెచ్చరికలు నిరంతరం వినండి
• 3 రోజుల నీరు, ఆహారం, మందులు సిద్ధంగా ఉంచుకోండి
• కిటికీలు, తలుపులు బలపరచండి
• ఖాళీ చేయవలసిన మార్గం తెలుసుకోండి
• ఫోన్లు, వాహనాలు చార్జ్ చేయండి

**తుఫాను సమయంలో:**
• ఇంట్లో ఉండండి — బలమైన గదిలో
• కిటికీలు, గాజు తలుపులకు దూరంగా ఉండండి
• తుఫాను కన్ను సమయంలో బయటకు వెళ్ళకండి — తుఫాను మళ్ళీ వస్తుంది

**తుఫాను తర్వాత:**
• అధికారిక అనుమతి వచ్చే వరకు బయటకు వెళ్ళకండి
• పడిపోయిన విద్యుత్ తీగలకు దూరంగా ఉండండి
• తాగునీటిని మరిగించండి

**అత్యవసర నంబర్లు:** 🚔 100 | 🚑 108 | IMD: 1800-180-1717""",

'సునామి': """🌊 **సునామి అత్యవసర మార్గదర్శకం**

**హెచ్చరిక సంకేతాలు:**
• తీవ్రమైన భూకంపం
• సముద్రం వెనక్కి తగ్గడం
• సముద్రం నుండి బిగ్గరగా శబ్దం
• అధికారిక సునామి హెచ్చరిక

**వెంటనే చేయవలసినవి:**
• లోపలికి మరియు ఎత్తైన ప్రదేశానికి వెళ్ళండి
• కనీసం 30 మీటర్ల ఎత్తుకు వెళ్ళండి
• అలలు చూసే వరకు ఆగకండి — పరిగెత్తలేరు
• అధికారిక అనుమతి వచ్చే వరకు తిరిగి రాకండి

**అత్యవసర నంబర్లు:** 🚔 100 | 🚑 108 | INCOIS: 040-23895000""",

'ప్రథమ చికిత్స': """🩺 **ప్రథమ చికిత్స త్వరిత మార్గదర్శకం**

**రక్తస్రావం:**
• శుభ్రమైన గుడ్డతో గట్టిగా నొక్కండి
• గుడ్డ తీయకండి — పైన మరొకటి వేయండి
• గాయపడిన అవయవాన్ని గుండె కంటే పైకి ఎత్తండి

**కాలిన గాయాలు:**
• 10-20 నిమిషాలు చల్లని నీటితో కడగండి
• మంచు, వెన్న, పేస్ట్ వాడకండి
• తీవ్రమైన కాలిన గాయాలకు 108 కి కాల్ చేయండి

**ఎముక విరిగితే:**
• కదలకుండా స్థిరపరచండి
• నేరుగా చేయడానికి ప్రయత్నించకండి
• 108 కి కాల్ చేయండి

**CPR (గుండె పని చేయకపోతే):**
• 30 సార్లు గుండె నొక్కండి (వేగంగా, గట్టిగా)
• 2 సార్లు శ్వాస ఇవ్వండి
• సహాయం వచ్చే వరకు కొనసాగించండి

**గొంతు అడ్డుపడితే:**
• 5 సార్లు వీపు మీద కొట్టండి
• 5 సార్లు పొట్ట నొక్కండి (Heimlich)

**అత్యవసర నంబర్లు:** 🚑 108""",

'సిద్ధత': """🎒 **విపత్తు సిద్ధత మార్గదర్శకం**

**అత్యవసర కిట్ (72 గంటలకు):**
• నీరు: ఒక్కో వ్యక్తికి రోజుకు 1 లీటర్ (3 రోజులకు)
• ఆహారం: పాడవని వస్తువులు (డబ్బాల ఆహారం, బిస్కెట్లు)
• ప్రథమ చికిత్స పెట్టె + మందులు
• టార్చ్ + అదనపు బ్యాటరీలు
• బ్యాటరీ రేడియో
• ముఖ్యమైన పత్రాల కాపీలు (వాటర్‌ప్రూఫ్ బ్యాగ్‌లో)
• నగదు, ఫోన్ చార్జర్, విజిల్

**కుటుంబ అత్యవసర ప్రణాళిక:**
• రెండు సమావేశ స్థలాలు నిర్ణయించుకోండి
• ఖాళీ చేయవలసిన మార్గాలు తెలుసుకోండి
• అందరికీ అత్యవసర నంబర్లు తెలియాలి
• సంవత్సరానికి రెండుసార్లు అభ్యాసం చేయండి

**అత్యవసర నంబర్లు:** 🚔 100 | 🚒 101 | 🚑 108""",

'మానసిక ఆరోగ్యం': """🧠 **విపత్తు తర్వాత మానసిక ఆరోగ్యం**

**సాధారణ ప్రతిచర్యలు:**
• షాక్, భయం, దుఃఖం, కోపం
• నిద్ర సమస్యలు, ఏకాగ్రత కష్టం
• తలనొప్పి, అలసట

**సమాళించుకోవడానికి:**
• కుటుంబం, స్నేహితులతో మాట్లాడండి — ఒంటరిగా ఉండకండి
• వార్తలు, సోషల్ మీడియా తక్కువగా చూడండి
• రోజువారీ దినచర్య కొనసాగించండి
• తగినంత నిద్ర, ఆహారం తీసుకోండి

**పిల్లలకు సహాయం:**
• వారు సురక్షితంగా ఉన్నారని భరోసా ఇవ్వండి
• సాధారణ దినచర్య కొనసాగించండి
• వారి ప్రశ్నలకు నిజాయితీగా సమాధానం ఇవ్వండి

**సహాయ నంబర్లు:** iCall: 9152987821 | Vandrevala: 1860-2662-345""",

'SOS': """🆘 **SOS అలర్ట్ పంపడం ఎలా**

**ఈ సిస్టమ్ ఉపయోగించి:**
1. ఎర్రని SOS బటన్ నొక్కండి (పేజీ కుడి దిగువ మూల)
2. అత్యవసర రకం ఎంచుకోండి:
   • వైద్య అత్యవసరం | చిక్కుకుపోవడం | అగ్ని | వరద | భూకంపం
3. మీ స్థానం వెతకండి లేదా GPS వాడండి
4. సహాయం అవసరమైన వ్యక్తుల సంఖ్య నమోదు చేయండి
5. మీ పరిస్థితి వివరించండి
6. SOS అలర్ట్ పంపండి బటన్ నొక్కండి

**తర్వాత ఏమి జరుగుతుంది:**
• అత్యవసర సమన్వయకర్తలకు వెంటనే తెలియజేయబడుతుంది
• సమీప రెస్క్యూ బృందం పంపబడుతుంది
• మీకు నిర్ధారణ ID అందుతుంది

**అత్యవసర నంబర్లు:** 🚔 100 | 🚒 101 | 🚑 108 | NDRF: 011-24363260""",

'నమస్కారం': """👋 **నమస్కారం! నేను ARIA**

నేను మీ **స్వయంచాలిత విపత్తు స్పందన సహాయకుడిని**.

**నేను సహాయం చేయగలిగే విషయాలు:**
🌊 **విపత్తులు** — వరద, భూకంపం, తుఫాను, అగ్ని, సునామి
🩺 **ప్రథమ చికిత్స** — రక్తస్రావం, కాలిన గాయాలు, CPR
🎒 **సిద్ధత** — అత్యవసర కిట్, కుటుంబ ప్రణాళిక
📱 **సిస్టమ్ సహాయం** — నివేదికలు, SOS, మ్యాప్
🧠 **మానసిక ఆరోగ్యం** — విపత్తు తర్వాత సహాయం

**ప్రయత్నించండి:** "వరద సమయంలో ఏమి చేయాలి?" లేదా "CPR ఎలా చేయాలి?"

**అత్యవసర నంబర్లు:**
🚔 పోలీసు: **100** | 🚒 అగ్నిమాపక: **101** | 🚑 అంబులెన్స్: **108**""",

'హలో': """👋 నమస్కారం! నేను ARIA.
విపత్తు భద్రత, ప్రథమ చికిత్స మరియు అత్యవసర సేవల గురించి సహాయం చేస్తాను.
🚔 పోలీసు: 100 | 🚒 అగ్నిమాపక: 101 | 🚑 అంబులెన్స్: 108""",

'భూకంపం': """🏚️ **భూకంప అత్యవసర మార్గదర్శకం**
• వంగి, కప్పుకుని, పట్టుకోండి
• కిటికీలకు దూరంగా ఉండండి
• భవనాల నుండి బయటకు వెళ్ళండి
• అఫ్టర్‌షాక్‌లకు సిద్ధంగా ఉండండి
• గాయాలకు 108 కి కాల్ చేయండి""",
}


# ── FAQ lookup ────────────────────────────────────────────────────────────────
def _faq_response(text: str, lang: str = 'en') -> str:
    # Telugu keywords → Telugu responses
    if lang == 'te' or any(ord(c) > 3000 for c in text):
        te_keys = [
            ('వరద',            FAQ_TE['వరద']),
            ('భూకంపం',         FAQ_TE['భూకంపం']),
            ('అగ్ని',           FAQ_TE['అగ్ని']),
            ('తుఫాను',         FAQ_TE['తుఫాను']),
            ('సునామి',         FAQ_TE['సునామి']),
            ('ప్రథమ చికిత్స',  FAQ_TE['ప్రథమ చికిత్స']),
            ('సిద్ధత',         FAQ_TE['సిద్ధత']),
            ('మానసిక',         FAQ_TE['మానసిక ఆరోగ్యం']),
            ('SOS',            FAQ_TE['SOS']),
            ('సహాయం',          FAQ_TE['SOS']),
            ('నమస్కారం',       FAQ_TE['నమస్కారం']),
            ('హలో',            FAQ_TE['హలో']),
            ('flood',          FAQ_TE['వరద']),
            ('earthquake',     FAQ_TE['భూకంపం']),
            ('fire',           FAQ_TE['అగ్ని']),
            ('cyclone',        FAQ_TE['తుఫాను']),
            ('first aid',      FAQ_TE['ప్రథమ చికిత్స']),
        ]
        text_lower = text.lower()
        for key, val in te_keys:
            if key.lower() in text_lower or key in text:
                return val
        return FAQ_TE['నమస్కారం']

    # English keywords
    text_lower = text.lower()
    priority = [
        'first aid', 'mental health', 'preparedness',
        'tsunami', 'cyclone', 'earthquake', 'flood',
        'fire', 'sos', 'hello', 'hi',
    ]
    for key in priority:
        if key in text_lower:
            return FAQ_EN.get(key, '')

    return """I'm ARIA. Ask me about:
• 🌊 Flood, Earthquake, Fire, Cyclone, Tsunami
• 🩺 First Aid — CPR, bleeding, burns
• 🎒 Preparedness — emergency kits
• 🆘 SOS — how to send alerts
**Emergency:** 🚔 100 | 🚒 101 | 🚑 108"""


# ── Groq AI ───────────────────────────────────────────────────────────────────
def _groq_chat(messages: list, system_extra: str = '') -> str:
    api_key = os.environ.get('GROQ_API_KEY', '').strip()
    if not api_key:
        return None
    try:
        from groq import Groq
        resp = Groq(api_key=api_key).chat.completions.create(
            model='llama3-8b-8192',
            messages=[{'role': 'system', 'content': SYSTEM_PROMPT + system_extra}] + messages,
            temperature=0.4,
            max_tokens=500,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return None


# ── Routes ────────────────────────────────────────────────────────────────────
@chatbot_bp.route('/chatbot')
@login_required
def index():
    groq_key = bool(os.environ.get('GROQ_API_KEY', '').strip())
    return render_template('chatbot/index.html', groq_key=groq_key)


@chatbot_bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data    = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])
    lang    = data.get('lang', 'en')

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    system_lang = ''
    if lang == 'te':
        system_lang = (
            '\n\nCRITICAL: Respond ENTIRELY in Telugu (తెలుగు) script. '
            'Use simple clear Telugu. '
            'Emergency numbers: పోలీసు:100, అగ్నిమాపక:101, అంబులెన్స్:108'
        )

    messages = history[-12:] + [{'role': 'user', 'content': message}]
    reply    = _groq_chat(messages, system_lang) or _faq_response(message, lang)

    # Optional: send to WhatsApp if requested
    share_phone = data.get('share_phone', '').strip()
    if share_phone:
        from ..whatsapp import send_whatsapp, format_chat_message
        import threading
        threading.Thread(
            target=send_whatsapp,
            args=(share_phone, format_chat_message(current_user.username, message, reply)),
            daemon=True
        ).start()

    return jsonify({
        'reply':      reply,
        'timestamp':  datetime.utcnow().strftime('%H:%M'),
        'ai_powered': bool(os.environ.get('GROQ_API_KEY')),
    })
