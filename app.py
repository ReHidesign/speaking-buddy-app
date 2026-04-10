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
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = None

    # --- FUNKCIÓK ---
    
    # Buddy hangja (Text-to-Speech)
    def speak_text(text):
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    # A Te hangod feldolgozása (Speech-to-Text / Whisper)
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

    # Buddy válasza (LLM)
    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        history = [{"role": "system", "content": system_instruction}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt:
            history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.8}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- UI ÉS OLDALSÁV ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    st.sidebar.info("💡 **TIP:** Type or say **'HELP'** if you want me to check your English!")
    
    if st.sidebar.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

    # Módok
    modes = {
        "📈 Test": "Friendly English teacher. Check the user's level with 2-3 questions.",
        "🎮 Game": "You are a lost, slightly tired tourist in London. Be natural, not like a bot. Start at a random location like Hyde Park.",
        "🖼️ Picture": "Ask the user to describe a scene from their imagination or a famous place. You provide feedback.",
        "💬 Chat": "A cool, friendly Londoner. Talk about movies, food, or hobbies."
    }

    st.subheader("Choose your practice mode:")
    cols = st.columns(4)
    for i, (label, instr) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = []
            st.session_state.current_mode = label
            ans = call_groq("Hello!", instr)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- CHAT MEGJELENÍTÉSE ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                st.audio(speak_text(msg["content"]), format='audio/mp3')

    # --- BEVITEL (SZÖVEG + MIKROFON) ---
    st.write("---")
    input_col, mic_col = st.columns([0.85, 0.15])
    
    with mic_col:
        audio_input = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key='recorder')

    with input_col:
        text_input = st.chat_input("Write or speak to Buddy...")

    # Bemenet feldolgozása (vagy szöveg, vagy hang)
    user_msg = None
    if text_input:
        user_msg = text_input
    elif audio_input:
        with st.spinner("Buddy is listening..."):
            user_msg = call_whisper(audio_input['bytes'])

    if user_msg:
        st.session_state.messages.append({"role": "user", "content": user_msg})
        
        # HELP logika
        current_instr = modes.get(st.session_state.current_mode, "Friendly assistant.")
        if "HELP" in user_msg.upper():
            final_instr = f"First, friendly correct any English mistakes in the user's message. Then: {current_instr}"
        else:
            final_instr = current_instr

        answer = call_groq(user_msg, final_instr)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # --- COPYRIGHT ---
    st.markdown("<br><br><p style='text-align: center; color: grey; font-size: 12px;'>© 2024 Speaking Buddy App - All Rights Reserved</p>", unsafe_allow_html=True)

else:
    st.warning("Please enter your Groq API Key in the sidebar!")
