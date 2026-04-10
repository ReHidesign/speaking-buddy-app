import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Ez a név a leguniverzálisabb:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.subheader("Choose a mode:")
        cols = st.columns(4)
        
        # JAVÍTOTT GOMB: Az AI rögtön karakterbe kerül
        if cols[1].button("🎮 Game"):
            st.session_state.messages = [] # Tiszta lap
            initial_prompt = "You are a lost tourist in London. Start the conversation by asking me for help in English!"
            response = model.generate_content(initial_prompt)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        # Chat megjelenítése
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Válaszadás
        if prompt := st.chat_input("Help the tourist..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Összefűzzük az előzményeket, hogy tudja, ki ő
                full_context = "You are a lost tourist. Stay in character! " + prompt
                time.sleep(1) # Biztonsági szünet
                response = model.generate_content(full_context)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Hiba: {e}")
else:
    st.info("Please enter your API key!")
