import streamlit as st
import requests
import json

# Oldal beállítása
st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# Bal oldali sáv az API kulcsnak
st.sidebar.title("Settings")
api_key = st.sidebar.text_input("Enter Groq API Key (gsk_...):", type="password")

if api_key:
    # Üzenetek tárolása a munkamenetben
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Emlékeztető a "HELP" funkcióra
    st.sidebar.info("💡 Tip: In 'Game' mode, write 'HELP' if you need corrections or advice!")

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    # Központi függvény a Groq hívásához
    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7 # Egy kis kreativitást adunk neki
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Connection error: {e}"

    # --- ÜZEMMÓDOK ---

    # 1. TEST MÓD
    if cols[0].button("📈 Test"):
        st.session_state.messages = []
        instr = "You are an English level assessor. Ask 3 quick, varied questions to test the user's level. Be professional."
        ans = call_groq("Start the test!", instr)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # 2. GAME MÓD (Itt módosítottuk az utasítást!)
    if cols[1].button("🎮 Game"):
        st.session_state.messages = []
        # Szigorú utasítás: Maradjon szerepben, ne tanítson!
        instr = "You are a lost tourist in London. STAY IN CHARACTER 100%. Do not give feedback, do not correct grammar, and do not act like a teacher. Just talk like a confused person. Only give help if the user explicitly writes 'HELP'."
        ans = call_groq("Excuse me, I'm lost. Start the conversation!", instr)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # 3. PICTURE MÓD
    if cols[2].button("🖼️ Picture"):
        st.session_state.messages = []
        instr = "Describe a famous scene or painting vividly and ask the user to guess what it is or describe their feelings about it."
        ans = call_groq("Start the picture description!", instr)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # 4. CHAT MÓD
    if cols[3].button("💬 Chat"):
        st.session_state.messages = []
        instr = "You are a friendly, casual English-speaking friend. Introduce yourself and ask how the user's day is going."
        ans = call_groq("Hi there!", instr)
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # --- CHAT MEGJELENÍTÉSE ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- FELHASZNÁLÓI BEVITEL ---
    if prompt := st.chat_input("Write back to Buddy..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            # Meghatározzuk az utasítást attól függően, hogy mi történik
            if "HELP" in prompt.upper():
                instr = "The user asked for help. Briefly explain their mistakes and give a better way to say it, then return to your role."
            else:
                instr = "You are in a conversation. If in a game, stay in character. Do not give unsolicited advice. Keep it natural."
            
            answer = call_groq(prompt, instr)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.info("Please enter your Groq API Key in the sidebar to start!")
