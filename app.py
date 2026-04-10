import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

st.set_page_config(page_title="Speaking Buddy v13", page_icon="🇬🇧", layout="wide")

# --- CUSTOM CSS A SZÍNEKHEZ ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .stButton>button { border-radius: 20px; border: 2px solid #4CAF50; background-color: white; color: black; }
    .stButton>button:hover { background-color: #4CAF50; color: white; }
    </style>
    """, unsafe_allow_html=True)

TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]

LEVELS = {
    "A1 (Beginner)": "Basic sentences.", "A2 (Pre-Int)": "Simple daily English.",
    "B1 (Intermediate)": "B1 Exam level.", "B2 (Upper-Int)": "B2 Exam level.",
    "C1 (Advanced)": "C1 Exam level.", "C2 (Proficiency)": "OKTV level."
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
        clean_text = re.sub(r'\*.*?\*', '', text).replace("?", ".").replace("!", ".").strip()
        tts = gTTS(text=clean_text if clean_text else "I am listening", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_instr = f"{system_instruction} Level: {LEVELS.get(st.session_state.user_level)}. Use *italics for actions*. NO emojis. If mode is Picture, DO NOT describe the image, wait for the student to do it."
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        return requests.post(url, headers=headers, data=json.dumps(data)).json()['choices'][0]['message']['content']

    # --- ÜDVÖZLÉS ---
    if not st.session_state.intro_done:
        st.image("https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800", width=400)
        st.title("Hello! I'm your Speaking Buddy! 🇬🇧")
        st.subheader("I'm here to help you practice English for exams or just for fun.")
        if st.button("Let's start!"):
            st.session_state.intro_done = True
            st.rerun()

    # --- SZINTFELMÉRŐ / VÁLASZTÓ ---
    elif not st.session_state.user_level:
        st.subheader("How should we start?")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Choose manually:")
            for l in LEVELS.keys():
                if st.button(l, use_container_width=True):
                    st.session_state.user_level = l
                    st.rerun()
        with col2:
            st.write("Not sure?")
            if st.button("🔍 Assess my level (3 questions)", use_container_width=True):
                st.session_state.user_level = "Assessment"
                ans = call_groq("Start a level assessment. Ask a simple question.", "Level Assessor Mode.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- MÓD VÁLASZTÓ ---
    elif not st.session_state.current_mode and st.session_state.user_level != "Assessment":
        st.subheader("What's the plan for today?")
        m_cols = st.columns(4)
        modes = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]
        for i, m in enumerate(modes):
            if m_cols[i].button(m, use_container_width=True):
                st.session_state.current_mode = re.sub(r'[^\w\s]', '', m).strip()
                st.rerun()

    # --- TÉMA VÁLASZTÓ ---
    elif not st.session_state.chat_topic and st.session_state.user_level != "Assessment":
        st.subheader(f"Topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = re.sub(r'[^\w\s]', '', topic).strip()
                if st.session_state.current_mode == "Picture":
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/professional_exam_photo_about_{st.session_state.chat_topic}_no_animals_unless_requested?width=800&height=600&seed={idx}"
                    ans = call_groq("I've generated a picture. Tell the student to describe it. DON'T describe it yourself!", "Examiner Mode.")
                else:
                    prompts = {"Chat": "Start a chat.", "Situation": "Start a roleplay.", "Debate": "Give me a controversial statement to argue about."}
                    ans = call_groq(prompts.get(st.session_state.current_mode), "English Partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- CHAT ---
    else:
        with st.sidebar:
            st.title("Buddy Panel")
            st.write(f"Level: **{st.session_state.user_level}**")
            if st.button("🔄 Change Mode/Topic"):
                st.session_state.current_mode = None
                st.session_state.chat_topic = None
                st.rerun()

        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        audio_input = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key="mic")
        text_input = st.chat_input("Write here...")
        user_msg = text_input if text_input else None # (Whisper hívás ide jönne)

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            # Itt a szintfelmérő logika vagy a sima válasz...
            answer = call_groq(user_msg, "Respond to the student.")
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown("<hr><p style='text-align: center; color: grey;'>© 2026 Speaking Buddy App by ReHi</p>", unsafe_allow_html=True)
