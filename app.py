import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random
import hashlib

st.set_page_config(page_title="Speaking Buddy", page_icon="🤖", layout="centered")

# --- DESIGN & MODERN AVATAR ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    
    /* Buddy modern, pulzáló avatárja */
    .avatar-container {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    .buddy-sphere {
        width: 120px;
        height: 120px;
        background: linear-gradient(135deg, #6e8efb, #a777e3);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 60px;
        box-shadow: 0 10px 20px rgba(110, 142, 251, 0.3);
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 10px 20px rgba(110, 142, 251, 0.3); }
        50% { transform: scale(1.05); box-shadow: 0 15px 30px rgba(110, 142, 251, 0.5); }
        100% { transform: scale(1); box-shadow: 0 10px 20px rgba(110, 142, 251, 0.3); }
    }

    .main-title { color: #1e3a5a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 800; text-align: center; }
    .sub-title { color: #666; text-align: center; margin-bottom: 30px; font-style: italic; }
    .status-box { background-color: #ffffff; padding: 12px; border-radius: 12px; border-left: 5px solid #6e8efb; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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
    # Session state
    keys = ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done", "feedback_level", "last_audio_id"]
    for k in keys:
        if k not in st.session_state: st.session_state[k] = None
    if st.session_state.messages is None: st.session_state.messages = []
    if st.session_state.feedback_level is None: st.session_state.feedback_level = "Balanced"

    def transcribe_audio(audio_bytes):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": "whisper-large-v3", "language": "en"}
        try:
            r = requests.post(url, headers=headers, files=files, data=data)
            return r.json().get("text", "")
        except: return ""

    def speak_text(text):
        clean = re.sub(r'\(.*?\)', '', text).replace("*", "").strip()
        tts = gTTS(text=clean if clean else "I'm listening.", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        mode_instr = ""
        if st.session_state.current_mode == "Situation":
            mode_instr = "ROLEPLAY: Briefly set the scene, then start talking in character immediately."
        elif st.session_state.current_mode == "Assessment":
            mode_instr = "ASSESSMENT: Ask questions one by one to evaluate the user's level."

        full_sys = f"{system_instruction} {mode_instr} Level: {st.session_state.user_level}. Feedback: {st.session_state.feedback_level}."
        hist = [{"role": "system", "content": full_sys}]
        hist.extend(st.session_state.messages[-5:])
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, data=json.dumps({"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.7}), timeout=15)
            return r.json()['choices'][0]['message']['content']
        except:
            return "*(Buddy smiles)* My connection flickered for a second. What were you saying?"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Buddy's feedback:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
        st.markdown("---")
        
        if st.session_state.user_level:
            st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
            if st.button("🔄 Change Level"):
                st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        if st.session_state.current_mode:
            st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
            if st.button("🏠 Change Mode/Topic"):
                st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
        
        st.markdown("---")
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("""
            <div class="avatar-container">
                <div class="buddy-sphere">🤖</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<h1 class='main-title'>Speaking Buddy</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-title'>your interactive language partner</p>", unsafe_allow_html=True)
        st.write("### Welcome!")
        st.write("I am here to help you practice **English speaking** and focus on **real-life communication**. Whether you want to **debate**, roleplay a **situation**, describe a **picture**, or just have a **friendly chat**, I'm ready!")
        if st.button("Let's start! 🚀", use_container_width=True):
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
            st.session_state.user_level = "Evaluation in progress"
            st.session_state.current_mode = "Assessment"
            ans = call_groq("Hello! Let's start the level assessment conversation.", "Level Evaluator.")
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
                if st.session_state.current_mode == "Picture":
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_exam_photo_{st.session_state.chat_topic}?width=800&height=600&seed={random.randint(1,99)}"
                ans = call_groq(f"Start a {st.session_state.current_mode} about {st.session_state.chat_topic}.", "Language Partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    else:
        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio_data = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text_input = st.chat_input("Message Buddy...")
        
        user_msg = None
        if audio_data:
            c_id = hashlib.md5(audio_data['bytes']).hexdigest()
            if c_id != st.session_state.last_audio_id:
                st.session_state.last_audio_id = c_id
                user_msg = transcribe_audio(audio_data['bytes'])
        elif text_input: user_msg = text_input

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner('Thinking...'):
                answer = call_groq(user_msg, "Partner.")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy v32 | ReHi</p>", unsafe_allow_html=True)
