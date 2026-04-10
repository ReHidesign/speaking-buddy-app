import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- CUSTOM CSS A DESIGNHOZ ---
st.markdown("""
    <style>
    .stApp { background-color: #fafafa; }
    .buddy-container { text-align: center; padding: 10px; }
    .buddy-avatar { font-size: 70px; margin-bottom: 0px; }
    .main-title { color: #2e4053; margin-top: -10px; }
    .stButton>button { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURÁCIÓ ---
TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]

LEVELS = {
    "A1 (Beginner)": "A1 level, very simple sentences.", "A2 (Pre-Int)": "A2 level, simple daily topics.",
    "B1 (Intermediate)": "B1 level, standard vocabulary.", "B2 (Upper-Int)": "B2 level, complex arguments.",
    "C1 (Advanced)": "C1 level, professional language."
}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    # Memória inicializálása
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []

    def speak_text(text):
        # Szigorú szűrés a dőlt betűkre
        speech_only = re.sub(r'\*.*?\*', '', text)
        speech_only = speech_only.replace("?", ".").replace("!", ".").replace(":", ".").strip()
        tts = gTTS(text=speech_only if speech_only else "Ready", lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        full_instr = (
            f"{system_instruction} Student level: {st.session_state.user_level}. "
            "STRICT: Use *italics* ONLY for physical actions. NO italics for normal speech, questions or keywords."
        )
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.6}
        return requests.post(url, headers=headers, data=json.dumps(data)).json()['choices'][0]['message']['content']

    # --- SIDEBAR (Bal oldali menü) ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.info("Created by: **ReHi**")
        st.markdown("---")
        st.warning("💡 **Tip:** Write '**HELP**' in the chat for corrections!")
        
        if st.session_state.user_level:
            st.success(f"Level: {st.session_state.user_level}")
        
        if st.session_state.chat_topic:
            if st.button("🏠 Back to Menu"):
                st.session_state.current_mode = None
                st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
                
        if st.button("🗑️ Full Reset"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

    # --- 1. ÜDVÖZLÉS (Sematikus Buddyval) ---
    if not st.session_state.intro_done:
        st.markdown("""
            <div class='buddy-container'>
                <div class='buddy-avatar'>🤖</div>
                <h1 class='main-title'>Speaking Buddy</h1>
                <p style='font-size: 1.2em; color: #555;'>Your interactive language speaking partner</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("### Welcome!")
        st.write("I am here to help you practice **English speaking** (and prepare for exams).")
        
        if st.button("Let's start! 🚀"):
            st.session_state.intro_done = True
            st.rerun()

    # --- 2. SZINTFELMÉRŐ ---
    elif not st.session_state.user_level:
        st.subheader("Set your level:")
        cols = st.columns(3)
        lvls = list(LEVELS.keys())
        for i, l in enumerate(lvls):
            if cols[i%3].button(l):
                st.session_state.user_level = l
                st.rerun()
        st.write("---")
        if st.button("🔍 Assess my level (Chat with Buddy)"):
            st.session_state.user_level = "Assessment"
            ans = call_groq("Hello! I'm Buddy. I'll ask 3 questions to find your level. Question 1: What is your favorite hobby and why?", "Level Assessor Mode.")
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- 3. MÓD VÁLASZTÓ ---
    elif not st.session_state.current_mode and st.session_state.user_level != "Assessment":
        st.subheader("Choose your path:")
        m_cols = st.columns(4)
        modes = ["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]
        for i, m in enumerate(modes):
            if m_cols[i].button(m):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()

    # --- 4. TÉMA VÁLASZTÓ ---
    elif not st.session_state.chat_topic and st.session_state.user_level != "Assessment":
        st.subheader(f"Topic for {st.session_state.current_mode}:")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            clean_t = topic.split()[-1]
            if t_cols[idx%3].button(topic):
                st.session_state.chat_topic = clean_t
                if st.session_state.current_mode == "Picture":
                    st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_exam_photo_about_{clean_t}?width=800&height=600&seed={random.randint(1,99)}"
                    ans = call_groq("I have a picture for you. *Buddy points to the screen.* Please describe it!", "Examiner Mode.")
                else:
                    prompts = {"Chat": "Start a chat.", "Situation": "Start a roleplay.", "Debate": "Give me a statement to debate."}
                    ans = call_groq(prompts.get(st.session_state.current_mode), "Language Partner.")
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
        with mic_col:
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic")
        with input_col:
            text_input = st.chat_input("Reply to Buddy...")

        user_msg = text_input if text_input else None # (Whisper logic is implicit here)

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            sys_msg = f"Partner in {st.session_state.current_mode} mode."
            if "HELP" in user_msg.upper(): sys_msg = "Correct grammar, then respond."
            answer = call_groq(user_msg, sys_msg)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    st.markdown(f"<br><hr><p style='text-align: center; color: grey; font-size: 11px;'>© 2026 Speaking Buddy by ReHi | All Rights Reserved</p>", unsafe_allow_html=True)
