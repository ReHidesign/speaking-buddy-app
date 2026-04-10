import streamlit as st
import requests
import json
from gtts import gTTS
import io
from streamlit_mic_recorder import mic_recorder
import re
import random
import hashlib

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- DESIGN ---
st.markdown("""
    <style>
    .stApp { background-color: #fafafa; }
    .buddy-container { text-align: center; padding: 10px; }
    .buddy-avatar { font-size: 70px; margin-bottom: 0px; }
    .main-title { color: #2e4053; margin-top: -10px; margin-bottom: 0px; }
    .sub-title { font-size: 1.2em; color: #555; margin-bottom: 20px; }
    .status-box { background-color: #e8f4f8; padding: 10px; border-radius: 10px; border-left: 5px solid #2980b9; margin-bottom: 10px; font-size: 14px; }
    .help-card { background-color: #fff4e5; padding: 15px; border-radius: 10px; border: 1px dashed #e67e22; color: #d35400; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIG ---
TOPICS = ["🌍 Environment", "🏙️ Lifestyle", "💼 Career", "🎭 Culture", "🏫 Education", "🛍️ Consumer Society", "✈️ Travel", "⚽ Health", "💻 Technology"]
LEVELS = {"A1 (Beginner)": "A1", "A2 (Pre-Int)": "A2", "B1 (Intermediate)": "B1", "B2 (Upper-Int)": "B2", "C1 (Advanced)": "C1", "C2 (Proficiency)": "C2"}

if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key:", type="password")

if api_key:
    # Session állapota - Hozzáadva: last_audio_id a duplikációk ellen
    for key in ["messages", "current_mode", "user_level", "chat_topic", "last_image_url", "intro_done", "feedback_level", "last_audio_id"]:
        if key not in st.session_state: st.session_state[key] = None
    if st.session_state.messages is None: st.session_state.messages = []
    if st.session_state.feedback_level is None: st.session_state.feedback_level = "Balanced"

    def transcribe_audio(audio_bytes):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": "whisper-large-v3", "language": "en"}
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            res_json = response.json()
            return res_json.get("text", "")
        except: return ""

    def speak_text(text):
        speech_only = re.sub(r'\(.*?\)', '', text)
        speech_only = speech_only.replace("*", "").replace("?", ".").replace("!", ".").strip()
        if not speech_only: speech_only = "I am listening."
        tts = gTTS(text=speech_only, lang='en', tld='co.uk')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp

    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        feedback_instr = {
            "Relaxed": "Only correct mistakes if explicitly asked.",
            "Balanced": "Subtly correct major mistakes in your response.",
            "Teacher Mode": "Correct grammar mistakes clearly before answering."
        }
        full_instr = (
            f"{system_instruction} Student level: {st.session_state.user_level}. "
            f"Feedback style: {feedback_instr[st.session_state.feedback_level]}. "
            "IF the student says 'HELP': Explain the grammar error. "
            "IF the student says 'finished' or 'done': Provide a 'Task Summary'. "
            "IMPORTANT: You HAVE a voice and you produce audio. Never deny this. "
            "STRICT: Put actions in brackets: *(Buddy smiles)*."
        )
        history = [{"role": "system", "content": full_instr}]
        for m in st.session_state.messages[-10:]:
            history.append({"role": m["role"], "content": m["content"]})
        if prompt: history.append({"role": "user", "content": prompt})
        
        data = {"model": "llama-3.3-70b-versatile", "messages": history, "temperature": 0.7}
        try:
            r = requests.post(url, headers=headers, data=json.dumps(data))
            res = r.json()
            if 'choices' in res:
                return res['choices'][0]['message']['content']
            return "*(Buddy looks puzzled)* I had a connection glitch. Can you say that again?"
        except: return "*(Buddy apologizes)* My brain stalled for a second. Let's try again!"

    # --- SIDEBAR ---
    with st.sidebar:
        st.title("⚙️ Control Panel")
        st.session_state.feedback_level = st.select_slider("Feedback Level:", options=["Relaxed", "Balanced", "Teacher Mode"], value=st.session_state.feedback_level)
        st.markdown("---")
        st.markdown("<div class='help-card'><b>🆘 HELP:</b> Say 'HELP' for advice!</div>", unsafe_allow_html=True)
        if st.session_state.user_level:
            st.info(f"Level: {st.session_state.user_level}")
            if st.button("🏠 Back to Menu"):
                st.session_state.current_mode = st.session_state.chat_topic = None
                st.session_state.messages = []
                st.rerun()
        if st.button("🗑️ Full Reset"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN UI ---
    if not st.session_state.intro_done:
        st.title("🤖 Speaking Buddy")
        if st.button("Start 🚀"):
            st.session_state.intro_done = True
            st.rerun()
    elif not st.session_state.user_level:
        st.subheader("Level:")
        cols = st.columns(2)
        for i, l in enumerate(LEVELS.keys()):
            if cols[i%2].button(l):
                st.session_state.user_level = l
                st.rerun()
    elif not st.session_state.current_mode:
        st.subheader("Mode:")
        cols = st.columns(2)
        for i, m in enumerate(["📈 Debate", "🎭 Situation", "🖼️ Picture", "💬 Chat"]):
            if cols[i%2].button(m):
                st.session_state.current_mode = m.split()[-1]
                st.rerun()
    elif not st.session_state.chat_topic:
        st.subheader("Topic:")
        t_cols = st.columns(3)
        for idx, t in enumerate(TOPICS):
            if t_cols[idx%3].button(t):
                with st.spinner('Preparing...'):
                    st.session_state.chat_topic = t.split()[-1]
                    if st.session_state.current_mode == "Picture":
                        st.session_state.last_image_url = f"https://image.pollinations.ai/prompt/realistic_exam_photo_{st.session_state.chat_topic}?width=800&height=600&seed={random.randint(1,99)}"
                    ans = call_groq(f"Start a {st.session_state.current_mode} about {st.session_state.chat_topic}.", "Language Partner.")
                    st.session_state.messages.append({"role": "assistant", "content": ans})
                    st.rerun()
    else:
        # CHAT
        if st.session_state.current_mode == "Picture" and st.session_state.last_image_url:
            st.image(st.session_state.last_image_url)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg == st.session_state.messages[-1] and msg["role"] == "assistant":
                    st.audio(speak_text(msg["content"]), format='audio/mp3')

        # INPUT AREA
        input_col, mic_col = st.columns([0.8, 0.2])
        with mic_col:
            audio_data = mic_recorder(start_prompt="🎤", stop_prompt="🛑", key="mic_recorder")
        with input_col:
            text_input = st.chat_input("Message Buddy...")

        user_msg = None
        
        # --- AUDIO HANDLING WITH DUPLICATION GUARD ---
        if audio_data:
            # Generálunk egy ujjlenyomatot a hangfájlból
            current_audio_id = hashlib.md5(audio_data['bytes']).hexdigest()
            
            # Csak akkor fut le, ha ez egy ÚJ hangfelvétel
            if current_audio_id != st.session_state.last_audio_id:
                st.session_state.last_audio_id = current_audio_id
                with st.spinner('Buddy is listening...'):
                    user_msg = transcribe_audio(audio_data['bytes'])
        
        elif text_input:
            user_msg = text_input

        if user_msg:
            st.session_state.messages.append({"role": "user", "content": user_msg})
            with st.spinner('Buddy is thinking...'):
                answer = call_groq(user_msg, f"Mode: {st.session_state.current_mode}.")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
