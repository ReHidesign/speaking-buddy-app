import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Speaking Buddy v3", page_icon="🇬🇧")

# --- KONFIGURÁCIÓ ---
TOPICS = [
    "✈️ Travel & Tourism", "🍔 Food & Cooking", "🎬 Movies & Entertainment", 
    "⚽ Sports & Health", "💻 Technology & AI", "🏠 Home & Family",
    "🎓 Education & Learning", "💼 Work & Career", "🌍 Environment"
]

LEVELS = {
    "A1 (Beginner)": "Use very simple words, short sentences. Focus on basic vocabulary.",
    "A2 (Pre-Intermediate)": "Simple English, but use connected sentences. Clear and slow.",
    "B1 (Intermediate)": "Standard English. Use common idioms and more complex structures.",
    "B2 (Upper-Intermediate)": "Natural, fast English with advanced vocabulary and phrasal verbs.",
    "C1 (Advanced)": "Sophisticated English, academic words, and nuanced expressions."
}

# --- API ÉS MEMÓRIA ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    if "messages" not in st.session_state: st.session_state.messages = []
    if "current_mode" not in st.session_state: st.session_state.current_mode = None
    if "user_level" not in st.session_state: st.session_state.user_level = None
    if "chat_topic" not in st.session_state: st.session_state.chat_topic = None

    # --- FUNKCIÓK ---
    def speak_text(text):
        # Az emojikat kiszedjük a felolvasás előtt
        import re
        clean_text = re.sub(r'[^\x00-\x7F]+', '', text) 
        tts = gTTS(text=clean_text, lang='en', tld='co.uk') # Marad a brit akcentus
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Szigorú utasítás: NE HASZNÁLJ EMOJIKAT!
        full_instr = f"{system_instruction} IMPORTANT: Do not use any emojis or icons in your response. Speak at {st.session_state.user_level} level."
        
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt:
            history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.5}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- SIDEBAR & RESET ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    if st.session_state.user_level:
        st.sidebar.success(f"Current Level: {st.session_state.user_level}")
    
    if st.sidebar.button("🗑️ Reset Everything"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

    # --- 1. LÉPÉS: SZINT MEGHATÁROZÁSA ---
    if not st.session_state.user_level:
        st.subheader("Welcome! First, let's set your English level:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Choose manually:")
            for lvl in LEVELS.keys():
                if st.button(lvl):
                    st.session_state.user_level = lvl
                    st.rerun()
        
        with col2:
            st.write("### Assessment:")
            if st.button("🔍 Assess my level (3 questions)"):
                st.session_state.user_level = "Assessment in progress"
                ans = call_groq("Start the level assessment.", "You are an examiner. Ask the user 3 simple questions one by one to find their level. Start with the first question.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- 2. LÉPÉS: MÓD VÁLASZTÁS ---
    elif st.session_state.user_level and not st.session_state.current_mode:
        st.subheader(f"Level: {st.session_state.user_level}. Choose a mode:")
        m_col = st.columns(4)
        if m_col[0].button("📈 Test"): st.session_state.current_mode = "Test"
        if m_col[1].button("🎮 Game"): st.session_state.current_mode = "Game"
        if m_col[2].button("🖼️ Picture"): st.session_state.current_mode = "Picture"
        if m_col[3].button("💬 Chat"): st.session_state.current_mode = "Chat"
        if any(m_col): st.rerun()

    # --- 3. LÉPÉS: TÉMA VÁLASZTÁS (Ha Chat mód) ---
    elif st.session_state.current_mode == "Chat" and not st.session_state.chat_topic:
        st.subheader("What topic shall we discuss?")
        t_cols = st.columns(3)
        for idx, topic in enumerate(TOPICS):
            if t_cols[idx % 3].button(topic):
                st.session_state.chat_topic = topic
                ans = call_groq(f"I want to talk about {topic}.", f"Conversation partner at {st.session_state.user_level} level.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- CHAT ÉS BEVITEL ---
    if st.session_state.user_level and (st.session_state.current_mode or st.session_state.user_level == "Assessment in progress"):
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        input_col, mic_col = st.columns([0.85, 0.15])
        with mic_col:
            # streamlit-mic-recorder vagy Whisper hívás ide jön (lásd előző kód)
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=f"rec_{len(st.session_state.messages)}")
        
        text_input = st.chat_input("Speak or write...")
        
        # (Whisper hívás és Groq válasz logika ugyanaz, mint az előző verzióban)
