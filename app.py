import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random
import hashlib

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #fafafa; }
    .buddy-container { text-align: center; padding: 10px; }
    .buddy-avatar { font-size: 70px; margin-bottom: 0px; }
    .main-title { color: #2e4053; margin-top: -10px; margin-bottom: 0px; }
    .sub-title { font-size: 1.2em; color: #555; margin-bottom: 20px; }
    .status-box { background-color: #e8f4f8; padding: 10px; border-radius: 10px; border-left: 5px solid #2980b9; margin-bottom: 10px; font-size: 14px; color: #2e4053; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIG ---
TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]
LEVELS = {"A1 (Beginner)": "A1", "A2 (Pre-Int)": "A2", "B1 (Intermediate)": "B1", "B2 (Upper-Int)": "B2", "C1 (Advanced)": "C1", "C2 (Proficiency)": "C2"}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done", "feedback_level", "last_audio_id"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []
    if st.session_state.feedback_level is None: st.session_state.feedback_level = "Balanced"

    def transcribe_audio(audio_bytes):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": "whisper-large-v3", "language": "en"}
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            return response.json().get("text", "")
        except: return ""

    def speak_text(text):
        speech_only = re.sub(r'\(.*?\)', '', text).replace("*", "").strip()
        if not speech_only: speech_only = "I'm listening."
        tts = gTTS(text=speech_only, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        mode_specific = ""
        if st.session_state.current_mode == "Situation":
            mode_specific = "Roleplay: Act as a partner, start the conversation immediately after setting the scene."
        elif st.session_state.current_mode == "Assessment":
            mode_specific = "Assessment: Ask 3 questions one-by-one to find the user's level."

        full_instr = f"{system_instruction} {mode_specific} Level: {st.session_state.user_level}."
        
        # Rövidített memória a hiba ellen
        history = [{"role": "system", "content": full_instr}]
        history.extend(st.session_state.messages[-4:]) 
        if prompt: history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        try:
            r = requests.post(url, headers=headers, data=json.dumps(data), timeout=15)
            return r.json()['choices'][0]['message']['content']
        except: 
            return "*(Buddy smiles)* I'm ready again. Please repeat your last thought!"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        if st.button("🔄 Change Level/Mode"):
            st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
            st.session_state.messages = []
            st.rerun()
        if st.button("🗑️ Full Reset"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-container'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>Speaking Buddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.write("### Welcome! 👋")
        st.write("I am here to help you practice English speaking and focus on **real-life communication**. Whether you want to **debate**, roleplay a **situation**, describe a **picture**, or just have a **friendly chat**, I'm ready!")
        if st.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Please set your English level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l, use_container_width=True):
                st.session_state.user_level = l
                st.rerun()
        st.markdown("---")
        if st.button("🔍 Assess my level (Chat with Buddy)", use_container_width=True):
            st.session_state.user_level = "Unknown"
            st.session_state.current_mode = "Assessment"
            ans = call_groq("Hello! Let's find my level.", "Level Assessor.")
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]
        cols = st.columns(2)
        for i, m in enumerate(m_list):
            if cols[i%2].button(m, use_container_width=True):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()

    elif not st.session_state.chat_topic and st.session_state.current_mode != "Assessment":
        st.subheader(f"Select a topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = topic.split()[-1]
                ans = call_groq(f"Start {st.session_state.current_mode} - {st.session_state.chat_topic}", "Partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    else:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio_data = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text_input = st.chat_input("Or type here...")
        
        user_msg = None
        if audio_data:
            c_id = hashlib.md5(audio_data['bytes']).hexdigest()
            if c_id != st.session_state.last_audio_id:
                st.session_state.last_audio_id = c_id
                user_msg = transcribe_audio(audio_data['bytes'])
        elif text_input: user_msg = text_input

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner('Buddy is thinking...'):
                answer = call_groq(user_msg, f"Mode: {st.session_state.current_mode}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
