import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# --- KONFIGURÁCIÓ ---
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
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    def speak_text(text):
        clean_text = re.sub(r'\*.*?\*', '', text).replace("?", ".").replace("!", ".").replace(":", ".").strip()
        tts = gTTS(text=clean_text if clean_text else "I am listening", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_instr = f"{system_instruction} Level: {LEVELS.get(st.session_state.user_level, 'B2')}. Use *italics for actions*. If the mode is Picture, DO NOT describe it, ask the student to do it."
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        return requests.post(url, headers=headers, data=json.dumps(data)).json()['choices'][0]['message']['content']

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🇬🇧 Speaking Buddy")
        st.write("Created by: **ReHi**")
        if st.button("🗑️ Reset Everything"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- FLOW ---
    if not st.session_state.user_level:
        st.subheader("Welcome! Please set your English level:")
        cols = st.columns(3)
        lvls = list(LEVELS.keys())
        for i, l in enumerate(lvls):
            if cols[i%3].button(l, use_container_width=True):
                st.session_state.user_level = l
                st.rerun()
        if st.button("🔍 Not sure? Assess my level"):
            st.session_state.user_level = "B2 (Upper-Int)" # Ideiglenes, amíg a felmérő login nem fut le
            st.rerun()

    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_cols = st.columns(4)
        modes = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]
        for i, m in enumerate(modes):
            if m_cols[i].button(m, use_container_width=True):
                st.session_state.current_mode = re.sub(r'[^\w\s]', '', m).strip()
                st.rerun()

    elif not st.session_state.chat_topic:
        st.subheader(f"Select a topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            clean_t = re.sub(r'[^\w\s]', '', topic).strip()
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = clean_t
                if st.session_state.current_mode == "Picture":
                    # KÉP LINKJEK HELYE (Ide írhatod majd a GitHub linkeket témák szerint)
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/professional_exam_photo_about_{clean_t}?width=800&height=600&seed={random.randint(1,1000)}"
                    ans = call_groq("I have a picture for you. Please describe what you see!", "Examiner mode.")
                else:
                    prompts = {"Chat": f"Start a chat about {clean_t}.", "Situation": f"Roleplay: {clean_t}.", "Debate": f"Let's debate: {clean_t}. Start with a statement."}
                    ans = call_groq(prompts.get(st.session_state.current_mode), "Language Partner.")
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
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic")
        with input_col:
            text_input = st.chat_input("Your turn...")

        user_msg = text_input if text_input else None
        if audio_input and not text_input:
            user_msg = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", 
                                     headers={"Authorization": f"Bearer {api_key}"}, 
                                     files={"file": ("audio.wav", audio_input['bytes'], "audio/wav"), 
                                            "model": (None, "whisper-large-v3"), "language": (None, "en")}).json().get("text", "")

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            system_p = f"You are a partner in {st.session_state.current_mode} mode."
            if "HELP" in user_msg.upper(): system_p = "Provide grammar feedback."
            answer = call_groq(user_msg, system_p)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown(f"<br><hr><p style='text-align: center; color: grey; font-size: 12px;'>© 2026 Speaking Buddy App by ReHi | All Rights Reserved</p>", unsafe_allow_html=True)
