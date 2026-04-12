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

# --- SESSION STATE INITIALIZATION (Minden előtt!) ---
if "messages" not in st.session_state: st.session_state.messages = []
if "current_mode" not in st.session_state: st.session_state.current_mode = None
if "user_level" not in st.session_state: st.session_state.user_level = None
if "chat_topic" not in st.session_state: st.session_state.chat_topic = None
if "intro_done" not in st.session_state: st.session_state.intro_done = False
if "feedback_level" not in st.session_state: st.session_state.feedback_level = "Balanced"

# --- CSS: DESIGN ÉS STABILIZÁLÁS ---
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
LEVELS = ["A1 (Beginner)", "A2 (Pre-Int)", "B1 (Intermediate)", "B2 (Upper-Int)", "C1 (Advanced)", "C2 (Proficiency)"]
TOPICS = [
    "🎲 Surprise Me (Free Chat)", "🏠 Family & Friends", "🏘️ Home & Housing", "🐾 Animals & Pets",
    "🌍 Environment & Nature", "🏙️ Lifestyle & Daily Routine", "💼 Jobs & Career", "🎭 Culture & Entertainment", 
    "🏫 Education & Languages", "🛍️ Shopping & Consumer Society", "✈️ Travel & Transport", "⚽ Health & Sport", 
    "💻 Tech & Media", "🍔 Food & Eating Out", "👗 Fashion & Clothes", "🌦️ Weather & Seasons",
    "🇭🇺 Hungary & the EU", "🏛️ General Culture & Civilization"
]

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

# --- FUNKCIÓK ---
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
        
        lv = st.session_state.user_level or "B1"
        topic = st.session_state.chat_topic or "General"
        
        kb_mapping = f"""
        Knowledge Base Instructions:
        Level B1: 'Twenty-three Topics for Teenagers' (Family: Ch1,2,4; Home: Ch3; Env: Ch22; Animals: Ch20; Lifestyle: Ch6; Jobs: Ch17; Culture: Ch7,8,9; Education: Ch5; Travel: Ch18,19; Health: Ch10,11; Tech: Ch15,16; Food: Ch12; Fashion: Ch14; Weather: Ch21; Shopping: Ch13; Hungary: Ch23).
        Level B2: '1000 Questions B2', 'Színes B2', 'Bajnóczi B2'.
        Level C1/C2: '1000 Questions C1', 'Színes C1'.
        Topic '🏛️ General Culture & Civilization': Focus on UK/US customs and history.
        Important: Be creative and avoid repeating the same questions.
        """
        
        mode_instr = f"Mode: {st.session_state.current_mode}. Level: {lv}. Topic: {topic}. {kb_mapping}"
        hist = [{"role": "system", "content": f"{system_instruction} {mode_instr}"}]
        hist.extend(st.session_state.messages[-4:])
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=20)
            return r.json()['choices'][0]['message']['content']
        except:
            return "*(Buddy smiles)* My connection flickered. Could you say that again?"

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
        
        if st.session_state.user_level and st.button("🔄 Change Topic/Level"):
            st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
            st.session_state.messages = []
            st.rerun()

    # --- MAIN UI ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-box'>I am here to help you <b>practise English speaking</b> and focus on <b>real-life communication</b>.<br><br>Ready to start?</div>", unsafe_allow_html=True)
        if st.button("Let's start! 🚀", kind="secondary"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        for i in range(0, len(LEVELS), 2):
            cols = st.columns(2)
            if cols[0].button(LEVELS[i], key=f"L{i}"):
                st.session_state.user_level = LEVELS[i]
                st.rerun()
            if i+1 < len(LEVELS):
                if cols[1].button(LEVELS[i+1], key=f"L{i+1}"):
                    st.session_state.user_level = LEVELS[i+1]
                    st.rerun()
        if st.button("🔍 Assess my level"):
            st.session_state.user_level = "Determining..."
            st.session_state.current_mode = "Assessment"
            st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello! Start assessment.", "Evaluator")})
            st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        modes = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang"]
        for i in range(0, len(modes), 2):
            cols = st.columns(2)
            if cols[0].button(modes[i], key=f"M{i}"):
                st.session_state.current_mode = modes[i]
                st.rerun()
            if i+1 < len(modes):
                if cols[1].button(modes[i+1], key=f"M{i+1}"):
                    st.session_state.current_mode = modes[i+1]
                    st.rerun()

    elif not st.session_state.chat_topic and st.session_state.current_mode != "Assessment":
        st.subheader("Select topic:")
        for i in range(0, len(TOPICS), 2):
            cols = st.columns(2)
            if cols[0].button(TOPICS[i], key=f"T{i}"):
                st.session_state.chat_topic = TOPICS[i]
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Start.", "Partner")})
                st.rerun()
            if i+1 < len(TOPICS):
                if cols[1].button(TOPICS[i+1], key=f"T{i+1}"):
                    st.session_state.chat_topic = TOPICS[i+1]
                    st.session_state.messages.append({"role": "assistant", "content": call_groq("Start.", "Partner")})
                    st.rerun()

    else:
        # Chat Interface
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
            with st.spinner('Buddy is thinking...'):
                ans = call_groq(user_msg, "Partner")
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    st.markdown("<div class='footer-note'>© 2026 SpeakingBuddy by ReHi</div>", unsafe_allow_html=True)
