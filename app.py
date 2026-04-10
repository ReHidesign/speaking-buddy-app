import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# API Kulcs kezelése
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Ez a legáltalánosabb hivatkozás
        model = genai.GenerativeModel('gemini-1.5-flash')

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Gombok
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        if cols[0].button("📈 Test"): st.session_state.messages.append({"role": "user", "content": "Start Level Test"})
        if cols[1].button("🎮 Game"): st.session_state.messages.append({"role": "user", "content": "Challenge Mode"})
        if cols[2].button("🖼️ Picture"): st.session_state.messages.append({"role": "user", "content": "Picture Lab"})
        if cols[3].button("💬 Chat"): st.session_state.messages.append({"role": "user", "content": "Casual Chat"})

        # Chat megjelenítés
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Üzenetküldés - Frissített logika
        if prompt := st.chat_input("Write here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Nagyon egyszerű hívás a teszteléshez
                response = model.generate_content(f"System: You are an English teacher. Answer the user briefly. User: {prompt}")
                if response:
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                else:
                    st.error("Üres válasz érkezett az AI-tól.")
                
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Please enter your API Key in the sidebar!")
