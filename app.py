import streamlit as st
import requests
import json

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# Bal oldali sáv a kulcsnak
api_key = st.sidebar.text_input("Enter Groq API Key (gsk_...):", type="password")

if api_key:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    def call_groq(prompt):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a friendly English mentor. Keep answers short and encouraging."},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            return response.json()['choices'][0]['message']['content']
        except:
            return "Oops, something went wrong. Try again!"

    # Gombok és a hozzájuk tartozó parancsok
    if cols[0].button("📈 Test"):
        st.session_state.messages = []
        ans = call_groq("Start a short English level test with 3 easy questions!")
        st.session_state.messages.append({"role": "assistant", "content": ans})

    if cols[1].button("🎮 Game"):
        st.session_state.messages = []
        ans = call_groq("You are a lost tourist in London. Start a conversation by asking me for help!")
        st.session_state.messages.append({"role": "assistant", "content": ans})

    if cols[2].button("🖼️ Picture"):
        st.session_state.messages = []
        ans = call_groq("Describe a famous painting in English and ask me what I think about it!")
        st.session_state.messages.append({"role": "assistant", "content": ans})

    if cols[3].button("💬 Chat"):
        st.session_state.messages = []
        ans = call_groq("Hello! Introduce yourself as my Speaking Buddy and ask me how my day was.")
        st.session_state.messages.append({"role": "assistant", "content": ans})

    # Chat megjelenítése
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Folyamatos beszélgetés
    if prompt := st.chat_input("Write back to Buddy..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            # Itt elküldjük az utolsó üzenetet a Buddynak
            answer = call_groq(prompt)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.info("Kérlek, add meg a Groq API kulcsodat (gsk_...) a bal oldalon!")
