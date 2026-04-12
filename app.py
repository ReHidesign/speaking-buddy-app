import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- CSS: STABIL KÉK DESIGN ---
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
    
    .stButton > button:hover {
        background-color: #2980b9 !important;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.4) !important;
    }

    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.15);
        font-size: 0.9em;
    }
    
    .help-card { 
        padding: 12px; border-radius: 10px; border: 1px dashed #e67e22; 
        background-color: rgba(230, 126, 34, 0.1); font-size: 13px; margin-bottom: 15px;
        color: #e67e22; font-weight: 600;
    }

    .footer-note { text-align: center; color: grey; font-size: 11px; margin-top: 50px; opacity: 0.8; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
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

if api_key:
    # State inicializálás
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
        kb_mapping = f"""
        Knowledge: B1: 'Twenty-three Topics'. B2: '1000 Questions B2', 'Színes B2'. C1/C2: '1000 Questions C1'.
        CRITICAL: Follow {st.session_state.user_level} level criteria. Never repeat yourself. Keep flow natural.
        """
        hist = [{"role": "system", "content": f"{system_instruction} {kb_mapping} Mode: {st.session_state.current_mode}. Topic: {st.session_state.chat_topic}"}]
        hist.extend(st.session_state.messages[-10:])
        if prompt: hist.append({"role": "user", "content": prompt})
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.7}, timeout=15)
            return r.json()['choices'][0]['message']['content']
        except: return "*(Buddy smiles)* A quick glitch. What was that again?"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.markdown("<div class='help-card'><b>🆘 Stuck?</b><br>Type 'HELP' for tips or 'HINT' if you need a word!</div>", unsafe_allow_html=True)
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher"], value=st.session_state.feedback_level or "Balanced")
        st.markdown("---")
        if st.session_state.user_level: st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
        if st.session_state.current_mode: st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        if st.session_state.chat_topic: st.markdown(f"<div class='status-box'><b>Topic:</b> {st.session_state.chat_topic}</div>", unsafe_allow_html=True)
        
        if st.session_state.user_level:
            if st.button("🔄 Restart Setup"):
                st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-text'>I am here to help you <b>practise English speaking</b>.<br><br>Whether you want to <b>debate</b>, roleplay a <b>situation</b>, describe a <b>picture</b>, or just have a <b>friendly chat</b>, I'm ready!</div>", unsafe_allow_html=True)
        if st.button("Let's start! 🚀"):
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
            st.session_state.messages.append({"role": "assistant", "content": "Hello! I'm Buddy. To assess your level, let's chat a bit. Tell me, what's your favorite way to spend a weekend?"})
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
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!", "Start Conversation")})
                st.rerun()
    else:
        # Chat interface
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        # Input handling
        audio_in = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text_in = st.chat_input("Write to Buddy...")
        
        input_to_process = None
        
        # Audio logic with loop-prevention
        if audio_in:
            audio_id = hash(audio_in['bytes'])
            if audio_id != st.session_state.last_audio_id:
                st.session_state.last_audio_id = audio_id
                with st.spinner('Buddy is listening...'):
                    try:
                        r = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", 
                                         headers={"Authorization": f"Bearer {api_key}"}, 
                                         files={"file": ("audio.wav", audio_in['bytes'])}, 
                                         data={"model": "whisper-large-v3", "language": "en"})
                        input_to_process = r.json().get("text", "")
                    except: st.error("Audio error. Try typing!")

        if text_in:
            input_to_process = text_in

        if input_to_process:
            st.session_state.messages.append({"role": "user", "content": input_to_process})
            with st.spinner('Thinking...'):
                response = call_groq(input_to_process, "Speaking Partner")
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    st.markdown("<div class='footer-note'><b>SpeakingBuddy</b> v70 | © 2026 ReHi</div>", unsafe_allow_html=True)
