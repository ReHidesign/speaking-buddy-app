import streamlit as st
import requests
import json

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# --- API KULCS KEZELÉSE ---
# Először megnézzük, be van-e állítva a Streamlit Secrets-ben (éles üzem)
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    # Ha nincs, akkor marad a manuális beírás a teszteléshez
    api_key = st.sidebar.text_input("Enter Groq API Key (gsk_...):", type="password")

if api_key:
    # --- MEMÓRIA (SESSION STATE) INICIALIZÁLÁSA ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    st.sidebar.title("Speaking Buddy")
    st.sidebar.info("💡 Write 'HELP' if you need corrections!")
    
    # Törlés gomb, ha új játékot akarnál indítani
    if st.sidebar.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Átadjuk a korábbi üzeneteket is, hogy a Buddy emlékezzen a kontextusra!
        history = [{"role": "system", "content": system_instruction}]
        for m in st.session_state.messages[-6:]: # Az utolsó 6 üzenetet mindig elküldjük
            history.append({"role": m["role"], "content": m["content"]})
        history.append({"role": "user", "content": prompt})

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": history,
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            return response.json()['choices'][0]['message']['content']
        except:
            return "My circuits are a bit tired. Can you repeat that?"

    # Üzemmód gombok - csak akkor adnak üzenetet, ha még üres a chat
    modes = {
        "📈 Test": "You are a level assessor. Start a quick test!",
        "🎮 Game": "You are a lost tourist in London. STAY IN CHARACTER. Start by asking for help!",
        "🖼️ Picture": "Describe a mysterious room and ask me what I see.",
        "💬 Chat": "Hi! You are my casual friend. Ask me about my day."
    }

    for i, (label, instr) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = []
            ans = call_groq("Start!", instr)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- CHAT MEGJELENÍTÉSE ---
    # Ez a rész felel azért, hogy frissítés után is ott legyenek a buborékok
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- BEVITEL ---
    if prompt := st.chat_input("Continue the story..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            if "HELP" in prompt.upper():
                s_instr = "Give a very brief grammar correction, then return to character."
            else:
                s_instr = "Continue the conversation naturally. Stay in character if in a game."
            
            answer = call_groq(prompt, s_instr)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.warning("Please provide an API Key to wake up your Buddy!")
