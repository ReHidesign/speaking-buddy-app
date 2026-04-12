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

# --- CSS: VISSZAÁLLÍTOTT ÉS JAVÍTOTT DESIGN ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 80px; margin-bottom: 5px; }
    .main-title { font-family: 'Helvetica Neue', sans-serif; font-weight: 800; margin-bottom: 0px; }
    .sub-title { font-style: italic; margin-top: 0px; margin-bottom: 25px; opacity: 0.8; }
    .welcome-text { text-align: center; font-size: 1.1em; line-height: 1.6; margin-bottom: 25px; max-width: 600px; margin-left: auto; margin-right: auto; }
    
    /* Gombok alapstílusa */
    .stButton > button { 
        border-radius: 8px; 
        width: 100%;
        transition: all 0.3s ease;
    }

    /* A kék gomb fehér betűvel - ahogy kérted, CSS-ből kényszerítve */
    div.stButton > button:contains("🚀") {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 1.2em !important;
        padding: 10px !important;
    }

    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.1);
        font-size: 0.9em;
    }
    .help-card { 
        padding: 12px; border-radius: 10px; border: 1px dashed #e67e22; 
        background-color: rgba(230, 126, 34, 0.1); font-size: 13px; margin-bottom: 15px;
    }
    .footer-note { text-align: center; color: grey; font-size: 11px; margin-top: 30px; opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ (Minden téma visszakerült) ---
TOPICS = [
    "🎲 Surprise Me (Free Chat)", "🏠 Family & Friends", "🏘️ Home & Housing", "🐾 Animals & Pets",
    "🌍 Environment & Nature", "🏙️ Lifestyle & Daily Routine", "💼 Jobs & Career", "🎭 Culture & Entertainment", 
    "🏫 Education & Languages", "🛍️ Shopping & Consumer Society", "✈️ Travel & Transport", "⚽ Health & Sport", 
    "💻 Tech & Media", "🍔 Food & Eating Out", "👗 Fashion & Clothes", "🌦️ Weather & Seasons",
    "🇭🇺 Hungary & the EU", "🏛️ General Culture & Civilization"
]

LEVELS = {"A1 (Beginner)": "A1", "A2 (Pre-Int)": "A2", "B1 (Intermediate)": "B1", "B2 (Upper-Int)": "B2", "C1 (Advanced)": "C1", "C2 (Proficiency)": "C2"}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

# --- SESSION STATE ---
if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic", "intro_done", "feedback_level"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

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
        B1: 'Twenty-three Topics for Teenagers'.
        B2: '1000 Questions B2', 'Színes B2'.
        C1/C2: '1000 Questions C1', 'Színes C1'.
        Topic '🏛️ General Culture & Civilization': You are a helpful tutor. Focus on countries, customs, and facts.
        IMPORTANT: Track the conversation flow. Do NOT ask the same question twice. Remember what has been discussed.
        """
        
        mode_instr = f"Mode: {st.session_state.current_mode}. Level: {lv}. Topic: {topic}. {kb_mapping}"
        hist = [{"role": "system", "content": f"{system_instruction} {mode_instr}"}]
        hist.extend(st.session_state.messages[-6:]) # Több emlékezet az ismétlések ellen
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=20)
            return r.json()['choices'][0]['message']['content']
        except:
            return "*(Buddy smiles)* A quick connection glitch! Can you repeat that?"

    # --- SIDEBAR: CONTROL PANEL ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level or "Balanced")
        st.markdown("---")
        
        if st.session_state.user_level:
            st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
        if st.session_state.current_mode:
            st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        if st.session_state.chat_topic:
            st.markdown(f"<div class='status-box'><b>Topic:</b> {st.session_state.chat_topic}</div>", unsafe_allow_html=True)
        
        if st.session_state.chat_topic:
            if st.button("⬅️ Back to topics menu"):
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        if st.session_state.user_level:
            if st.button("🔄 Change Level/Mode"):
                st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        st.markdown("<div class='help-card'><b>🆘 Stuck?</b> Type 'HELP' for tips!</div>", unsafe_allow_html=True)
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-text'>I am here to help you <b>practise English speaking</b> and focus on <b>real-life communication</b> (and exam preparation).<br><br>Whether you want to <b>debate</b>, roleplay a <b>situation</b>, describe a <b>picture</b>, or just have a <b>friendly chat</b>, I'm ready!</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 2, 1])
        if c2.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l):
                st.session_state.user_level = l
                st.rerun()
        if st.button("🔍 Assess my level"):
            st.session_state.user_level = "Determining..."
            st.session_state.current_mode = "Assessment"
            st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello! Start assessment.", "Level Evaluator")})
            st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang & Idioms"]
        cols = st.columns(2)
        for i, m in enumerate(m_list):
            if cols[i%2].button(m):
                st.session_state.current_mode = m
                st.rerun()

    elif not st.session_state.chat_topic and st.session_state.current_mode != "Assessment":
        st.subheader("Select topic:")
        t_cols = st.columns(2)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%2].button(topic):
                st.session_state.chat_topic = topic
                with st.spinner('Buddy is getting ready...'):
                    ans = call_groq("Hello! Let's start.", "Partner")
                    st.session_state.messages.append({"role": "assistant", "content": ans})
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
            try:
                r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers={"Authorization": f"Bearer {api_key}"}, files={"file": ("audio.wav", audio_data['bytes'])}, data={"model": "whisper-large-v3", "language": "en"})
                user_msg = r.json().get("text", "")
            except: user_msg = "ERROR_AUDIO"

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner('Thinking...'):
                ans = call_groq(user_msg, "Partner")
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    st.markdown("<div class='footer-note'>Please note: SpeakingBuddy is an AI and can make mistakes.<br>© 2026 SpeakingBuddy by ReHi</div>", unsafe_allow_html=True)
