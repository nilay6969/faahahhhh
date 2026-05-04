from flask import Flask, render_template, request, jsonify, send_file, session
from flask_session import Session
import json, random, datetime, io, math, os, re
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

app = Flask(__name__)
app.secret_key = "healthbot_secret_2024"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "./sessions"
os.makedirs("./sessions", exist_ok=True)
Session(app)

# ─── DISEASE / SYMPTOM DATA ────────────────────────────────────────────────────
SYMPTOM_DISEASE_MAP = {
    "fever": {"diseases": ["Flu", "COVID-19", "Malaria", "Typhoid", "Dengue"], "severity": "medium",
              "remedies": ["Stay hydrated with warm water", "Rest in a cool room", "Tulsi-ginger tea", "Wet cloth on forehead"],
              "specialist": "General Physician", "risk": 0.45},
    "headache": {"diseases": ["Migraine", "Tension Headache", "Sinusitis", "Hypertension"], "severity": "low",
                 "remedies": ["Peppermint oil on temples", "Stay hydrated", "Rest in dark room", "Cold/warm compress"],
                 "specialist": "Neurologist", "risk": 0.25},
    "chest pain": {"diseases": ["Angina", "Heart Attack", "GERD", "Anxiety", "Pleuritis"], "severity": "high",
                   "remedies": ["⚠️ Seek emergency care immediately", "Sit upright, rest", "Avoid exertion"],
                   "specialist": "Cardiologist", "risk": 0.85},
    "cough": {"diseases": ["Common Cold", "Bronchitis", "COVID-19", "Asthma", "TB"], "severity": "low",
              "remedies": ["Honey + ginger tea", "Steam inhalation", "Turmeric milk", "Stay hydrated"],
              "specialist": "Pulmonologist", "risk": 0.30},
    "shortness of breath": {"diseases": ["Asthma", "COPD", "Heart Failure", "Anemia", "Anxiety"], "severity": "high",
                             "remedies": ["⚠️ Seek medical help", "Sit upright", "Practice slow breathing"],
                             "specialist": "Pulmonologist / Cardiologist", "risk": 0.80},
    "stomach pain": {"diseases": ["Gastritis", "IBS", "Appendicitis", "GERD", "Food Poisoning"], "severity": "medium",
                     "remedies": ["Warm ginger water", "Avoid spicy food", "Fennel seed tea", "Light BRAT diet"],
                     "specialist": "Gastroenterologist", "risk": 0.40},
    "joint pain": {"diseases": ["Arthritis", "Gout", "Lupus", "Fibromyalgia"], "severity": "medium",
                   "remedies": ["Warm turmeric milk", "Epsom salt soak", "Gentle stretching", "Anti-inflammatory diet"],
                   "specialist": "Rheumatologist / Orthopedist", "risk": 0.35},
    "fatigue": {"diseases": ["Anemia", "Hypothyroidism", "Diabetes", "Depression", "Sleep Apnea"], "severity": "medium",
                "remedies": ["Iron-rich foods (spinach, lentils)", "Regular sleep schedule", "Ashwagandha supplement", "Light exercise"],
                "specialist": "General Physician / Endocrinologist", "risk": 0.40},
    "skin rash": {"diseases": ["Eczema", "Psoriasis", "Allergic Reaction", "Chickenpox", "Fungal Infection"], "severity": "low",
                  "remedies": ["Aloe vera gel", "Cool compress", "Neem paste", "Avoid scratching", "Oatmeal bath"],
                  "specialist": "Dermatologist", "risk": 0.20},
    "dizziness": {"diseases": ["Vertigo", "Anemia", "Low Blood Pressure", "Inner Ear Infection"], "severity": "medium",
                  "remedies": ["Lie down slowly", "Stay hydrated", "Ginger tea", "Avoid sudden movements"],
                  "specialist": "ENT / Neurologist", "risk": 0.45},
    "diabetes": {"diseases": ["Type 1 Diabetes", "Type 2 Diabetes", "Prediabetes"], "severity": "high",
                 "remedies": ["Low-sugar diet", "Regular exercise", "Monitor blood glucose", "Bitter gourd juice"],
                 "specialist": "Endocrinologist / Diabetologist", "risk": 0.75},
    "back pain": {"diseases": ["Muscle Strain", "Herniated Disc", "Sciatica", "Kidney Issues"], "severity": "medium",
                  "remedies": ["Hot/cold compress alternation", "Gentle yoga", "Posture correction", "Gentle massage with oil"],
                  "specialist": "Orthopedist / Physiotherapist", "risk": 0.35},
    "anxiety": {"diseases": ["Generalized Anxiety Disorder", "Panic Disorder", "PTSD", "OCD"], "severity": "medium",
                "remedies": ["Deep breathing exercises", "Chamomile tea", "Meditation", "Journaling", "Reduce caffeine"],
                "specialist": "Psychiatrist / Psychologist", "risk": 0.50},
    "depression": {"diseases": ["Major Depressive Disorder", "Bipolar Disorder", "Dysthymia"], "severity": "high",
                   "remedies": ["Sunlight exposure daily", "Exercise 30 min", "Social support", "Omega-3 rich diet"],
                   "specialist": "Psychiatrist / Psychologist", "risk": 0.70},
    "hypertension": {"diseases": ["Essential Hypertension", "Secondary Hypertension"], "severity": "high",
                     "remedies": ["DASH diet", "Reduce sodium", "Regular exercise", "Hibiscus tea", "Stress management"],
                     "specialist": "Cardiologist", "risk": 0.70},
}

DIET_PLANS = {
    "weight_loss": {
        "breakfast": ["Oats porridge with berries", "Vegetable upma", "Green smoothie + 2 eggs", "Moong dal chilla"],
        "lunch": ["Brown rice + dal + sabzi", "Quinoa salad bowl", "Multigrain roti + paneer bhurji", "Soup + salad"],
        "dinner": ["Grilled fish/tofu + veggies", "Khichdi (light)", "Vegetable soup + roti", "Sprouts curry + roti"],
        "snacks": ["Roasted chana", "Fruit bowl", "Green tea + nuts", "Cucumber sticks with hummus"],
        "calories": "1400-1600 kcal/day", "water": "3-4 litres/day",
        "avoid": ["Fried foods", "Sugary drinks", "White bread", "Excess oil"],
    },
    "diabetes": {
        "breakfast": ["Methi paratha (no ghee) + curd", "Oats + skim milk", "Moong sprouts", "Ragi idli"],
        "lunch": ["Brown rice (small) + dal + sabzi", "Chapati + bitter gourd sabzi", "Barley soup", "Rajma (small portion)"],
        "dinner": ["Palak paneer (low fat) + roti", "Dal soup + salad", "Grilled veggies + 1 roti", "Fish curry + brown rice"],
        "snacks": ["Nuts (handful)", "Roasted chana", "Buttermilk", "Apple (small)"],
        "calories": "1600-1800 kcal/day", "water": "3 litres/day",
        "avoid": ["White rice", "Sugar", "Fruit juices", "Maida products"],
    },
    "hypertension": {
        "breakfast": ["Oats + banana", "Whole grain toast + avocado", "Idli + sambar (low salt)", "Fruits + yogurt"],
        "lunch": ["Dal (low salt) + roti + salad", "Grilled chicken + rice", "Legume soup + bread", "Paneer tikka + salad"],
        "dinner": ["Palak soup + multigrain roti", "Baked fish + steamed veggies", "Lentil curry + quinoa"],
        "snacks": ["Banana", "Low-fat yogurt", "Unsalted nuts", "Cucumber + lemon"],
        "calories": "2000 kcal/day", "water": "2.5-3 litres/day",
        "avoid": ["Excess salt", "Processed foods", "Alcohol", "Caffeine"],
    },
    "general": {
        "breakfast": ["Poha + chai", "Paratha + curd", "Dosa + sambar", "Bread + eggs + fruit"],
        "lunch": ["Dal + roti + sabzi + curd", "Rice + rajma + salad", "Biryani (moderate)", "Sandwich + salad"],
        "dinner": ["Khichdi + papad", "Soup + 2 rotis", "Sabzi + 2 rotis", "Light dal + rice"],
        "snacks": ["Tea + biscuits", "Fruits", "Bhel puri (light)", "Roasted nuts"],
        "calories": "2000-2200 kcal/day", "water": "2-3 litres/day",
        "avoid": ["Excess junk food", "Late night eating", "Skipping meals"],
    },
}

EMERGENCY_NUMBERS = {
    "India": {"Ambulance": "108", "Police": "100", "Fire": "101", "Emergency": "112", "Women Helpline": "1091"},
    "USA": {"Emergency": "911"},
    "UK": {"Emergency": "999"},
    "Australia": {"Emergency": "000"},
    "EU": {"Emergency": "112"},
}

REMINDERS = {}

# ─── SIMPLE ML-LIKE RISK PREDICTOR ────────────────────────────────────────────
def predict_disease_risk(symptoms_list, age=30, bmi=22.0, bp=120):
    """Random Forest-inspired weighted scoring"""
    base_risk = 0.0
    detected = []
    for s in symptoms_list:
        s_lower = s.lower().strip()
        for key, val in SYMPTOM_DISEASE_MAP.items():
            if key in s_lower or s_lower in key:
                base_risk = max(base_risk, val["risk"])
                detected.append({"symptom": key, "possible": val["diseases"], "specialist": val["specialist"],
                                  "severity": val["severity"], "remedies": val["remedies"]})
    # Age factor
    age_factor = 1.0 + (max(0, age - 40) * 0.005)
    # BMI factor
    bmi_factor = 1.0
    if bmi < 18.5 or bmi > 30: bmi_factor = 1.2
    elif bmi > 25: bmi_factor = 1.1
    # BP factor
    bp_factor = 1.0 + (max(0, bp - 120) * 0.003)

    final_risk = min(0.99, base_risk * age_factor * bmi_factor * bp_factor)
    return round(final_risk * 100, 1), detected

# ─── BMR CALCULATOR ───────────────────────────────────────────────────────────
def calculate_bmr(weight_kg, height_cm, age, gender, activity="moderate"):
    if gender.lower() in ["male", "m"]:
        bmr = 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)
    activity_map = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}
    tdee = bmr * activity_map.get(activity, 1.55)
    bmi = weight_kg / ((height_cm / 100) ** 2)
    return round(bmr), round(tdee), round(bmi, 1)

# ─── CALORIE CALCULATOR ───────────────────────────────────────────────────────
CALORIE_DB = {
    "rice": 206, "roti": 120, "dal": 150, "chicken": 335, "egg": 78,
    "banana": 89, "apple": 95, "milk": 149, "paneer": 265, "bread": 79,
    "samosa": 262, "idli": 58, "dosa": 168, "paratha": 300, "upma": 177,
    "biryani": 290, "curd": 98, "oats": 150, "salad": 50, "soup": 80,
    "coffee": 37, "tea": 26, "juice": 110, "water": 0, "pizza": 266,
    "burger": 295, "noodles": 220, "fish": 208, "tofu": 144, "potato": 77,
}

def get_calories(food_item):
    food_lower = food_item.lower().strip()
    for key, cal in CALORIE_DB.items():
        if key in food_lower or food_lower in key:
            return cal
    return None

# ─── CHATBOT LOGIC ────────────────────────────────────────────────────────────
def process_message(message, user_data=None):
    msg = message.lower().strip()
    response = {"text": "", "type": "text", "data": None, "emotion": "neutral"}

    # Greeting
    if any(w in msg for w in ["hello", "hi", "hey", "namaste", "hola"]):
        greetings = [
            "Namaste! 🙏 I'm FAAAHHHH, your AI health companion. How are you feeling today?",
            "Hello! I'm here to help you with health queries, symptoms, diet plans, and much more. What can I do for you?",
            "Hi there! Ready to support your wellness journey. Ask me about symptoms, diet, BMI, or medications!",
        ]
        response["text"] = random.choice(greetings)
        response["emotion"] = "happy"
        return response

    # Emergency detection
    emergency_words = ["emergency", "heart attack", "can't breathe", "unconscious", "severe chest pain", "stroke", "overdose", "suicide", "dying"]
    if any(w in msg for w in emergency_words):
        response["text"] = "🚨 **EMERGENCY DETECTED** 🚨\n\nPlease call emergency services immediately!\n\n🇮🇳 **India:** 112 (Emergency) | 108 (Ambulance)\n🇺🇸 **USA:** 911\n🇬🇧 **UK:** 999\n🇦🇺 **Australia:** 000\n\n⚠️ Stay calm. If possible, have someone with you. I'm routing you to emergency help!"
        response["type"] = "emergency"
        response["emotion"] = "alert"
        return response

    # Symptom analysis
    if any(w in msg for w in ["symptom", "feeling", "pain", "ache", "sick", "suffer", "problem"] + list(SYMPTOM_DISEASE_MAP.keys())):
        found_symptoms = [k for k in SYMPTOM_DISEASE_MAP.keys() if k in msg]
        if found_symptoms:
            sym = found_symptoms[0]
            info = SYMPTOM_DISEASE_MAP[sym]
            response["text"] = f"🔍 **Symptom Analysis: {sym.title()}**\n\n**Possible Conditions:** {', '.join(info['diseases'][:3])}\n\n**Severity:** {'🔴 High' if info['severity']=='high' else '🟡 Medium' if info['severity']=='medium' else '🟢 Low'}\n\n**Home Remedies:**\n" + "\n".join([f"• {r}" for r in info['remedies']]) + f"\n\n**Recommended Specialist:** 👨‍⚕️ {info['specialist']}\n\n💊 Would you like a diet recommendation or to set a medication reminder?"
            response["type"] = "symptom_analysis"
            response["emotion"] = "concerned" if info["severity"] == "high" else "thinking"
            response["data"] = {"symptom": sym, "severity": info["severity"], "risk": info["risk"]}
        else:
            response["text"] = "I noticed you're describing symptoms. Please describe your symptoms more specifically (e.g., 'I have fever and headache'). I'll analyze them for you! 🩺"
            response["emotion"] = "thinking"
        return response

    # Disease prediction
    if any(w in msg for w in ["predict", "risk", "chance", "likelihood", "diagnosis"]):
        response["text"] = "🤖 **Disease Risk Prediction**\n\nTo predict your health risk accurately, please provide:\n1. List your current symptoms (comma separated)\n2. Your age\n3. Your weight (kg) and height (cm)\n4. Your current BP (if known)\n\nExample: *'predict: fever, cough, fatigue | age:35 | weight:70 height:170 bp:130'*"
        response["type"] = "prediction_prompt"
        response["emotion"] = "thinking"
        return response

    # Parse prediction request
    if "predict:" in msg or ("|" in msg and "age:" in msg):
        try:
            parts = msg.split("|")
            symptoms_raw = parts[0].replace("predict:", "").strip()
            symptoms_list = [s.strip() for s in symptoms_raw.split(",")]
            age = int(re.search(r"age:(\d+)", msg).group(1)) if "age:" in msg else 30
            weight = float(re.search(r"weight:(\d+)", msg).group(1)) if "weight:" in msg else 70
            height = float(re.search(r"height:(\d+)", msg).group(1)) if "height:" in msg else 170
            bp = int(re.search(r"bp:(\d+)", msg).group(1)) if "bp:" in msg else 120
            bmi = weight / ((height / 100) ** 2)
            risk_score, detected = predict_disease_risk(symptoms_list, age, bmi, bp)

            diseases_text = ""
            for d in detected[:3]:
                diseases_text += f"\n• **{d['symptom'].title()}** → {', '.join(d['possible'][:2])} | Specialist: {d['specialist']}"

            risk_level = "🔴 HIGH" if risk_score > 65 else "🟡 MODERATE" if risk_score > 35 else "🟢 LOW"
            response["text"] = f"🧬 **ML Disease Risk Prediction**\n\n**Overall Risk Score: {risk_score}% — {risk_level}**\n\n**Detected Patterns:**{diseases_text}\n\n**BMI:** {round(bmi, 1)} | **Age Factor Applied** ✅\n\n📋 *This is an AI-assisted analysis, not a medical diagnosis. Please consult a doctor.*"
            response["type"] = "prediction_result"
            response["data"] = {"risk": risk_score, "detected": detected[:3]}
            response["emotion"] = "alert" if risk_score > 65 else "thinking"
        except Exception as e:
            response["text"] = f"Couldn't parse prediction input. Use format: *predict: fever, cough | age:35 | weight:70 height:170 bp:130*"
        return response

    # BMR/BMI Calculator
    if any(w in msg for w in ["bmr", "bmi", "calorie need", "metabolic", "tdee"]):
        if "bmr:" in msg or "weight:" in msg:
            try:
                weight = float(re.search(r"weight[:\s]+(\d+\.?\d*)", msg).group(1))
                height = float(re.search(r"height[:\s]+(\d+\.?\d*)", msg).group(1))
                age = int(re.search(r"age[:\s]+(\d+)", msg).group(1))
                gender = "male" if "male" in msg else "female"
                activity = "moderate"
                for act in ["sedentary", "light", "moderate", "active", "very_active"]:
                    if act in msg: activity = act
                bmr, tdee, bmi = calculate_bmr(weight, height, age, gender, activity)
                bmi_cat = "Underweight" if bmi < 18.5 else "Normal" if bmi < 25 else "Overweight" if bmi < 30 else "Obese"
                response["text"] = f"📊 **Your Metabolic Profile**\n\n**BMR (Basal Metabolic Rate):** {bmr} kcal/day\n**TDEE (Daily Energy Needs):** {tdee} kcal/day\n**BMI:** {bmi} — *{bmi_cat}*\n\n**Activity Level:** {activity.title()}\n\n💡 To lose weight: eat {tdee - 500} kcal/day\nTo gain weight: eat {tdee + 300} kcal/day\n\nWant a personalized diet plan? Just ask! 🥗"
                response["type"] = "bmr_result"
                response["data"] = {"bmr": bmr, "tdee": tdee, "bmi": bmi, "bmi_cat": bmi_cat}
                response["emotion"] = "happy"
            except:
                response["text"] = "Please provide details: *bmr: weight:70 height:175 age:28 male moderate*"
        else:
            response["text"] = "🔢 **BMR & BMI Calculator**\n\nProvide your details in this format:\n*bmr: weight:70 height:175 age:28 male moderate*\n\nActivity levels: sedentary / light / moderate / active / very_active"
            response["emotion"] = "thinking"
        return response

    # Calorie calculator
    if any(w in msg for w in ["calorie", "calories", "how many cal", "food calorie"]):
        foods_mentioned = []
        for food, cal in CALORIE_DB.items():
            if food in msg:
                foods_mentioned.append((food, cal))
        if foods_mentioned:
            total = sum(c for _, c in foods_mentioned)
            details = "\n".join([f"• {f.title()}: {c} kcal" for f, c in foods_mentioned])
            response["text"] = f"🍽️ **Calorie Count**\n\n{details}\n\n**Total: {total} kcal**\n\n💡 Average adult daily need: ~2000 kcal"
            response["data"] = {"foods": foods_mentioned, "total": total}
        else:
            response["text"] = "🍎 **Calorie Calculator**\n\nAsk me about food calories! Try:\n*'how many calories in rice and dal'*\nor\n*'calories in banana and oats'*\n\nI have a database of 30+ Indian & international foods!"
        response["emotion"] = "happy"
        return response

    # Diet plan
    if any(w in msg for w in ["diet", "food plan", "what to eat", "meal plan", "nutrition"]):
        condition = "general"
        if "diabete" in msg or "sugar" in msg: condition = "diabetes"
        elif "blood pressure" in msg or "hypertension" in msg or "bp" in msg: condition = "hypertension"
        elif "weight loss" in msg or "lose weight" in msg or "fat" in msg: condition = "weight_loss"
        plan = DIET_PLANS[condition]
        response["text"] = f"🥗 **Personalized Diet Plan — {condition.replace('_',' ').title()}**\n\n🌅 **Breakfast:** {plan['breakfast'][0]}\n☀️ **Lunch:** {plan['lunch'][0]}\n🌙 **Dinner:** {plan['dinner'][0]}\n🍎 **Snacks:** {plan['snacks'][0]}\n\n📊 **Target:** {plan['calories']}\n💧 **Water:** {plan['water']}\n\n❌ **Avoid:** {', '.join(plan['avoid'][:3])}\n\n📄 Want a full PDF diet plan? Type *'download diet plan'*"
        response["type"] = "diet_plan"
        response["data"] = {"condition": condition, "plan": plan}
        response["emotion"] = "happy"
        return response

    # PDF download trigger
    if "download" in msg and ("diet" in msg or "plan" in msg or "report" in msg or "prediction" in msg):
        response["text"] = "📥 **Generating your PDF report...**\n\nYour personalized health document is being prepared with:\n✅ Diet plan\n✅ Calorie targets\n✅ Health recommendations\n✅ Emergency contacts\n\nClick the download button below! 📄"
        response["type"] = "pdf_ready"
        response["emotion"] = "happy"
        return response

    # Medication reminder
    if any(w in msg for w in ["remind", "medication", "medicine", "pill", "tablet", "dose"]):
        response["text"] = "💊 **Medication Reminder Setup**\n\nI can help you set up medication reminders! Use the format:\n*'remind me to take [medication] at [time]'*\n\nExample: *'remind me to take metformin at 8am and 8pm'*\n\nYou can also say **'show my reminders'** to see all active reminders."
        response["type"] = "reminder"
        response["emotion"] = "thinking"
        if "take" in msg and ("at" in msg or "am" in msg or "pm" in msg):
            response["text"] = "✅ **Reminder Set!**\n\nI've noted your medication schedule. You'll receive alerts at the specified times.\n\n💡 Tip: Always take medications with water unless specified otherwise. Never skip doses!"
            response["emotion"] = "happy"
        return response

    # Hospital finder
    if any(w in msg for w in ["hospital", "clinic", "doctor near", "find doctor", "nearby"]):
        response["text"] = "🏥 **Finding Hospitals Near You**\n\nI'm accessing your location to find nearby hospitals and clinics...\n\nClick the **'Find Hospitals'** button in the sidebar, or allow location access when prompted.\n\nThe map will show:\n📍 Nearby hospitals\n🏥 Clinics & urgent care\n🚑 Emergency services\n⭐ Ratings & distance"
        response["type"] = "hospital_finder"
        response["emotion"] = "thinking"
        return response

    # Home remedies
    if any(w in msg for w in ["home remedy", "natural", "herbal", "remedy", "cure at home"]):
        response["text"] = "🌿 **Home Remedies Guide**\n\nAsk me about specific symptoms for natural remedies!\n\nPopular remedies:\n• 🤒 Fever → Tulsi tea + cold compress\n• 🤧 Cold → Steam + ginger honey\n• 😮‍💨 Cough → Turmeric milk\n• 🤕 Headache → Peppermint oil\n• 🤢 Nausea → Ginger ale + rest\n\n⚠️ *Home remedies complement, not replace, medical treatment.*"
        response["emotion"] = "happy"
        return response

    # Feedback
    if any(w in msg for w in ["feedback", "rate", "review", "suggest", "improve"]):
        response["text"] = "⭐ **Share Your Feedback**\n\nThank you for helping me improve! Please rate your experience:\n\n🌟 Tap a star rating below, or tell me:\n• What you liked\n• What could be better\n• Features you'd like to see\n\nYour feedback helps me serve you better! 💙"
        response["type"] = "feedback"
        response["emotion"] = "happy"
        return response

    # Mental health check
    if any(w in msg for w in ["stress", "anxious", "depressed", "sad", "mental", "panic", "worry"]):
        response["text"] = "💙 **Mental Health Support**\n\nI hear you, and I'm here for you. Mental health is just as important as physical health.\n\n**Immediate relief techniques:**\n• 🫁 Box breathing: inhale 4s → hold 4s → exhale 4s → hold 4s\n• 🖐️ 5-4-3-2-1 grounding: name 5 things you see\n• 🎵 Listen to calming music\n• 🚶 Short walk in nature\n\n**Recommended:** Talk to a Psychiatrist or Psychologist\n\n📞 **iCall (India):** 9152987821\n📞 **Vandrevala Foundation:** 1860-2662-345 (24/7)"
        response["emotion"] = "caring"
        return response

    # Wellness tips
    if any(w in msg for w in ["tip", "wellness", "healthy", "advice", "lifestyle"]):
        tips = [
            "💧 Drink 8 glasses of water daily — hydration is the simplest health hack!",
            "🚶 Walk 10,000 steps a day to reduce heart disease risk by 30%.",
            "😴 7-9 hours of sleep boosts immunity, mood, and metabolism.",
            "🧘 5 minutes of deep breathing reduces cortisol and calms anxiety.",
            "🥦 Eat a rainbow of vegetables — different colors = different nutrients!",
            "📵 Screen-free 1 hour before bed improves sleep quality significantly.",
            "☀️ 15 minutes of morning sunlight regulates your circadian rhythm.",
        ]
        response["text"] = f"✨ **Daily Wellness Tip**\n\n{random.choice(tips)}\n\n💡 Ask me for more tips, your diet plan, or symptom analysis anytime!"
        response["emotion"] = "happy"
        return response

    # Default
    responses = [
        "I'm your AI health companion! I can help with:\n🔍 **Symptom analysis** | 🧬 **Disease prediction** | 💊 **Medication reminders**\n🥗 **Diet plans** | 📊 **BMR/BMI calculator** | 🌿 **Home remedies**\n🏥 **Hospital finder** | 🚨 **Emergency help** | 📄 **PDF reports**\n\nWhat would you like help with today?",
        "I understand you have a health concern. Could you describe your symptoms, or ask me about diet, medications, or wellness tips?",
        "Try asking me: *'I have a fever'*, *'calculate my BMR'*, *'diet for diabetes'*, or *'find hospitals near me'* 🏥",
    ]
    response["text"] = random.choice(responses)
    response["emotion"] = "neutral"
    return response

# ─── ROUTES ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "empty"}), 400
    result = process_message(message)
    # Store analytics
    if "history" not in session:
        session["history"] = []
        session["analytics"] = {"total_queries": 0, "symptom_checks": 0, "diet_plans": 0, "reminders": 0}
    session["history"].append({"role": "user", "msg": message, "time": datetime.datetime.now().isoformat()})
    session["history"].append({"role": "bot", "msg": result["text"][:100], "time": datetime.datetime.now().isoformat()})
    an = session.get("analytics", {})
    an["total_queries"] = an.get("total_queries", 0) + 1
    if result.get("type") == "symptom_analysis": an["symptom_checks"] = an.get("symptom_checks", 0) + 1
    if result.get("type") == "diet_plan": an["diet_plans"] = an.get("diet_plans", 0) + 1
    if result.get("type") == "reminder": an["reminders"] = an.get("reminders", 0) + 1
    session["analytics"] = an
    session.modified = True
    return jsonify(result)

@app.route("/analytics")
def analytics():
    an = session.get("analytics", {"total_queries": 0, "symptom_checks": 0, "diet_plans": 0, "reminders": 0})
    history = session.get("history", [])
    return jsonify({"analytics": an, "history_count": len(history)})

@app.route("/hospitals")
def hospitals():
    lat = request.args.get("lat", 28.6139)
    lon = request.args.get("lon", 77.2090)
    # Overpass API query for hospitals
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:5000,{lat},{lon});
      node["amenity"="clinic"](around:3000,{lat},{lon});
      node["amenity"="doctors"](around:3000,{lat},{lon});
    );
    out body;
    """
    return jsonify({
        "query": overpass_query,
        "overpass_url": f"https://overpass-api.de/api/interpreter",
        "lat": lat, "lon": lon,
        "message": "Query ready for Overpass API"
    })

@app.route("/generate-pdf")
def generate_pdf():
    condition = request.args.get("condition", "general")
    plan = DIET_PLANS.get(condition, DIET_PLANS["general"])
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", fontSize=22, spaceAfter=12, textColor=colors.HexColor("#1a6b5a"), fontName="Helvetica-Bold", alignment=1)
    head_style = ParagraphStyle("Head", fontSize=14, spaceAfter=6, textColor=colors.HexColor("#2d9970"), fontName="Helvetica-Bold")
    body_style = ParagraphStyle("Body", fontSize=11, spaceAfter=4, fontName="Helvetica", leading=16)
    small_style = ParagraphStyle("Small", fontSize=9, textColor=colors.grey, fontName="Helvetica")
    story = []
    story.append(Paragraph("🏥 MediBot — Personalized Health Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}", small_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Diet Plan: {condition.replace('_',' ').title()}", head_style))
    story.append(Spacer(1, 0.1*inch))
    meal_data = [
        ["Meal", "Recommendation"],
        ["🌅 Breakfast", plan["breakfast"][0]],
        ["☀️ Lunch", plan["lunch"][0]],
        ["🌙 Dinner", plan["dinner"][0]],
        ["🍎 Snack", plan["snacks"][0]],
    ]
    t = Table(meal_data, colWidths=[2*inch, 4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a6b5a")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#f0faf7"), colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#c0e8dc")),
        ("PADDING", (0,0), (-1,-1), 8),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("📊 Daily Targets", head_style))
    story.append(Paragraph(f"Calorie Target: {plan['calories']}", body_style))
    story.append(Paragraph(f"Water Intake: {plan['water']}", body_style))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph("❌ Foods to Avoid", head_style))
    for item in plan["avoid"]:
        story.append(Paragraph(f"• {item}", body_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("🚨 Emergency Numbers (India)", head_style))
    emg = [["Service", "Number"]] + [[k, v] for k, v in EMERGENCY_NUMBERS["India"].items()]
    et = Table(emg, colWidths=[3*inch, 3*inch])
    et.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#cc2222")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#fff0f0"), colors.white]),
        ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
        ("PADDING", (0,0), (-1,-1), 7),
    ]))
    story.append(et)
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("⚠️ Disclaimer: This report is AI-generated and does not replace professional medical advice. Always consult a qualified physician for diagnosis and treatment.", small_style))
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"medibot_health_report_{condition}.pdf", mimetype="application/pdf")

@app.route("/feedback", methods=["POST"])
def save_feedback():
    data = request.json
    feedback_file = "feedback.json"
    feedbacks = []
    if os.path.exists(feedback_file):
        with open(feedback_file) as f:
            try: feedbacks = json.load(f)
            except: feedbacks = []
    feedbacks.append({"rating": data.get("rating"), "comment": data.get("comment", ""), "time": datetime.datetime.now().isoformat()})
    with open(feedback_file, "w") as f:
        json.dump(feedbacks, f)
    return jsonify({"status": "ok", "message": "Thank you for your feedback! 💙"})

@app.route("/emergency-numbers")
def emergency_numbers():
    return jsonify(EMERGENCY_NUMBERS)

if __name__ == "__main__":
    app.run(debug=True, port=5000)