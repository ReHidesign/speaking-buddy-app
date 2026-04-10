import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- ESZTÉTIKAI FINOMÍTÁS ---
st.markdown("""
    <style>
    .main { background-color: #fafafa; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .buddy-header { text-align: center; padding: 20px; color: #2e4053; border-bottom: 2px solid #eee; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]

LEVELS = {
    "A1 (Beginner)": "A1 level, very simple sentences.", "A2 (Pre-Int)": "A2 level, simple daily topics.",
    "B1 (Intermediate)": "B1 level, standard exam vocabulary.", "B2 (Upper-Int)": "B2 level, complex arguments.",
    "C1 (Advanced)": "C1 level, professional and abstract language."
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
        # Csak a dőlt betűs részeket szűrjük ki, a többit hagyjuk meg tisztán
        speech_only = re.sub(r'\*.*?\*', '', text)
        speech_only = speech_only.replace("?", ".").replace("!", ".").replace(":", ".").strip()
        tts = gTTS(text=speech_only if speech_only else "Ready", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # SZIGORÚ UKÁSZ: Nincs dőlt betű a kérdésekben!
        full_instr = (
            f"{system_instruction} Current student level: {st.session_state.user_level}. "
            "STRICT RULE: Use *italics* ONLY for physical actions (narrative). "
            "NEVER use italics for normal words, questions, or choices like 'agree' or 'disagree'. "
            "If in Picture mode: DO NOT describe the scene, ask the student to do it first."
        )
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.6}
        return requests.post(url, headers=headers, data=json.dumps(data)).json()['choices'][0]['message']['content']

    # --- 1. NYITÓ KÉPERNYŐ ---
    if not st.session_state.intro_done:
        st.markdown("<div class='buddy-header'><h1>🇬🇧 Speaking Buddy</h1><p>Your interactive language examiner</p></div>", unsafe_allow_html=True)
        st.write("### Welcome!")
        st.write("I am your AI partner designed to help you prepare for English speaking exams through real-time conversation.")
        if st.button("Start My Session"):
            st.session_state.intro_done = True
            st.rerun()

    # --- 2. SZINT VÁLASZTÓ ---
    elif not st.session_state.user_level:
        st.subheader("First, let's set your English level:")
        col1, col2 = st.columns([1, 1])
        with col1:
            for l in LEVELS.keys():
                if st.button(l):
                    st.session_state.user_level = l
                    st.rerun()
        with col2:
            if st.button("🔍 Assess my level (Chat)"):
                st.session_state.user_level = "Assessment in progress"
                ans = call_groq("Hello! I'm Buddy. I will ask you 3 questions to find your level. Question 1: What do you like to do in your free time?", "Level Assessor Mode.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- 3. MÓD VÁLASZTÓ ---
    elif not st.session_state.current_mode and st.session_state.user_level != "Assessment in progress":
        st.subheader("Choose your practice mode:")
        m_cols = st.columns(4)
        modes = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]
        for i, m in enumerate(modes):
            if m_cols[i].button(m):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()

    # --- 4. TÉMA ÉS FELADAT INDÍTÁSA ---
    elif not st.session_state.chat_topic and st.session_state.user_level != "Assessment in progress":
        st.subheader(f"Select a topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            clean_t = topic.split()[-1]
            if t_cols[idx%3].button(topic):
                st.session_state.chat_topic = clean_t
                if st.session_state.current_mode == "Picture":
                    # Itt majd a GitHub linkek jönnek, addig a stabilabb generátor
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/a_clear_realistic_photo_about_{clean_t}_for_exam_description?width=800&height=600&seed={random.randint(1,99)}"
                    ans = call_groq("I have a picture for you. *Buddy shows you a picture.* Please describe it in detail.", "Examiner Mode.")
                else:
                    prompts = {
                        "Chat": f"Start a friendly talk about {clean_t}.",
                        "Situation": f"We are in a situation related to {clean_t}. *Buddy starts the conversation.*",
                        "Debate": f"Let's debate {clean_t}. Give me a strong statement to start."
                    }
                    ans = call_groq(prompts.get(st.session_state.current_mode), "Language Partner.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- 5. AKTÍV CHAT ---
    else:
        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url, use_column_width=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        st.write("---")
        input_col, mic_col = st.columns([0.8, 0.2])
        with mic_col:
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic_btn")
        with input_col:
            text_input = st.chat_input("Speak or type here...")

        user_msg = text_input if text_input else None
        # (Ide jön a Whisper API hívás, ha audio_input van - a korábbi kód alapján)

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            # Speciális segítség kérés
            sys_msg = f"Partner in {st.session_state.current_mode} mode."
            if "HELP" in user_msg.upper(): sys_msg = "Correct the user's grammar and explain why, then continue."
            
            answer = call_groq(user_msg, sys_msg)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    # FOOTER
    st.markdown(f"<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy by ReHi | Exam Prep Edition</p>", unsafe_allow_html=True)
