import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
from pydub import AudioSegment

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
    if "whisper_text" not in st.session_state:
        st.session_state.whisper_text = ""

    # --- FUNKCIÓK ---
    
    # Text-to-Speech (Buddy hangja)
    def speak_text(text):
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    # Speech-to-Text (A te hangod -> szöveg)
    def call_whisper(audio_bytes):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Audioformátum konvertálása (szükség esetén pydub-bal)
        # Ez a rész trükkös lehet a böngészők miatt, de kezdjük az alapokkal
        files = {
            "file": ("audio.wav", audio_bytes, "audio/wav"),
            "model": (None, "whisper-large-v3"),
            "language": (None, "en"),
            "response_format": (None, "json")
        }
        
        try:
            response = requests.post(url, headers=headers, files=files)
            if response.status_code == 200:
                return response.json().get("text", "")
            else:
                st.error(f"Whisper Error: {response.status_code}")
                return ""
        except Exception as e:
            st.error(f"Error calling Whisper: {e}")
            return ""

    # Szöveg hívása (Buddy válasza)
    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        history = [{"role": "system", "content": system_instruction}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt:
            history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response.json()['choices'][0]['message']['content']

    # --- OLDALSÁV ÉS ÜZEMMÓDOK ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    st.sidebar.info("💡 **TIP:** Type 'HELP' (any case) in your message or say it for corrections!")
    if st.sidebar.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.session_state.whisper_text = ""
        st.rerun()

    # Módok instrukciói
    modes = {
        "📈 Test": "Assessor mode.",
        "🎮 Game": "You are a lost tourist in London. STAY IN CHARACTER. Start somewhere new (e.g., Hyde Park).",
        "🖼️ Picture": "IMPORTANT: The user will describe an image. Wait for their input and respond to it.",
        "💬 Chat": "Casual conversation friend."
    }

    st.subheader("Choose your practice mode:")
    cols = st.columns(4)
    for i, (label, instr) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = []
            st.session_state.current_mode = label
            st.session_state.whisper_text = ""
            
            # Képes feladatnál nem generálunk kezdő szöveget
            if label != "🖼️ Picture":
                ans = call_groq("Start!", instr)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            else:
                st.session_state.messages.append({"role": "assistant", "content": "Welcome to Picture Mode! I'm showing you an image. Please describe what you see or how it makes you feel."})
                # Itt majd meg kell jelenítenünk a képet
                st.info("Imagine a beautiful picture of the Swiss Alps here.")
            st.rerun()

    # --- CHAT ÉS HANG ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                st.audio(speak_text(msg["content"]), format='audio/mp3')

    # --- BEVITEL (MIKROFON ÉS SZÖVEG) ---
    st.write("---")
    
    # Mikrofon rögzítő
    audio = mic_recorder(start_prompt="🎤 Record", stop_prompt="🛑 Stop", key='recorder')
    
    # Ha van felvétel, elküldjük a Whisper-nek
    if audio and st.session_state.whisper_text == "":
        with st.spinner("Transcribing your voice..."):
            text_from_voice = call_whisper(audio['bytes'])
            if text_from_voice:
                st.session_state.whisper_text = text_from_voice
                st.rerun() # Frissítünk, hogy a szöveg megjelenjen a dobozban

    # Szöveges beviteli mező (amibe a Whisper is beírja a szöveget)
    prompt = st.chat_input("Type here...", key="chat_input")
    
    # Ha a Whisper-ből jött szöveg, azt használjuk
    final_prompt = prompt if prompt else st.session_state.whisper_text

    if final_prompt:
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        st.session_state.whisper_text = "" # Töröljük a Whisper szöveget a következő körre
        
        current_instr = modes.get(st.session_state.current_mode, "Friendly assistant.")
        if "HELP" in final_prompt.upper():
            final_instr = f"CRITICAL: User needs help! First, briefly correct their grammar/vocabulary. Then continue as: {current_instr}"
        else:
            final_instr = current_instr

        with st.chat_message("assistant"):
            answer = call_groq(final_prompt, final_instr)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    # --- COPYRIGHT ---
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: grey;'>© 2024 Speaking Buddy App - All Rights Reserved</p>", unsafe_allow_html=True)

else:
    st.warning("API Key needed!")
