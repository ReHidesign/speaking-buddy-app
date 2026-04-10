import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- DESIGN ÉS STÍLUS ---
st.markdown("""
    <style>
    .stApp { background-color: #fafafa; }
    .buddy-container { text-align: center; padding: 10px; }
    .buddy-avatar { font-size: 70px; margin-bottom: 0px; }
    .main-title { color: #2e4053; margin-top: -10px; margin-bottom: 0px; }
    .sub-title { font-size: 1.2em; color: #555; margin-bottom: 20px; }
    .status-box { background-color: #e8f4f8; padding: 10px; border-radius: 10px; border-left: 5px solid #2980b9; margin-bottom: 10px; font-size: 14px; }
    .help-card { background-color: #fff4e5; padding: 15px; border-radius: 10px; border: 1px dashed #e67e22; color: #d35400; font-size: 13px; }
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
    # Session állapota
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done", "feedback_level"]:
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
        # Kiszűrjük a zárójeles instrukciókat a felolvasásból
        speech_only = re.sub(r'\(.*?\)', '', text)
        speech_only = speech_only.replace("*", "").replace("?", ".").replace("!", ".").strip()
        tts = gTTS(text=speech_only if speech_only else "I'm listening", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        feedback_instr = {
            "Relaxed": "Only correct mistakes if explicitly asked. Focus on natural flow.",
            "Balanced": "Subtly correct major mistakes in your response. Be encouraging.",
            "Teacher Mode": "Act like a strict but kind tutor. Correct grammar mistakes clearly."
        }
        
        full_instr = (
            f"{system_instruction} Student level: {st.session_state.user_level}. "
            f"Feedback style: {feedback_instr[st.session_state.feedback_level]}. "
            "IF the student says 'HELP': Provide a short, clear grammar explanation about their last input. "
            "IF the student says 'finished' or 'done': Give a structured 'Task Summary' at the end. "
            "CONFIRMATION: You HAVE a voice (audio). If the student hears you, acknowledge it. "
            "STRICT: Put all non-spoken actions in brackets and italics: *(Buddy smiles)*. "
        )
        
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            result = response.json()
            if 'choices' in result:
                return result['choices'][0]['message']['content']
            else:
                return "*(Buddy looks puzzled)* I'm sorry, I had a brief connection issue. Could you repeat that?"
        except:
            return "*(Buddy apologizes)* I encountered a small technical glitch. Let's try again!"

    # --- SIDEBAR NAVIGÁCIÓ ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        
        st.session_state.feedback_level = st.select_slider(
            "Buddy's Feedback Level:",
            options=["Relaxed", "Balanced", "Teacher Mode"],
            value=st.session_state.feedback_level
        )
        
        st.markdown("---")
        st.markdown("""
            <div class='help-card'>
                <b>🆘 Need Help?</b><br>
                Type or say <b>'HELP'</b> anytime for grammar advice or translations!
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
        
        if st.session_state.user_level or st.session_state.current_mode:
            st.markdown("### 📍 Session Info:")
            if st.session_state.user_level: st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
            if st.session_state.current_mode: st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
        
        if st.session_state.current_mode:
            if st.button("🏠 Change Mode/Topic"):
                st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
        
        if st.session_state.user_level:
            if st.button("🔄 Change English Level"):
                st.session_state.user_level = st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        if st.button("🗑️ Full Reset"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- UI FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-container'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>Speaking Buddy</h1><p class='sub-title'>your interactive language partner</p></div>", unsafe_allow_html=True)
        st.write("### Welcome!")
        st.write("I'm here to practice speaking with you. Choose your level and a topic to begin!")
        if st.button("Let's go! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your English level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l, use_container_width=True):
                st.session_state.user_level = l
                st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang & Idioms"]
        cols = st.columns(2)
        for i, m in enumerate(m_list):
            if cols[i%2].button(m, use_container_width=True):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader(f"Select a topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%3].button(topic, use_container_width=True):
                with st.spinner('Buddy is preparing the session...'):
                    clean_t = topic.split()[-1]
                    st.session_state.chat_topic = clean_t
                    if st.session_state.current_mode == "Picture":
                        st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_exam_photo_{clean_t}?width=800&height=600&seed={random.randint(1,99)}"
                    ans = call_groq(f"Start a {st.session_state.current_mode} about {clean_t}.", "Language Partner.")
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    st.rerun()

    else:
        # CHAT INTERFACE
        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        input_col, mic_col = st.columns([0.85, 0.15])
        with mic_col:
            audio_data = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic_recorder")
        with input_col:
            text_input = st.chat_input("Message Buddy...")

        user_msg = None
        if audio_data:
            with st.spinner('Buddy is listening...'):
                user_msg = transcribe_audio(audio_data['bytes'])
        elif text_input:
            user_msg = text_input

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner('Buddy is thinking...'):
                answer = call_groq(user_msg, f"Mode: {st.session_state.current_mode}.")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            # AZONNALI RERUN: Megelőzi a hanghurok kialakulását azáltal, hogy törli a mic_recorder puffert
            st.rerun()

    st.markdown("<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy by ReHi</p>", unsafe_allow_html=True)
