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
    def speak_text(text):
        tts = gTTS(text=text, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

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

    # --- OLDALSÁV (TIP ÉS INFÓ) ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    if st.session_state.current_mode:
        st.sidebar.success(f"Mode: {st.session_state.current_mode}")
    
    # Itt a fix Tipp mező
    st.sidebar.info("💡 **TIP:** If you are stuck or made a mistake, type **'HELP'** in your message to get a correction!")

    if st.sidebar.button("🗑️ Reset Conversation"):
        st.session_state.messages = []
        st.rerun()

    # --- ÜZEMMÓDOK ---
    modes = {
        "📈 Test": "Professional English teacher. Assess the user's level.",
        "🎮 Game": "You are a lost tourist in London. Stay in character! No teaching unless 'HELP' is asked.",
        "🖼️ Picture": "Describe a scene and ask for the user's thoughts.",
        "💬 Chat": "A friendly companion for casual talk."
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

    # --- CHAT ÉS HANG ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                st.audio(speak_text(msg["content"]), format='audio/mp3')

    # --- BEVITEL (SZÖVEG ÉS MIKROFON) ---
    st.write("---")
    c1, c2 = st.columns([0.8, 0.2])
    
    with c2:
        # Mikrofon gomb
        audio = mic_recorder(start_prompt="🎤 Speak", stop_prompt="🛑 Stop", key='recorder')

    with c1:
        prompt = st.chat_input("Type here or use the mic...")

    # Ha van hangfelvétel (Ezt majd a Whisper-rel kell összekötni, de most maradjunk a szövegnél)
    if audio:
        st.warning("Voice recognition is the next step! For now, please use the text box.")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # HELP logika kényszerítése
        current_instr = modes.get(st.session_state.current_mode, "Friendly assistant.")
        if "HELP" in prompt.upper():
            final_instr = f"CRITICAL: The user needs help! First, correct their grammar mistakes shortly. Then continue as: {current_instr}"
        else:
            final_instr = current_instr

        with st.chat_message("assistant"):
            answer = call_groq(prompt, final_instr)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

    # --- COPYRIGHT ---
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: grey;'>© 2024 Speaking Buddy App - All Rights Reserved</p>", unsafe_allow_html=True)

else:
    st.warning("Please enter your API Key!")
