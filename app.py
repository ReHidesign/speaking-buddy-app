import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- CSS: FIXÁLT ÉS BIZTONSÁGOS STÍLUSOK ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Gombok mobilbarát elrendezése */
    div.stButton > button {
        border-radius: 12px !important;
        width: 100% !important; 
        margin-bottom: 8px;
        border: 1px solid #d1d5db !important;
        height: 3.5em;
        font-weight: 500;
    }

    /* Kezdő gomb egyedi színezése */
    div.stButton > button:first-child:contains("🚀") {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
    }

    .buddy-header { text-align: center; padding: 10px; }
    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.1);
        font-size: 0.9em;
    }
    .footer-note { text-align: center; color: grey; font-size: 10px; margin-top: 30px; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
TOPICS = [
    "🎲 Surprise Me", "🏠 Family & Friends", "🏘️ Home & Housing", "🐾 Animals & Pets",
    "🌍 Environment", "🏙️ Lifestyle", "💼 Jobs & Career", "🎭 Culture", 
    "🏫 Education", "🛍️ Shopping", "✈️ Travel", "⚽ Health & Sport", 
    "💻 Tech & Media", "🍔 Food", "👗 Fashion", "🌦️ Weather"
]
LEVELS = ["A1 (Beginner)", "A2 (Pre-Int)", "B1 (Intermediate)", "B2 (Upper-Int)", "C1 (Advanced)"]

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Groq API Key:", type="password")

# --- SESSION STATE ---
if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic", "intro_done"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    def speak_text(text):
        clean = re.sub(r'\(.*?\)', '', text).replace("*", "").strip()
        tts = gTTS(text=clean if clean else "I'm listening.", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        lv = st.session_state.user_level or "B1"
        mode = st.session_state.current_mode or "Chat"
        topic = st.session_state.chat_topic or "General"
        
        system_msg = f"You are SpeakingBuddy. Level: {lv}, Mode: {mode}, Topic: {topic}. Be helpful."
        hist = [{"role": "system", "content": system_msg}]
        hist.extend(st.session_state.messages[-5:])
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist}, timeout=15)
            return r.json()['choices'][0]['message']['content']
        except:
            return "Connection error. Let's try again!"

    # --- UI FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><h1>🤖 SpeakingBuddy</h1></div>", unsafe_allow_html=True)
        st.write("Ready to practice? Click the button below!")
        if st.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Select your level:")
        for lvl in LEVELS:
            if st.button(lvl):
                st.session_state.user_level = lvl
                st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        for m in ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]:
            if st.button(m):
                st.session_state.current_mode = m
                st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader("Select topic:")
        for t in TOPICS:
            if st.button(t):
                st.session_state.chat_topic = t
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!")})
                st.rerun()

    else:
        # Chat felület
        with st.sidebar:
            st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}<br><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
            if st.button("🔄 New Topic"):
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text = st.chat_input("Write here...")
        
        user_msg = text
        if audio:
            try:
                r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", 
                                 headers={"Authorization": f"Bearer {api_key}"}, 
                                 files={"file": ("audio.wav", audio['bytes'])}, 
                                 data={"model": "whisper-large-v3", "language": "en"})
                user_msg = r.json().get("text", "")
            except: pass

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner("Buddy is thinking..."):
                ans = call_groq(user_msg)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

st.markdown("<div class='footer-note'>© 2026 SpeakingBuddy</div>", unsafe_allow_html=True)
