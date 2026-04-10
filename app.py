import streamlit as st
import requests
import json
from gtts import gTTS
import io

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# API Kulcs ellenőrzése
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = None

    # --- HANG GENERÁLÁSA FUNKCIÓ ---
    def speak_text(text):
        tts = gTTS(text=text, lang='en', tld='co.uk') # Brit kiejtés (tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction, include_history=True):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        history = [{"role": "system", "content": system_instruction}]
        if include_history:
            for m in st.session_state.messages[-10:]:
                history.append({"role": m["role"], "content": m["content"]})
        if prompt:
            history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            return response.json()['choices'][0]['message']['content']
        except:
            return "Sorry, I lost my voice for a second!"

    # Módok választása
    modes = {
        "📈 Test": "Level assessor mode.",
        "🎮 Game": "You are a lost tourist in London. STAY IN CHARACTER.",
        "🖼️ Picture": "Describe a scene for the user.",
        "💬 Chat": "Casual conversation friend."
    }

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    for i, (label, instr) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = []
            st.session_state.current_mode = label
            ans = call_groq("Start!", instr, include_history=False)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # Oldalsáv infók
    st.sidebar.title("🇬🇧 Speaking Buddy")
    if st.session_state.current_mode:
        st.sidebar.write(f"Mode: {st.session_state.current_mode}")

    # Chat megjelenítése és hang lejátszása
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            # Csak az utolsó Buddy üzenethez teszünk lejátszót, hogy ne legyen zajos
            if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                audio_data = speak_text(msg["content"])
                st.audio(audio_data, format='audio/mp3')

    # Felhasználói bemenet
    if prompt := st.chat_input("Talk to me..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun() # Frissítünk, hogy a hívás elinduljon
