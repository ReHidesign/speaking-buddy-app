import streamlit as st
import requests
import json

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# Most Groq kulcsot kérünk
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
            "model": "llama-3.3-70b-versatile", # Ez egy bivalyerős modell
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"Hiba: {response.status_code} - {response.text}"

    if cols[1].button("🎮 Game"):
        st.session_state.messages = []
        answer = call_groq("You are a lost tourist in London. Ask me for help in English!")
        st.session_state.messages.append({"role": "assistant", "content": answer})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    if prompt := st.chat_input("Speak..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        with st.chat_message("assistant"):
            answer = call_groq("You are an English teacher. " + prompt)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.info("Please enter your Groq API Key on the left!")
