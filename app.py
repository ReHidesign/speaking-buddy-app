import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

st.set_page_config(page_title="Speaking Buddy v6", page_icon="🇬🇧")

# --- KONFIGURÁCIÓ (Bővített témák) ---
TOPICS = [
    "✈️ Travel & Customs", "🍔 Restaurant & Food", "🎬 Entertainment", 
    "⚽ Health & Sports", "💻 Tech & Social Media", "🏠 Family & Home",
    "💼 Work & Job Interview", "🌍 Global Issues", "🎭 Art & Fashion",
    "🏫 School & OKTV", "🛍️ Shopping & Complaints", "🏥 At the Doctor"
]

LEVELS = {
    "A1 (Beginner)": "Very simple, short sentences.",
    "A2 (Pre-Intermediate)": "Simple English, connected thoughts.",
    "B1 (Intermediate)": "Standard English, everyday topics.",
    "B2 (Upper-Intermediate)": "Natural, fast, idiomatic English.",
    "C1 (Advanced)": "Sophisticated, nuanced vocabulary.",
    "C2 (Proficiency)": "Academic, complex structures, professional/OKTV level."
}

# --- API ÉS MEMÓRIA ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    # Állapotok inicializálása
    for key in ["messages", "current_mode", "user_level", "chat_topic"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    # --- FUNKCIÓK ---
    def speak_text(text):
        clean_text = re.sub(r'[^\x00-\x7F]+', '', text) # Emojik ki
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
        full_instr = f"{system_instruction} Current Level: {level_instr}. NO emojis. If user says 'HELP', correct them first."
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
        st.sidebar.success(f"Level: {st.session_state.user_level}")
    if st.sidebar.button("🗑️ Full Reset"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    # --- FLOW ---
    # 1. Szint
    if not st.session_state.user_level:
        st.subheader("Select your English level:")
        cols = st.columns(3)
        for i, lvl in enumerate(LEVELS.keys()):
            if cols[i%3].button(lvl, use_container_width=True):
                st.session_state.user_level = lvl
                st.rerun()
    
    # 2. Mód
    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_cols = st.columns(4)
        for i, m in enumerate(["📈 Test", "🎮 Game", "🖼️ Picture", "💬 Chat"]):
            if m_cols[i].button(m, use_container_width=True):
                st.session_state.current_mode = m
                st.rerun()

    # 3. Téma választás (Bármelyik módhoz!)
    elif not st.session_state.chat_topic:
        st.subheader(f"Choose a topic for your {st.session_state.current_mode} session:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = topic
                
                # Instrukció generálása a mód + téma alapján
                prompts = {
                    "Chat": f"Let's talk about {topic}. Start a friendly discussion.",
                    "Game": f"We are in a roleplay about {topic}. You start the scene with a problem or situation.",
                    "Picture": f"The topic is {topic}. Describe a very detailed imaginary scene and ask me to describe it back.",
                    "Test": f"Ask me 3 complex questions about {topic} to test my skills."
                }
                ans = call_groq(prompts[st.session_state.current_mode], "You are a professional partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # 4. A Chat felület
    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        st.write("---")
        input_col, mic_col = st.columns([0.85, 0.15])
        with mic_col:
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"rec_{len(st.session_state.messages)}")
        with input_col:
            text_input = st.chat_input("Speak or write...")

        user_msg = text_input if text_input else (call_whisper(audio_input['bytes']) if audio_input else None)

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            instr = f"Partner in {st.session_state.current_mode} mode about {st.session_state.chat_topic}."
            if "HELP" in user_msg.upper(): instr = "CORRECT GRAMMAR FIRST, then continue conversation."
            answer = call_groq(user_msg, instr)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<p style='text-align: center; color: grey; font-size: 10px;'>© 2024 Speaking Buddy App - OKTV & Exam Prep Edition</p>", unsafe_allow_html=True)
