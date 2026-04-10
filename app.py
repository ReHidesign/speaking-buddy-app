import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# API Kulcs kezelése
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # JAVÍTÁS 1: A legújabb modell hivatkozás
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

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

        # Üzenetküldés
        if prompt := st.chat_input("Write here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # JAVÍTÁS 2: Generálás kényszerítése a legújabb protokollal
                response = model.generate_content(
                    f"System: You are an English teacher. Answer the user briefly. User: {prompt}",
                    generation_config=genai.types.GenerationConfig(candidate_count=1)
                )
                if response:
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                
    except Exception as e:
        # Itt pontosabb hibaüzenetet kapunk, ha valami mégsem stimmel
        st.error(f"Technikai részlet: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot a bal oldalon!")
