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

# --- CSS: DESIGN ÉS MOBIL FIX ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 80px; margin-bottom: 5px; }
    .main-title { font-family: 'Helvetica Neue', sans-serif; font-weight: 800; margin-bottom: 0px; }
    .sub-title { font-style: italic; margin-top: 0px; margin-bottom: 25px; opacity: 0.8; }
    
    .welcome-box { text-align: center; font-size: 1.1em; line-height: 1.6; margin-bottom: 25px; max-width: 600px; margin-left: auto; margin-right: auto; }
    
    .stButton > button { border-radius: 8px; width: 100%; margin-bottom: 5px; }
    .stButton > button[kind="secondary"] {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
    }

    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.1);
        font-size: 0.9em;
    }
    .footer-note { text-align: center; color: grey; font-size: 10px; margin-top: 30px; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
LEVEL_ORDER = ["A1 (Beginner)", "A2 (Pre-Int)", "B1 (Intermediate)", "B2 (Upper-Int)", "C1 (Advanced)", "C2 (Proficiency)"]
TOPICS = [
    "🎲 Surprise Me", "🏠 Family & Friends", "🏘️ Home & Housing", "🐾 Animals & Pets",
    "🌍 Environment", "🏙️ Lifestyle", "💼 Jobs & Career", "🎭 Culture", 
    "🏫 Education", "🛍️ Shopping", "✈️ Travel", "⚽ Health & Sport", 
    "💻 Tech & Media", "🍔 Food", "👗 Fashion", "🌦️ Weather",
    "🇭🇺 Hungary & EU", "🏛️ Civilization"
]

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

# --- ÁLLAPOT KEZELÉS (Session State) ---
state_keys = {
    "messages": [],
    "current_mode": None,
    "user_level": None,
    "chat_topic": None,
    "intro_done": False,
    "feedback_level": "Balanced"
}

for key, default in state_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default

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
        
        mode = st.session_state.current_mode or "Conversation"
        level = st.session_state.user_level or "B1"
        topic = st.session_state.chat_topic or "General"
        
        kb_text = f"""
        Strictly use these as knowledge base:
        Level B1: 'Twenty-three Topics for Teenagers'.
        Level B2: '1000 Questions B2', 'Színes B2', 'Bajnóczi B2'.
        Level C1/C2: '1000 Questions C1', 'Színes C1'.
        Topic '🏛️ Civilization': Act as a tutor for British/American culture.
        Always vary your questions. If the student returns, do not ask the same thing.
        """
        
        hist = [{"role": "system", "content": f"{system_instruction} Mode: {mode}. Level: {level}. Topic: {topic}. {kb_text}"}]
        hist.extend(st.session_state.messages[-4:])
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=20)
            return r.json()['choices'][0]['message']['content']
        except:
            return "*(Buddy smiles)* I had a tiny glitch. What was that again?"

    # --- SIDEBAR: CONTROL PANEL ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
        st.markdown("---")
        
        if st.session_state.user_level:
            st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
        if st.session_state.current_mode:
            st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        if st.session_state.chat_topic:
            st.markdown(f"<div class='status-box'><b>Topic:</b> {st.session_state.chat_topic}</div>", unsafe_allow_html=True)
        
        if st.session_state.user_level and st.button("🔄 Reset / New Topic"):
            st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
            st.session_state.messages = []
            st.rerun()

    # --- MAIN UI FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("""
            <div class='welcome-box'>
            I am here to help you <b>practise English speaking</b> and focus on <b>real-life communication</b> (and exam preparation).<br><br>
            Whether you want to <b>debate</b>, roleplay a <b>situation</b>, describe a <b>picture</b>, or just have a <b>friendly chat</b>, I'm ready!
            </div>
            """, unsafe_allow_html=True)
        if st.button("Let's start! 🚀", kind="secondary"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        # A1-A2, B1-B2 sorrend fixálása
        for i in range(0, len(LEVEL_ORDER), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(LEVEL_ORDER):
                    lvl = LEVEL_ORDER[i+j]
                    if cols[j].button(lvl, key=f"L_{lvl}"):
                        st.session_state.user_level = lvl
                        st.rerun()
        if st.button("🔍 Assess my level"):
            st.session_state.user_level = "Determining..."
            st.session_state.current_mode = "Assessment"
            st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello! Start assessment.", "Evaluator")})
            st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang"]
        for i in range(0, len(m_list), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(m_list):
                    m = m_list[i+j]
                    if cols[j].button(m, key=f"M_{m}"):
                        st.session_state.current_mode = m
                        st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader("Select topic:")
        for i in range(0, len(TOPICS), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(TOPICS):
                    t = TOPICS[i+j]
                    if cols[j].button(t, key=f"T_{t}"):
                        st.session_state.chat_topic = t
                        with st.spinner('Buddy is getting ready...'):
                            st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello! Start.", "Partner")})
                        st.rerun()

    else:
        # Chat interface
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio_data = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text_input = st.chat_input("Write to Buddy...")
        
        user_msg = text_input
        if audio_data:
            url_trans = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers_trans = {"Authorization": f"Bearer {api_key}"}
            files = {"file": ("audio.wav", audio_data['bytes'], "audio/wav")}
            try:
                r = requests.post(url_trans, headers=headers_trans, files=files, data={"model": "whisper-large-v3", "language": "en"}, timeout=25)
                user_msg = r.json().get("text", "")
            except: user_msg = None

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner('Thinking...'):
                ans = call_groq(user_msg, "Partner")
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    st.markdown("<div class='footer-note'>© 2026 SpeakingBuddy by ReHi</div>", unsafe_allow_html=True)
