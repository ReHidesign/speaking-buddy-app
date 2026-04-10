import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# --- API KULCS ÉS MEMÓRIA ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    # Kezdeti állapotok beállítása
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = None
    if "chat_topic" not in st.session_state:
        st.session_state.chat_topic = None

    # --- FUNKCIÓK ---
    def speak_text(text):
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_whisper(audio_bytes):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav"),
            "model": (None, "whisper-large-v3"),
            "language": (None, "en")
        }
        try:
            response = requests.post(url, headers=headers, files=files)
            return response.json().get("text", "")
        except:
            return None

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        history = [{"role": "system", "content": system_instruction}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt:
            history.append({"role": "user", "content": prompt})
        
        # Temperature 0.4: kiegyensúlyozott, okos válaszok
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.4}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- UI ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    st.sidebar.info("💡 **TIP:** Type or say **'HELP'** to get corrections!")
    
    if st.sidebar.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.session_state.chat_topic = None
        st.session_state.current_mode = None
        st.rerun()

    # Üzemmód választó
    st.subheader("Choose your practice mode:")
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    
    mode_selected = None
    if m_col1.button("📈 Test"): mode_selected = "Test"
    if m_col2.button("🎮 Game"): mode_selected = "Game"
    if m_col3.button("🖼️ Picture"): mode_selected = "Picture"
    if m_col4.button("💬 Chat"): mode_selected = "Chat"

    if mode_selected:
        st.session_state.messages = []
        st.session_state.current_mode = mode_selected
        st.session_state.chat_topic = None
        
        if mode_selected != "Chat":
            instr = {
                "Test": "Helpful English teacher assessing the user's level.",
                "Game": "A lost tourist in London. Start at Hyde Park.",
                "Picture": "Describe a vivid scene and ask the user to explain it."
            }[mode_selected]
            ans = call_groq("Hello!", instr)
            st.session_state.messages.append({"role": "assistant", "content": ans})
        st.rerun()

    # --- SPECIFIKUS CHAT TÉMÁK ---
    if st.session_state.current_mode == "Chat" and not st.session_state.chat_topic:
        st.write("### What would you like to talk about?")
        t_cols = st.columns(3)
        topics = ["✈️ Travel", "🍔 Food & Cooking", "🎬 Movies & Series", "🎸 Music", "⚽ Sports", "💻 Technology"]
        
        for idx, topic in enumerate(topics):
            if t_cols[idx % 3].button(topic):
                st.session_state.chat_topic = topic
                prompt = f"I chose the topic: {topic}. Say hi and ask a thought-provoking question about this."
                ans = call_groq(prompt, "You are a friendly conversation partner. Focus on the chosen topic.")
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    # --- CHAT MEGJELENÍTÉSE ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                st.audio(speak_text(msg["content"]), format='audio/mp3')

    # --- BEVITEL ---
    if st.session_state.current_mode and (st.session_state.current_mode != "Chat" or st.session_state.chat_topic):
        st.write("---")
        input_col, mic_col = st.columns([0.85, 0.15])
        
        with mic_col:
            # Beragadás fix: a key-t dinamikussá tesszük, hogy minden felvétel után "reseteljen"
            audio_key = f"rec_{len(st.session_state.messages)}"
            audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key=audio_key)

        with input_col:
            text_input = st.chat_input("Write or speak to Buddy...")

        user_msg = None
        if text_input:
            user_msg = text_input
        elif audio_input:
            with st.spinner("Buddy is listening..."):
                user_msg = call_whisper(audio_input['bytes'])

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            
            # HELP logika és Instr. összeállítása
            instr_base = "Friendly partner."
            if st.session_state.current_mode == "Game": instr_base = "A lost tourist in London."
            if st.session_state.current_mode == "Chat": instr_base = f"Chatting about {st.session_state.chat_topic}."
            
            final_instr = instr_base
            if "HELP" in user_msg.upper():
                final_instr = f"FIRST: Correct mistakes briefly. THEN: {instr_base}"

            answer = call_groq(user_msg, final_instr)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    # --- COPYRIGHT ---
    st.markdown("<br><br><p style='text-align: center; color: grey; font-size: 10px;'>© 2024 Speaking Buddy App - All Rights Reserved</p>", unsafe_allow_html=True)
