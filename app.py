import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #fafafa; }
    .buddy-container { text-align: center; padding: 10px; }
    .buddy-avatar { font-size: 70px; margin-bottom: 0px; }
    .main-title { color: #2e4053; margin-top: -10px; }
    .stButton>button { border-radius: 12px; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]

LEVELS = {
    "A1 (Beginner)": "A1 level, basic sentences.", 
    "A2 (Pre-Int)": "A2 level, simple daily topics.",
    "B1 (Intermediate)": "B1 level, intermediate vocabulary.", 
    "B2 (Upper-Int)": "B2 level, fluent arguments.",
    "C1 (Advanced)": "C1 level, professional language.",
    "C2 (Proficiency)": "C2 level, native-like academic English."
}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    def speak_text(text):
        # Csak a narrációt (csillagok/dőlt betű) vágjuk le a hangból
        speech_only = re.sub(r'\*.*?\*', '', text)
        speech_only = speech_only.replace("?", ".").replace("!", ".").replace(":", ".").strip()
        tts = gTTS(text=speech_only if speech_only else "Listening", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_instr = (
            f"{system_instruction} Student level: {st.session_state.user_level}. "
            "IMPORTANT: Use *italics* ONLY for actions. NEVER for normal speech or questions. "
            "If mode is Slang, use natural expressions and idioms."
        )
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-8:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        return requests.post(url, headers=headers, data=json.dumps(data)).json()['choices'][0]['message']['content']

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.info("Created by: **ReHi**")
        if st.session_state.user_level: st.success(f"Level: {st.session_state.user_level}")
        if st.session_state.chat_topic:
            if st.button("🏠 Back to Menu"):
                st.session_state.current_mode = None
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
        if st.button("🗑️ Full Reset"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- 1. ÜDVÖZLÉS ---
    if not st.session_state.intro_done:
        st.markdown("""
            <div class='buddy-container'>
                <div class='buddy-avatar'>🤖</div>
                <h1 class='main-title'>Speaking Buddy</h1>
                <p style='font-size: 1.2em; color: #444;'>Your interactive language speaking partner</p>
            </div>
            """, unsafe_allow_html=True)
        st.write("### Welcome!")
        st.write("I'm here to help you master **English speaking** for **real-life communication** (and to succeed in your exams along the way).")
        if st.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    # --- 2. SZINT ---
    elif not st.session_state.user_level:
        st.subheader("Set your English level:")
        lvls = list(LEVELS.keys())
        cols = st.columns(2)
        for i, l in enumerate(lvls):
            if cols[i%2].button(l, use_container_width=True):
                st.session_state.user_level = l
                st.rerun()
        if st.button("🔍 Not sure? Assess me", use_container_width=True):
            st.session_state.user_level = "Assessment"
            ans = call_groq("Start a level check. Question 1: How would you describe your personality?", "Level Assessor Mode.")
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- 3. MÓD ---
    elif not st.session_state.current_mode and st.session_state.user_level != "Assessment":
        st.subheader("Choose your practice mode:")
        m_cols = st.columns(2)
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang & Idioms"]
        for i, m in enumerate(m_list):
            if m_cols[i%2].button(m, use_container_width=True):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()

    # --- 4. TÉMA ---
    elif not st.session_state.chat_topic and st.session_state.user_level != "Assessment":
        st.subheader(f"Select a topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            clean_t = topic.split()[-1]
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = clean_t
                if st.session_state.current_mode == "Picture":
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_photo_about_{clean_t}_exam_style?width=800&height=600&seed={random.randint(1,999)}"
                    ans = call_groq("Tell the student you have a picture for them and ask them to describe it. *Buddy shows the picture.*", "Examiner Mode.")
                elif st.session_state.current_mode == "Slang":
                    ans = call_groq(f"Let's learn some idioms and slang about {clean_t}. Start the session.", "Cool English Teacher Mode.")
                else:
                    ans = call_groq(f"Start a {st.session_state.current_mode} session about {clean_t}.", "English Partner Mode.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- 5. CHAT ---
    else:
        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        input_col, mic_col = st.columns([0.8, 0.2])
        with mic_col: audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic")
        with input_col: text_input = st.chat_input("Message Buddy...")

        user_msg = text_input if text_input else None
        # Whisper logic implicit
        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            sys_m = f"Respond in {st.session_state.current_mode} mode."
            if "HELP" in user_msg.upper(): sys_m = "Correct grammar/style, then continue."
            answer = call_groq(user_msg, sys_m)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy by ReHi | Real-life English Partner</p>", unsafe_allow_html=True)
