import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- CSS: VÉGLEGES DESIGN ÉS MOBIL OPTIMALIZÁLÁS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 80px; margin-bottom: 5px; }
    .main-title { font-family: 'Helvetica Neue', sans-serif; font-weight: 800; margin-bottom: 0px; }
    .sub-title { font-style: italic; opacity: 0.8; margin-top: 0px; margin-bottom: 25px; }
    .welcome-text { text-align: center; font-size: 1.1em; line-height: 1.6; margin-bottom: 25px; max-width: 600px; margin-left: auto; margin-right: auto; }
    
    /* GOMBOK DESIGNJA */
    .stButton > button { 
        border-radius: 8px !important; 
        width: 100% !important;
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
        padding: 10px !important;
    }
    
    /* START GOMB KÖZÉPRE */
    .start-container {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    div.stButton > button:has(div:contains("🚀")) {
        max-width: 250px !important;
        font-size: 1.2em !important;
        height: 60px !important;
    }

    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.15);
        font-size: 0.85em;
    }
    
    .help-hint-bar {
        text-align: center; font-size: 0.8em; color: #e67e22; 
        font-weight: bold; margin-bottom: 10px; border: 1px dashed #e67e22;
        border-radius: 5px; padding: 5px;
    }

    .footer-note { text-align: center; color: grey; font-size: 11px; margin-top: 50px; opacity: 0.8; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
TOPICS = ["🎲 Surprise Me (Free Chat)", "🏠 Family & Friends", "🏘️ Home & Housing", "🐾 Animals & Pets", "🌍 Environment & Nature", "🏙️ Lifestyle & Daily Routine", "💼 Jobs & Career", "🎭 Culture & Entertainment", "🏫 Education & Languages", "🛍️ Shopping & Consumer Society", "✈️ Travel & Transport", "⚽ Health & Sport", "💻 Tech & Media", "🍔 Food & Eating Out", "👗 Fashion & Clothes", "🌦️ Weather & Seasons", "🇭🇺 Hungary & the EU", "🏛️ General Culture & Civilization"]
LEVELS = {"A1 (Beginner)": "A1", "A2 (Pre-Int)": "A2", "B1 (Intermediate)": "B1", "B2 (Upper-Int)": "B2", "C1 (Advanced)": "C1", "C2 (Proficiency)": "C2"}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic", "intro_done", "feedback_level", "last_audio_id"]:
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
        mode_instr = f"Level: {st.session_state.user_level}. Mode: {st.session_state.current_mode}. Topic: {st.session_state.chat_topic}."
        hist = [{"role": "system", "content": f"{system_instruction} {mode_instr} Stay conversational."}]
        hist.extend(st.session_state.messages[-10:])
        if prompt: hist.append({"role": "user", "content": prompt})
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=15)
            return r.json()['choices'][0]['message']['content']
        except: return "*(Buddy smiles)* A quick glitch. Let's try again!"

    # --- SIDEBAR (Asztali nézethez) ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.markdown("<div style='color:#e67e22; font-weight:bold;'>🆘 HELP / HINT available!</div>", unsafe_allow_html=True)
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher"], value=st.session_state.feedback_level or "Balanced")
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-text'>I am here to help you <b>practise English speaking</b> and focus on <b>real-life communication</b> (and exam preparation).<br><br>Whether you want to <b>debate</b>, roleplay a <b>situation</b>, describe a <b>picture</b>, or just have a <b>friendly chat</b>, I'm ready!</div>", unsafe_allow_html=True)
        
        # START GOMB KÖZÉPRE
        _, start_col, _ = st.columns([1, 2, 1])
        if start_col.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l):
                st.session_state.user_level = l
                st.rerun()
        st.markdown("---")
        _, ac, _ = st.columns([1, 2, 1])
        if ac.button("🔍 Assess my level"):
            st.session_state.user_level = "Determining..."
            st.session_state.current_mode = "Assessment"
            st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm Buddy. To assess your level, let's chat. Tell me, what's your favorite way to spend a weekend?"})
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
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!", "Start")})
                st.rerun()
    else:
        # MOBIL NAVIGÁCIÓ ÉS EMLÉKEZTETŐ
        st.markdown("<div class='help-hint-bar'>💡 Stuck? Type 'HELP' for tips or 'HINT' for a word!</div>", unsafe_allow_html=True)
        top_c1, top_c2 = st.columns(2)
        if top_c1.button("⬅️ Topics"):
            st.session_state.chat_topic = None
            st.session_state.messages = []
            st.rerun()
        if top_c2.button("🔄 Reset"):
            st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
            st.session_state.messages = []
            st.rerun()
        
        st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level} | <b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio_in = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text_in = st.chat_input("Write to Buddy...")
        
        input_proc = None
        if audio_in:
            a_id = hash(audio_in['bytes'])
            if a_id != st.session_state.last_audio_id:
                st.session_state.last_audio_id = a_id
                try:
                    r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", headers={"Authorization": f"Bearer {api_key}"}, files={"file": ("audio.wav", audio_in['bytes'])}, data={"model": "whisper-large-v3", "language": "en"})
                    input_proc = r.json().get("text", "")
                except: st.error("Audio error.")
        elif text_in: input_proc = text_in

        if input_proc:
            st.session_state.messages.append({"role": "user", "content": input_proc})
            with st.spinner('Thinking...'):
                ans = call_groq(input_proc, "Partner")
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    st.markdown("<div class='footer-note'><b>© 2026 SpeakingBuddy by ReHi</b></div>", unsafe_allow_html=True)
