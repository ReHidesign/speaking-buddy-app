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
    .status-box { background-color: #e8f4f8; padding: 10px; border-radius: 10px; border-left: 5px solid #2980b9; margin-bottom: 10px; }
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
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    def speak_text(text):
        # MINDENT kitörlünk, ami zárójelben van (a narrációt)
        speech_only = re.sub(r'\(.*?\)', '', text)
        speech_only = speech_only.replace("*", "").replace("?", ".").replace("!", ".").strip()
        tts = gTTS(text=speech_only if speech_only else "I am listening", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_instr = (
            f"{system_instruction} Student level: {st.session_state.user_level}. "
            "STRICT RULE: Put ALL non-spoken actions or narrative descriptions in brackets and italics like: *(Buddy smiles)*. "
            "Never use italics outside of brackets. "
            "In DEBATE mode: Always take the OPPOSITE side of the student to challenge them."
        )
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-8:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        return requests.post(url, headers=headers, data=json.dumps(data)).json()['choices'][0]['message']['content']

    # --- SIDEBAR (Folyamatosan látható) ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        
        # Státusz kijelzés
        if st.session_state.user_level or st.session_state.current_mode:
            st.markdown("### 📍 You are here:")
            if st.session_state.user_level: st.markdown(f"<div class='status-box'><b>Level:</b> {st.session_state.user_level}</div>", unsafe_allow_html=True)
            if st.session_state.current_mode: st.markdown(f"<div class='status-box'><b>Mode:</b> {st.session_state.current_mode}</div>", unsafe_allow_html=True)
            if st.session_state.chat_topic: st.markdown(f"<div class='status-box'><b>Topic:</b> {st.session_state.chat_topic}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("💡 **Tip:** Write '**HELP**' in the chat for corrections!")
        
        if st.session_state.chat_topic:
            if st.button("🏠 Back to Mode Selection"):
                st.session_state.current_mode = None
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()

        if st.button("🗑️ Full Reset"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- FLOW ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-container'><div class='buddy-avatar'>🤖</div><h1 class='main-title'>Speaking Buddy</h1><p>Your interactive language speaking partner</p></div>", unsafe_allow_html=True)
        st.write("I'm here to help you master **English speaking** for **real-life communication** (and exams).")
        if st.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    elif not st.session_state.user_level:
        st.subheader("Set your English level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l, use_container_width=True):
                st.session_state.user_level = l
                st.rerun()
        if st.button("🔍 Assess my level", use_container_width=True):
            st.session_state.user_level = "Assessment"
            ans = call_groq("Start a level check. Question 1: What would be your dream job?", "Level Assessor.")
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    elif not st.session_state.current_mode and st.session_state.user_level != "Assessment":
        st.subheader("Choose your practice mode:")
        m_list = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat", "🗣️ Slang & Idioms"]
        cols = st.columns(2)
        for i, m in enumerate(m_list):
            if cols[i%2].button(m, use_container_width=True):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()

    elif not st.session_state.chat_topic and st.session_state.user_level != "Assessment":
        st.subheader(f"Select a topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            clean_t = topic.split()[-1]
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = clean_t
                if st.session_state.current_mode == "Picture":
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_exam_photo_{clean_t}?width=800&height=600&seed={random.randint(1,99)}"
                    ans = call_groq("Ask the student to describe the picture. *(Buddy points to the screen)*", "Examiner.")
                elif st.session_state.current_mode == "Debate":
                    ans = call_groq(f"Give a controversial statement about {clean_t} and ask if I agree.", "Debater.")
                elif st.session_state.current_mode == "Situation":
                    ans = call_groq(f"Set up a specific real-life scene about {clean_t}. Start the roleplay.", "Roleplay Partner.")
                else:
                    ans = call_groq(f"Start a session about {clean_t}.", "English Partner.")
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

        input_col, mic_col = st.columns([0.8, 0.2])
        with mic_col: audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic")
        with input_col: text_input = st.chat_input("Message Buddy...")

        user_msg = text_input if text_input else None
        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            sys_m = f"Respond in {st.session_state.current_mode} mode."
            if "HELP" in user_msg.upper(): sys_m = "Correct grammar/style, then continue."
            answer = call_groq(user_msg, sys_m)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy by ReHi</p>", unsafe_allow_html=True)
