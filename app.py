import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

# --- PAGE CONFIG ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- CSS: ÚJ, AGRESSZÍVABB STÍLUS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 80px; }
    .main-title { font-family: 'Helvetica Neue', sans-serif; font-weight: 800; margin-bottom: 0px; }
    .sub-title { font-style: italic; margin-bottom: 25px; opacity: 0.8; }
    
    /* START GOMB KÉNYSZERÍTÉSE: Kék háttér, fehér betű, középen */
    div.stButton > button:first-child[kind="primary"], 
    div.stButton > button:contains("🚀") {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 1.3em !important;
        height: 60px !important;
        width: 280px !important;
        margin: 0 auto !important;
        display: block !important;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3);
    }

    .status-box { 
        padding: 10px; border-radius: 10px; border-left: 5px solid #3498db; 
        margin-bottom: 10px; background-color: rgba(120, 120, 120, 0.1);
        font-size: 0.9em;
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

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # BUDDY TUDÁSA: Itt instruáljuk a könyvekre és az ismétlés elkerülésére
        kb_mapping = """
        Use the following knowledge bases:
        B1: 'Twenty-three Topics for Teenagers'.
        B2: '1000 Questions and Answers B2'.
        C1/C2: '1000 Questions C1'.
        CRITICAL: Never repeat a question you have already asked. Be varied and creative.
        """
        
        mode_instr = f"Mode: {st.session_state.current_mode}. Level: {st.session_state.user_level}. Topic: {st.session_state.chat_topic}. {kb_mapping}"
        hist = [{"role": "system", "content": f"{system_instruction} {mode_instr}"}]
        hist.extend(st.session_state.messages[-10:]) # 10 üzenetnyi memória az ismétlés ellen
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, json={"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.8}, timeout=15)
            return r.json()['choices'][0]['message']['content']
        except: return "*(Buddy smiles)* A minor connection glitch! Try again."

    # --- SIDEBAR: CONTROL PANEL ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        if st.session_state.user_level:
            st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
        if st.session_state.current_mode:
            st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        
        if st.session_state.chat_topic or st.session_state.current_mode == "Assessment":
            if st.button("⬅️ Back to Topics Menu"):
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; margin-bottom: 25px;'>Ready to improve your English? Let's start!</div>", unsafe_allow_html=True)
        
        # Itt próbáljuk a primary típust a kékítéshez
        if st.button("Let's start! 🚀", type="primary"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l):
                st.session_state.user_level = l
                st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang & Idioms"]
        cols = st.columns(2)
        for i, m in enumerate(m_list):
            if cols[i%2].button(m):
                st.session_state.current_mode = m
                st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader("Select topic:")
        t_cols = st.columns(2)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%2].button(topic):
                st.session_state.chat_topic = topic
                st.session_state.messages.append({"role": "assistant", "content": call_groq("Hello!", "Partner")})
                st.rerun()

    else:
        # Chat felület
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text = st.chat_input("Write to Buddy...")
        
        if text:
            st.session_state.messages.append({"role": "user", "content": text})
            with st.spinner('Thinking...'):
                ans = call_groq(text, "Partner")
                st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    st.markdown("""
        <div class='footer-note'>
            <b>SpeakingBuddy</b> is an AI practice partner. While advanced, it may occasionally make 
            mistakes. For certification, consult a human teacher.<br>
            <b>© 2026 SpeakingBuddy by ReHi</b>
        </div>
        """, unsafe_allow_html=True)
