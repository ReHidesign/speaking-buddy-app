import streamlit as st
import requests
import json

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

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

    st.sidebar.title("Speaking Buddy")
    if st.session_state.current_mode:
        st.sidebar.write(f"Active Mode: **{st.session_state.current_mode}**")
    
    if st.sidebar.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.session_state.current_mode = None
        st.rerun()

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    def call_groq(prompt, system_instruction):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Kontextus építése
        history = [{"role": "system", "content": system_instruction}]
        for m in st.session_state.messages[-10:]: # Több üzenetet küldünk a jobb emlékezetért
            history.append({"role": m["role"], "content": m["content"]})
        
        # Csak akkor adjuk hozzá a promptot, ha nem üres (kezdésnél üres)
        if prompt:
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
            return "My circuits are a bit tired. Try again!"

    # Gombok és instrukciók
    modes = {
        "📈 Test": "You are a professional English assessor. Conduct a short level test.",
        "🎮 Game": "You are a lost tourist in London. STAY IN CHARACTER. No teaching!",
        "🖼️ Picture": "Describe a vivid scene and ask for the user's opinion.",
        "💬 Chat": "You are a friendly companion. Keep the conversation casual."
    }

    # Gombnyomás kezelése
    for i, (label, instr) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = []
            st.session_state.current_mode = label
            ans = call_groq("", instr) # Üres prompttal indítjuk a kezdő szöveget
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.rerun()

    # --- CHAT MEGJELENÍTÉSE ---
    # Ez mindig lefut, így frissítés után is látszanak az üzenetek
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- BEVITEL ---
    if prompt := st.chat_input("Type here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            # Meghatározzuk az alap instrukciót a mód alapján
            base_instr = modes.get(st.session_state.current_mode, "You are a helpful assistant.")
            
            if "HELP" in prompt.upper():
                final_instr = f"{base_instr} The user needs HELP. Give a brief correction, then continue."
            else:
                final_instr = f"{base_instr} Continue the conversation naturally."
            
            answer = call_groq(prompt, final_instr)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.warning("API Key needed!")
