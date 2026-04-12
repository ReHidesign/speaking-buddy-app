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

# --- SESSION STATE INITIALIZATION (Betonbiztos kezdés) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_mode" not in st.session_state: st.session_state.current_mode = None
if "user_level" not in st.session_state: st.session_state.user_level = None
if "chat_topic" not in st.session_state: st.session_state.chat_topic = None
if "intro_done" not in st.session_state: st.session_state.intro_done = False
if "feedback_level" not in st.session_state: st.session_state.feedback_level = "Balanced"

# --- CSS DESIGN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .buddy-header { text-align: center; padding: 20px; }
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
    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        lv, md, tp = st.session_state.user_level, st.session_state.current_mode, st.session_state.chat_topic
        hist = [{"role": "system", "content": f"{system_instruction} Level:{lv}, Mode:{md}, Topic:{tp}."}]
        hist.extend(st.session_state.messages[-4:])
        if prompt: hist.append({"role": "user", "content": prompt})
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=20)
            return r.json()['choices'][0]['message']['content']
        except: return "*(Buddy smiles)* Glitch! Say it again?"

    # --- SIDEBAR: CONTROL PANEL ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
        st.markdown("---")
        # Ezek a blokkok felelnek a folyamatos kijelzésért
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
        st.markdown("<div class='welcome-box'>I am here to help you <b>practise English speaking</b>.<br><br>Choose your level and let's get started!</div>", unsafe_allow_html=True)
        if st.button("Let's start! 🚀", kind="secondary"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        # MOBIL FIX: Soronkénti kettes felosztás a logikus sorrendért (A1-A2, B1-B2...)
        for i in range(0, len(LEVELS), 2):
            c1, c2 = st.columns(2)
            if c1.button(LEVELS[i], key=f"L{i}"):
                st.session_state.user_level = LEVELS[i]
                st.rerun()
            if i+1 < len(LEVELS):
                if c2.button(LEVELS[i+1], key=f"L{i+1}"):
                    st.session_state.user_level = LEVELS[i+1]
                    st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        for i in range(0, len(MODES), 2):
            c1, c2 = st.columns(2)
            if c1.button(MODES[i], key=f"M{i}"):
                st.session_state.current_mode = MODES[i]
                st.rerun()
            if i+1 < len(MODES):
                if c2.button(MODES[i+1], key=f"M{i+1}"):
                    st.session_state.current_mode = MODES[i+1]
                    st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader("Select topic:")
        for i in range(0, len(TOPICS), 2):
            c1, c2 = st.columns(2)
            if c1.button(TOPICS[i], key=f"T{i}"):
                st.session_state.chat_topic = TOPICS[i]
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!", "Partner")})
                st.rerun()
            if i+1 < len(TOPICS):
                if c2.button(TOPICS[i+1], key=f"T{i+1}"):
                    st.session_state.chat_topic = TOPICS[i+1]
                    st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!", "Partner")})
                    st.rerun()
    else:
        # Chat Interface (Standard rész)
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
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
