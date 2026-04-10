import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random
import hashlib

# --- PAGE CONFIG (Ez segít a mobil elnevezésben) ---
st.set_page_config(page_title="SpeakingBuddy", page_icon="🤖", layout="centered")

# --- CSS: MENÜ ELREJTÉSE ÉS DESIGN ---
st.markdown("""
    <style>
    /* A Streamlit menü és a kód megtekintésének elrejtése */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .stApp { background-color: #f8f9fa; }
    .buddy-header { text-align: center; padding: 20px; }
    .buddy-avatar { font-size: 100px; margin-bottom: 10px; }
    .main-title { color: #1e3a5a; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; margin-bottom: 0px; }
    .sub-title { color: #666; font-style: italic; margin-top: 0px; margin-bottom: 30px; }
    .welcome-text { text-align: center; font-size: 1.1em; line-height: 1.6; margin-bottom: 25px; max-width: 600px; margin-left: auto; margin-right: auto; }
    .status-box { background-color: #ffffff; padding: 12px; border-radius: 12px; border-left: 5px solid #3498db; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); color: #2e4053; }
    .help-card { background-color: #fff4e5; padding: 15px; border-radius: 10px; border: 1px dashed #e67e22; color: #d35400; font-size: 13px; margin-top: 10px; }
    div.stButton > button { display: block; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]
LEVELS = {"A1 (Beginner)": "A1", "A2 (Pre-Int)": "A2", "B1 (Intermediate)": "B1", "B2 (Upper-Int)": "B2", "C1 (Advanced)": "C1", "C2 (Proficiency)": "C2"}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    # Session inicializálás
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
            r = requests.post(url, headers=headers, files=files, data=data, timeout=25)
            return r.json().get("text", "")
        except: return "ERROR_AUDIO"

    def speak_text(text):
        clean = re.sub(r'\(.*?\)', '', text).replace("*", "").strip()
        tts = gTTS(text=clean if clean else "I'm listening.", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        mode_instr = f"Mode: {st.session_state.current_mode}. Level: {st.session_state.user_level}."
        hist = [{"role": "system", "content": f"{system_instruction} {mode_instr}"}]
        hist.extend(st.session_state.messages[-4:])
        if prompt: hist.append({"role": "user", "content": prompt})
        
        try:
            r = requests.post(url, headers=headers, data=json.dumps({"model": "llama-3.3-70b-versatile", "messages": hist, "temperature": 0.7}), timeout=20)
            return r.json()['choices'][0]['message']['content']
        except:
            return "*(Buddy smiles)* I'm having a little lag. Could you please repeat your last message?"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Style:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
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
        st.markdown("<div class='help-card'><b>🆘 Stuck?</b> Type 'HELP' for grammar tips!</div>", unsafe_allow_html=True)
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>SpeakingBuddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.markdown("<div class='welcome-text'>I am here to help you practice <b>English speaking</b> and focus on <b>real-life communication</b> (and exam preparation).<br><br>Whether you want to <b>debate</b>, roleplay a <b>situation</b>, describe a <b>picture</b>, or just have a <b>friendly chat</b>, I'm ready!</div>", unsafe_allow_html=True)
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
        if st.button("🔍 Assess my level", use_container_width=True):
            st.session_state.user_level = "Determining..."
            st.session_state.current_mode = "Assessment"
            st.session_state.messages.append({"role": "assistant", "content": call_groq("Start assessment.", "Level Evaluator")})
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
        st.subheader(f"Select a topic:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = topic.split()[-1]
                if st.session_state.current_mode == "Picture":
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_exam_photo_{st.session_state.chat_topic}?seed={random.randint(1,99)}"
                st.session_state.messages.append({"role": "assistant", "content": call_groq(f"Start {st.session_state.current_mode}.", "Partner")})
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
        elif text_input:
            user_msg = text_input

        if user_msg:
            if user_msg == "ERROR_AUDIO":
                st.error("I couldn't process the audio. Please try typing your message!")
            else:
                st.session_state.messages.append({"role": "user", "content": user_msg})
                with st.spinner('Thinking...'):
                    ans = call_groq(user_msg, "Partner")
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    st.markdown("<br><hr><p style='text-align: center; color: grey; font-size: 10px;'>© 2026 SpeakingBuddy by ReHi</p>", unsafe_allow_html=True)
