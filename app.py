import streamlit as st
import requests
import json

# Oldal konfigurációja
st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- API KULCS KEZELÉSE ---
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Groq API Key (gsk_...):", type="password")

if api_key:
    # --- MEMÓRIA INICIALIZÁLÁSA ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_mode" not in st.session_state:
        st.session_state.current_mode = None

    # --- OLDALSÁV ---
    st.sidebar.title("🇬🇧 Speaking Buddy")
    if st.session_state.current_mode:
        st.sidebar.markdown(f"Active Mode: **{st.session_state.current_mode}**")
    
    st.sidebar.info("💡 **Tip:** Write 'HELP' in the chat if you need grammar advice or translations!")
    
    if st.sidebar.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.current_mode = None
        st.rerun()

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    # --- MODULÁRIS GROQ HÍVÁS ---
    def call_groq(prompt, system_instruction, include_history=True):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Üzenetek összeállítása
        history = [{"role": "system", "content": system_instruction}]
        
        if include_history:
            for m in st.session_state.messages[-10:]:
                history.append({"role": m["role"], "content": m["content"]})
        
        if prompt:
            history.append({"role": "user", "content": prompt})

        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": history,
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                return "Buddy is thinking too hard. Try again in a second!"
        except:
            return "Connection error. Please check your internet!"

    # --- ÜZEMMÓDOK DEFINIÁLÁSA ---
    modes = {
        "📈 Test": "You are a professional English assessor. Ask 3 quick questions to test the user's level.",
        "🎮 Game": "You are a lost tourist in London. STAY IN CHARACTER 100%. Ask for directions. No teaching!",
        "🖼️ Picture": "Describe a mysterious or beautiful scene vividly and ask the user what they see or feel.",
        "💬 Chat": "You are a friendly, casual English-speaking companion. Ask how the user is doing."
    }

    # Gombok kezelése
    for i, (label, instr) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = [] # Törlés új mód indításakor
            st.session_state.current_mode = label
            # Kezdő üzenet generálása (történet nélkül, csak az instrukció alapján)
            ans = call_groq("Start the conversation!", instr, include_history=False)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- CHAT MEGJELENÍTÉSE ---
    # Ez a rész mindig lefut, így frissítéskor is megmaradnak az üzenetek!
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- FELHASZNÁLÓI BEVITEL ---
    if prompt := st.chat_input("Write something in English..."):
        # Felhasználó üzenetének mentése
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            # Aktuális mód instrukciójának lekérése
            base_instr = modes.get(st.session_state.current_mode, "You are a helpful English teacher.")
            
            # HELP logika
            if "HELP" in prompt.upper():
                final_instr = f"{base_instr} IMPORTANT: The user asked for help. Briefly explain their grammar mistakes or translate difficult words, then continue the conversation."
            else:
                final_instr = f"{base_instr} Continue the conversation naturally. Stay in character if applicable."
            
            # Válasz lekérése a memóriával együtt
            answer = call_groq(prompt, final_instr)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

else:
    st.warning("⚠️ Please provide an API Key in the sidebar or Secrets to start!")
