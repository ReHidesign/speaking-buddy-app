import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re

st.set_page_config(page_title="Speaking Buddy v12", page_icon="🇬🇧", layout="wide")

# --- KONFIGURÁCIÓ ---
TOPICS = [
    "🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", 
    "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"
]

LEVELS = {
    "A1 (Beginner)": "Basic sentences.", "A2 (Pre-Int)": "Simple daily English.",
    "B1 (Intermediate)": "B1 Exam level.", "B2 (Upper-Int)": "B2/First Exam level.",
    "C1 (Advanced)": "C1/Advanced Exam level.", "C2 (Proficiency)": "Academic/OKTV level."
}

# --- API ÉS MEMÓRIA ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    # --- SEGÉDFUNKCIÓK ---
    def clean_text_for_audio(text):
        # Narráció (csillagok közötti rész) törlése a hangból
        speech_only = re.sub(r'\*.*?\*', '', text)
        # Írásjelek neveinek kiszűrése (hogy ne mondja ki: question mark)
        speech_only = speech_only.replace("?", ".").replace("!", ".").replace(":", ".").replace("-", " ")
        return speech_only.strip()

    def speak_text(text):
        clean_text = clean_text_for_audio(text)
        if not clean_text: clean_text = "I am listening."
        tts = gTTS(text=clean_text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_instr = (
            f"{system_instruction} Level: {LEVELS.get(st.session_state.user_level)}. "
            "Use *italics for actions*. No emojis. If user says 'HELP', provide corrections."
        )
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🇬🇧 Speaking Buddy")
        st.info("Created by: **ReHi**")
        st.markdown("---")
        st.warning("💡 **Tip:** Write '**HELP**' in the chat if you need grammar advice or translations!")
        if st.session_state.user_level:
            st.success(f"Mode: {st.session_state.current_mode}\nLevel: {st.session_state.user_level}")
        if st.button("🗑️ Reset Everything"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- FLOW ---
    # 1. Szintválasztás
    if not st.session_state.user_level:
        st.subheader("Welcome! Please set your English level:")
        cols = st.columns(3)
        lvls = list(LEVELS.keys())
        for i, l in enumerate(lvls):
            if cols[i%3].button(l, use_container_width=True):
                st.session_state.user_level = l
                st.rerun()
    
    # 2. Módválasztás
    elif not st.session_state.current_mode:
        st.subheader("Choose your practice mode:")
        m_cols = st.columns(4)
        for i, m in enumerate(["📈 Test", "🎮 Game", "🖼️ Picture", "💬 Chat"]):
            if m_cols[i].button(m, use_container_width=True):
                st.session_state.current_mode = re.sub(r'[^\w\s]', '', m).strip()
                st.rerun()

    # 3. Témaválasztás (és képgenerálás)
    elif not st.session_state.chat_topic:
        st.subheader(f"Select a topic for your {st.session_state.current_mode} session:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            clean_t = re.sub(r'[^\w\s]', '', topic).strip()
            if t_cols[idx%3].button(topic, use_container_width=True):
                st.session_state.chat_topic = clean_t
                
                if st.session_state.current_mode == "Picture":
                    # Ingyenes képgenerálás a téma alapján
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/a_realistic_photo_for_english_speaking_exam_about_{clean_t.replace(' ', '_')}?width=800&height=600&nologo=true"
                    ans = call_groq(f"I am the examiner. I show the student a picture about {clean_t}. Ask the student to describe and analyze it.", "Examiner Mode.")
                else:
                    prompts = {
                        "Chat": f"Start a friendly chat about {clean_t}.",
                        "Game": f"Roleplay: {clean_t}. *The Buddy arrives.* Start the dialogue.",
                        "Test": f"Ask 3 exam-style questions about {clean_t}."
                    }
                    ans = call_groq(prompts.get(st.session_state.current_mode), "Language partner.")
                
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # 4. Aktív Chat
    else:
        # Ha képes mód, mutassuk a képet legfelül
        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url, caption=f"Exam Task: {st.session_state.chat_topic}")

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        st.write("---")
        input_col, mic_col = st.columns([0.85, 0.15])
        with mic_col:
            # Dinamikus kulcs a mikrofonhoz a beragadás ellen
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"rec_{len(st.session_state.messages)}")
        with input_col:
            text_input = st.chat_input("Speak or write here...")

        user_msg = text_input if text_input else None
        if audio_input and not text_input:
            # Whisper hívás a Groq-on keresztül
            user_msg = requests.post("https://api.groq.com/openai/v1/audio/transcriptions", 
                                     headers={"Authorization": f"Bearer {api_key}"}, 
                                     files={"file": ("audio.wav", audio_input['bytes'], "audio/wav"), 
                                            "model": (None, "whisper-large-v3"), "language": (None, "en")}).json().get("text", "")

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            system_p = f"You are a partner in {st.session_state.current_mode} mode about {st.session_state.chat_topic}."
            if "HELP" in user_msg.upper(): 
                system_p = "IMPORTANT: Focus on grammar correction first, then respond."
            answer = call_groq(user_msg, system_p)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    # COPYRIGHT
    st.markdown(f"<br><hr><p style='text-align: center; color: grey; font-size: 12px;'>© 2026 Speaking Buddy App by ReHi | All Rights Reserved</p>", unsafe_allow_html=True)
