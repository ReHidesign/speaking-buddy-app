import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

st.set_page_config(page_title="Speaking Buddy v7", page_icon="🇬🇧")

# --- KONFIGURÁCIÓ ---
TOPICS = [
    "✈️ Travel & Customs", "🍔 Restaurant & Food", "🎬 Entertainment", 
    "⚽ Health & Sports", "💻 Tech & Social Media", "🏠 Family & Home",
    "🌍 Global Issues", "🎭 Art & Fashion", "💼 Career & Work"
]

LEVELS = {
    "A1 (Beginner)": "Very simple, short sentences.",
    "A2 (Pre-Intermediate)": "Simple English, connected thoughts.",
    "B1 (Intermediate)": "Standard English, everyday topics.",
    "B2 (Upper-Intermediate)": "Natural, fast, idiomatic English.",
    "C1 (Advanced)": "Sophisticated, nuanced vocabulary.",
    "C2 (Proficiency)": "Academic, complex structures, professional level."
}

# --- API ÉS MEMÓRIA ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    # --- FUNKCIÓK ---
    def speak_text(text):
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
        full_instr = f"{system_instruction} Current Level: {level_instr}. NO emojis. IMPORTANT: If user says 'HELP', correct them first."
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.5}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- SIDEBAR (Visszakerült a Help panel és a ReHi név) ---
    with st.sidebar:
        st.title("🇬🇧 Speaking Buddy")
        st.info("Created by: **ReHi**")
        
        st.markdown("---")
        st.warning("💡 **Tip:** Write '**HELP**' in the chat if you need grammar advice or translations!")
        
        if st.session_state.user_level:
            st.success(f"Level: {st.session_state.user_level}")
        
        if st.button("🗑️ Full Reset"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- FLOW ---
    # 1. Szintválasztás (Vízszintes elrendezés)
    if not st.session_state.user_level:
        st.subheader("Select your English level:")
        cols = st.columns(3)
        lvls = list(LEVELS.keys())
        for i in range(len(lvls)):
            if cols[i % 3].button(lvls[i], use_container_width=True):
                st.session_state.user_level = lvls[i]
                st.rerun()
    
    # 2. Módválasztás
    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_cols = st.columns(4)
        for i, m in enumerate(["📈 Test", "🎮 Game", "🖼️ Picture", "💬 Chat"]):
            if m_cols[i].button(m, use_container_width=True):
                st.session_state.current_mode = m
                st.rerun()

    # 3. Témaválasztás (Gombok minden módhoz)
    elif not st.session_state.chat_topic:
        st.subheader(f"Choose a topic for your {st.session_state.current_mode} session:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx % 3].button(topic, use_container_width=True):
                st.session_state.chat_topic = topic
                prompts = {
                    "Chat": f"Start a friendly discussion about {topic}.",
                    "Game": f"We are in a roleplay about {topic}. Start the scene as a character with a goal.",
                    "Picture": f"The topic is {topic}. Describe a scene for me to visualize and discuss.",
                    "Test": f"Ask 3 challenging questions about {topic}."
                }
                ans = call_groq(prompts[st.session_state.current_mode], "Be a helpful language partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # 4. Aktív Chat felület
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
            instr = f"Language partner in {st.session_state.current_mode} mode about {st.session_state.chat_topic}."
            if "HELP" in user_msg.upper(): 
                instr = "First, correct any grammar or spelling mistakes clearly. Then continue the conversation."
            answer = call_groq(user_msg, instr)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    # Copyright szekció frissítve
    st.markdown(f"<br><hr><p style='text-align: center; color: grey; font-size: 12px;'>© 2026 Speaking Buddy App by ReHi | All Rights Reserved</p>", unsafe_allow_html=True)
