import streamlit as st
import requests
import json

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    # Közvetlen API hívás függvény - ez nem tud "elromlani" a verziók miatt
    def call_gemini_direct(prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts":[{"text": prompt}]}]}
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"

    # Gombok beállítása
    modes = {"📈 Test": "Start an English test!", 
             "🎮 Game": "You are a lost tourist. Ask me for help!", 
             "🖼️ Picture": "Describe a picture for me!", 
             "💬 Chat": "Hi!"}

    for i, (label, text) in enumerate(modes.items()):
        if cols[i].button(label):
            st.session_state.messages = []
            answer = call_gemini_direct(text)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    # Chat megjelenítése
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Üzenetküldés
    if prompt := st.chat_input("Speak to Buddy..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            answer = call_gemini_direct("You are an English teacher. " + prompt)
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
else:
    st.info("Kérlek, add meg az API kulcsot!")
