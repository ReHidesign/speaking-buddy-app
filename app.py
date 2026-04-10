import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        # Itt kényszerítjük a stabil verziót
        genai.configure(api_key=api_key, transport='rest') 
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.subheader("Choose a mode:")
        
        # Visszateszem az összes gombot
        cols = st.columns(4)
        
        # Egyszerűsített hívás a legstabilabb névvel
        if cols[1].button("🎮 Game"):
            st.session_state.messages = []
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content("You are a lost tourist in London. Start the conversation briefly!")
            st.session_state.messages.append({"role": "assistant", "content": res.text})

        # Chat megjelenítése
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Say something..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            
            with st.chat_message("assistant"):
                model = genai.GenerativeModel('gemini-1.5-flash')
                # Itt is a legegyszerűbb formát használjuk
                response = model.generate_content("Lost tourist persona: " + prompt)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Sajnos még mindig hiba van: {e}")
else:
    st.info("Please enter your API key!")
