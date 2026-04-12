import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- INITIALIZE SESSION STATE (MINDEN ELŐTT!) ---
state_defaults = {
    "messages": [],
    "current_mode": None,
    "user_level": None,
    "chat_topic": None,
    "intro_done": False,
    "feedback_level": "Balanced"
}

for key, default in state_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- CSS DESIGN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 80px; }
    .main-title { font-weight: 800; margin-bottom: 0px; }
    .sub-title { font-style: italic; opacity: 0.8; margin-bottom: 25px; }
    .welcome-box { text-align: center; font-size: 1.1em; line-height: 1.6; margin-bottom: 25px; }
    .stButton > button { border-radius: 8px; width: 100%; margin-bottom: 2px; }
    .stButton > button[kind="secondary"] { background-color: #3498db !important; color: white !important; }
    .status-box { padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.1); font-size: 0.9em; }
    .footer-note { text-align: center; color: grey; font-size: 10px; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONFIG ---
LEVELS = ["A1 (Beginner)", "A2 (Pre-Int)", "B1 (Intermediate)", "B2 (Upper-Int)", "C1 (Advanced)", "C2 (Proficiency)"]
MODES = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang"]
TOPICS = ["🎲 Surprise Me", "🏠 Family & Friends", "🏘️ Home & Housing", "🐾 Animals & Pets", "🌍 Environment", "🏙️ Lifestyle", "💼 Jobs & Career", "🎭 Culture", "🏫 Education", "🛍️ Shopping", "✈️ Travel", "⚽ Health & Sport", "💻 Tech & Media", "🍔 Food", "👗 Fashion", "🌦️ Weather", "🇭🇺 Hungary & EU", "🏛️ Civilization"]

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    def speak_text(text):
        clean = re.sub(r'\(.*?\)', '', text).replace("*", "").strip()
        tts = gTTS(text=clean if clean else "I'm listening.", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        lv, md, tp = st.session_state.user_level, st.session_state.current_mode, st.session_state.chat_topic
        kb = "B1: Topics for Teenagers. B2: 1000 Questions/Bajnóczi. C1: 1000 Questions C1. Civilization: Culture tutor. Don't repeat questions!"
        hist = [{"role": "system", "content": f"{system_instruction} Level:{lv}, Mode:{md}, Topic:{tp}. {kb}"}]
        hist.extend(st.session_state.messages[-4:])
        if prompt: hist.append({"role": "user", "content": prompt})
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=20)
            return r.json()['choices'][0]['message']['content']
        except: return "*(Buddy smiles)* Connection glitch! Can you repeat?"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
        st.markdown("---")
        if st.session_state.user_level: st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
        if st.session_state.current_mode: st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        if st.session_state.chat_topic: st.markdown(f"<div class='status-box'><b>Topic:</b> {st.session_state.chat_topic}</div>", unsafe_allow_html=True)
        if st.session_state.user_level and st.button("🔄 New Session"):
            st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
            st.session_state.messages = []
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-box'>I am here to help you <b>practise English speaking</b> and focus on <b>real-life communication</b>.<br><br>Whether you want to <b>debate</b>, <b>roleplay</b>, or just <b>chat</b>, I'm ready!</div>", unsafe_allow_html=True)
        if st.button("Let's start! 🚀", kind="secondary"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        for i in range(0, len(LEVELS), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(LEVELS):
                    if cols[j].button(LEVELS[i+j], key=f"L{i+j}"):
                        st.session_state.user_level = LEVELS[i+j]
                        st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        for i in range(0, len(MODES), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(MODES):
                    if cols[j].button(MODES[i+j], key=f"M{i+j}"):
                        st.session_state.current_mode = MODES[i+j]
                        st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader("Select topic:")
        for i in range(0, len(TOPICS), 2):
            cols = st.columns(2)
            for j in range(2):
                if i+j < len(TOPICS):
                    if cols[j].button(TOPICS[i+j], key=f"T{i+j}"):
                        st.session_state.chat_topic = TOPICS[i+j]
                        st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!", "Partner")})
                        st.rerun()
    else:
        # Chat Interface
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')
        
        audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text = st.chat_input("Write to Buddy...")
        user_msg = text
        if audio:
            try:
                r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers={"Authorization": f"Bearer {api_key}"}, files={"file": ("audio.wav", audio['bytes'])}, data={"model": "whisper-large-v3", "language": "en"})
                user_msg = r.json().get("text", "")
            except: user_msg = None
        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            st.session_state.messages.append({"role": "assistant", "content": call_groq(user_msg, "Partner")})
            st.rerun()

    st.markdown("<div class='footer-note'>© 2026 SpeakingBuddy by ReHi</div>", unsafe_allow_html=True)
