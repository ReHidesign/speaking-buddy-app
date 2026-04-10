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

# --- DESIGN (v33-as alapok megtartva) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 100px; margin-bottom: 10px; }
    .main-title { color: #1e3a5a; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; margin-bottom: 0px; }
    .sub-title { color: #666; font-style: italic; margin-top: 0px; margin-bottom: 30px; }
    .welcome-text { text-align: center; font-size: 1.1em; line-height: 1.6; margin-bottom: 20px; }
    .status-box { background-color: #ffffff; padding: 12px; border-radius: 12px; border-left: 5px solid #3498db; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #2e4053; }
    .help-card { background-color: #fff4e5; padding: 15px; border-radius: 10px; border: 1px dashed #e67e22; color: #d35400; font-size: 13px; margin-top: 10px; }
    div.stButton > button { display: block; margin: 0 auto; }
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
            r = requests.post(url, headers=headers, files=files, data=data, timeout=10)
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
            mode_instr = "ROLEPLAY: Be a partner, act immediately in character."
        elif st.session_state.current_mode == "Assessment":
            mode_instr = "ASSESSMENT: Ask one question at a time to check user level."

        full_sys = f"{system_instruction} {mode_instr} Level: {st.session_state.user_level}. Feedback: {st.session_state.feedback_level}."
        
        # STABILITÁS: Csak az utolsó 4 üzenetet küldjük el, hogy ne legyen időtúllépés
        hist = [{"role": "system", "content": full_sys}]
        hist.extend(st.session_state.messages[-4:])
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, data=json.dumps({"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.7}), timeout=15)
            res = r.json()
            if 'choices' in res: return res['choices'][0]['message']['content']
            return "*(Buddy smiles)* My ears failed me for a second. Can you say that again?"
        except:
            return "*(Buddy nods)* I lost the connection for a moment. Please continue!"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
        st.markdown("---")
        
        if st.session_state.user_level or st.session_state.current_mode:
            st.markdown("### 📍 Current Status:")
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

        st.markdown("<div class='help-card'><b>🆘 Help:</b> Say <b>'HELP'</b> for grammar tips!</div>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>Speaking Buddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-text'>I am here to help you practice <b>English speaking</b> and focus on <b>real-life communication</b>.<br>Whether you want to <b>debate</b>, roleplay a <b>situation</b>, describe a <b>picture</b>, or just have a <b>friendly chat</b>, I'm ready!</div>", unsafe_allow_html=True)
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
            st.session_state.user_level = "Determining..."
            st.session_state.current_mode = "Assessment"
            ans = call_groq("Hello! Let's talk to find my level.", "Level Evaluator.")
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang & Idioms"]
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
        text_input = st.chat_input("Write to Buddy...")
        
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
                answer = call_groq(user_msg, "Partner.")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy v34 | ReHi</p>", unsafe_allow_html=True)
