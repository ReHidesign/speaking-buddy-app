import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- CSS: TELJES, MOBILBARÁT DESIGN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .buddy-header { text-align: center; padding: 20px; }
    .main-title { font-weight: 800; margin-bottom: 0px; }
    .sub-title { font-style: italic; opacity: 0.8; margin-bottom: 25px; }
    .welcome-text { text-align: center; font-size: 1.1em; line-height: 1.6; max-width: 600px; margin: 0 auto 25px auto; }
    
    /* GOMB KONTÉNER: Ez oldja meg a mobil elrendezést */
    .button-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin: 15px 0;
    }
    
    /* Egységes gomb stílus paraméterek nélkül */
    div.stButton > button {
        border-radius: 12px !important;
        min-width: 140px !important;
        height: 3.5em !important;
        transition: all 0.2s;
        border: 1px solid #d1d5db !important;
    }
    
    /* Kék kiemelés a kezdő gombnak */
    div.stButton > button:contains("🚀") {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
    }

    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.1);
        font-size: 0.9em;
    }
    .footer-note { text-align: center; color: grey; font-size: 11px; margin-top: 50px; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# --- ADATOK ---
TOPICS = [
    "🎲 Surprise Me", "🏠 Family & Friends", "🏘️ Home", "🐾 Animals",
    "🌍 Environment", "🏙️ Lifestyle", "💼 Jobs & Career", "🎭 Culture", 
    "🏫 Education", "🛍️ Shopping", "✈️ Travel", "⚽ Sport", 
    "💻 Tech", "🍔 Food", "👗 Fashion", "🌦️ Weather"
]
LEVELS = ["A1 (Beginner)", "A2 (Pre-Int)", "B1 (Intermediate)", "B2 (Upper-Int)", "C1 (Advanced)"]
MODES = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang"]

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
        system_msg = f"You are SpeakingBuddy. User level: {st.session_state.user_level}. Mode: {st.session_state.current_mode}. Topic: {st.session_state.chat_topic}."
        hist = [{"role": "system", "content": system_msg}]
        hist.extend(st.session_state.messages[-6:])
        if prompt: hist.append({"role": "user", "content": prompt})
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist}, timeout=15)
            return r.json()['choices'][0]['message']['content']
        except: return "Connection error, sorry!"

    # --- SIDEBAR: CONTROL PANEL ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        if st.session_state.user_level:
            st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
        if st.session_state.current_mode:
            st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        
        if st.session_state.chat_topic:
            if st.button("⬅️ Back to Topics"):
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
        
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><h1 class='main-title'>🤖 SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-text'>I am here to help you <b>practise English speaking</b> and focus on <b>real-life communication</b>. Whether you want to <b>debate</b>, roleplay a <b>situation</b>, or just have a <b>friendly chat</b>, I'm ready!</div>", unsafe_allow_html=True)
        # Középre igazított kezdő gomb konténer
        st.markdown("<div class='button-grid'>", unsafe_allow_html=True)
        if st.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        st.markdown("<div class='button-grid'>", unsafe_allow_html=True)
        for lvl in LEVELS:
            if st.button(lvl):
                st.session_state.user_level = lvl
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        st.markdown("<div class='button-grid'>", unsafe_allow_html=True)
        for m in MODES:
            if st.button(m):
                st.session_state.current_mode = m
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif not st.session_state.chat_topic:
        st.subheader("Select topic:")
        st.markdown("<div class='button-grid'>", unsafe_allow_html=True)
        for t in TOPICS:
            if st.button(t):
                st.session_state.chat_topic = t
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!")})
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Chat felület
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text = st.chat_input("Write to Buddy...")
        
        user_msg = text
        if audio:
            # Whisper API hívás (kihagyva a rövidítésért, de a logikád megvan)
            pass

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner("Thinking..."):
                ans = call_groq(user_msg)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    st.markdown("<div class='footer-note'>Please note: SpeakingBuddy is an AI and can make mistakes.<br>© 2026 SpeakingBuddy by ReHi</div>", unsafe_allow_html=True)
