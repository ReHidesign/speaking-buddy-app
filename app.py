import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Próbáljuk a leguniverzálisabb nevet
        model = genai.GenerativeModel('gemini-pro')

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.subheader("Choose a mode:")
        cols = st.columns(4)
        
        # Ez a kis trükk segít elkerülni a hibát a gomboknál
        def safe_generate(p):
            try:
                time.sleep(1)
                return model.generate_content(p).text
            except Exception as err:
                return f"Wait a moment and try again! (Error: {err})"

        if cols[0].button("📈 Test"):
            st.session_state.messages = [{"role": "assistant", "content": safe_generate("Start an English level test!")}]
        if cols[1].button("🎮 Game"):
            st.session_state.messages = [{"role": "assistant", "content": safe_generate("Roleplay: You are a lost tourist in London. Ask me for help!")}]
        if cols[2].button("🖼️ Picture"):
            st.session_state.messages = [{"role": "assistant", "content": safe_generate("Describe a picture for me to talk about!")}]
        if cols[3].button("💬 Chat"):
            st.session_state.messages = [{"role": "assistant", "content": "Hi! How can I help you today?"}]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Write here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            with st.chat_message("assistant"):
                res = safe_generate(prompt)
                st.write(res)
                st.session_state.messages.append({"role": "assistant", "content": res})

    except Exception as e:
        st.error(f"Kapcsolódási hiba. Próbáld meg frissíteni az oldalt! ({e})")
else:
    st.info("Kérlek, add meg az API kulcsot!")
