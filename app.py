import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

st.set_page_config(page_title="Speaking Buddy v4", page_icon="🇬🇧")

# --- KONFIGURÁCIÓ ---
TOPICS = [
    "✈️ Travel & Tourism", "🍔 Food & Cooking", "🎬 Movies & Entertainment", 
    "⚽ Sports & Health", "💻 Technology & AI", "🏠 Home & Family",
    "🎓 Education & Learning", "💼 Work & Career", "🌍 Environment",
    "⚖️ Politics & Society", "🎭 Arts & Culture"
]

LEVELS = {
    "A1 (Beginner)": "Very simple words, short sentences.",
    "A2 (Pre-Intermediate)": "Simple English, connected sentences.",
    "B1 (Intermediate)": "Standard everyday English.",
    "B2 (Upper-Intermediate)": "Natural, fast English, phrasal verbs.",
    "C1 (Advanced)": "Sophisticated English, nuanced expressions.",
    "C2 (Proficiency)": "Academic, complex structures, professional vocabulary for OKTV level."
}

# --- API ÉS MEMÓRIA ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    if "messages" not in st.session_state: st.session_state.messages = []
    if "current_mode" not in st.session_state: st.session_state.current_mode = None
    if "user_level" not in st.session_state: st.session_state.user_level = None
    if "chat_topic" not in st.session_state: st.session_state.chat_topic = None

    # --- FUNKCIÓK ---
    def speak_text(text):
        # Emojik eltávolítása a felolvasás előtt
        clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
        tts = gTTS(text=clean_text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_whisper(audio_bytes):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav"), "model": (None, "whisper-large-v3"), "language": (None, "en")}
        try:
            response = requests.post(url, headers=headers, files=files)
            return response.json().get("text", "")
        except: return None

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        level_instr = LEVELS.get(st.session_state.user_level, "Natural English")
        full_instr = f"{system_instruction} Level: {level_instr}. IMPORTANT: No emojis. If the user asks for HELP, start with a friendly grammar correction."
        
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.5}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- SIDEBAR ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    if st.session_state.user_level:
        st.sidebar.info(f"Level: **{st.session_state.user_level}**")
    
    st.sidebar.write("---")
    if st.sidebar.button("🆘 Get Help (Grammar Check)"):
        st.sidebar.warning("Type 'HELP' at the end of your message!")
    
    if st.sidebar.button("🗑️ Reset Everything"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    # --- 1. LÉPÉS: SZINT VÁLASZTÁS ---
    if not st.session_state.user_level:
        st.subheader("Welcome! Please set your level:")
        cols = st.columns(2)
        with cols[0]:
            st.markdown("### Manual Selection")
            for lvl in LEVELS.keys():
                if st.button(lvl, use_container_width=True):
                    st.session_state.user_level = lvl
                    st.rerun()
        with cols[1]:
            st.markdown("### Not sure?")
            if st.button("🔍 Assess my level (3 questions)", use_container_width=True):
                st.session_state.user_level = "Assessment in progress"
                ans = call_groq("Start assessment.", "Ask 3 questions to find the user's CEFR level.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- 2. LÉPÉS: MÓD VÁLASZTÁS ---
    elif st.session_state.user_level and not st.session_state.current_mode:
        st.subheader("Pick a mode:")
        m_cols = st.columns(4)
        modes = ["📈 Test", "🎮 Game", "🖼️ Picture", "💬 Chat"]
        for i, m in enumerate(modes):
            if m_cols[i].button(m, use_container_width=True):
                st.session_state.current_mode = m
                if m != "Chat":
                    ans = call_groq("Hello!", f"Start a {m} session.")
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- 3. LÉPÉS: TÉMA VÁLASZTÁS (Chat) ---
    elif st.session_state.current_mode == "Chat" and not st.session_state.chat_topic:
        st.subheader("Choose a topic:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx % 3].button(topic, use_container_width=True):
                st.session_state.chat_topic = topic
                ans = call_groq(f"Let's talk about {topic}.", "Be a partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- CHAT FÜLET ---
    if st.session_state.user_level and (st.session_state.current_mode or st.session_state.user_level == "Assessment in progress"):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        st.write("---")
        input_col, mic_col = st.columns([0.85, 0.15])
        with mic_col:
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"rec_{len(st.session_state.messages)}")
        
        text_input = st.chat_input("Message Buddy...")
        
        user_msg = text_input if text_input else (call_whisper(audio_input['bytes']) if audio_input else None)

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            
            # Dinamikus instrukció a mód alapján
            base = f"Partner in {st.session_state.current_mode} mode."
            if "HELP" in user_msg.upper():
                base = "FIRST: Correct mistakes briefly. THEN: Continue the talk."
            
            answer = call_groq(user_msg, base)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<p style='text-align: center; color: grey; font-size: 10px;'>© 2024 Speaking Buddy App</p>", unsafe_allow_html=True)
