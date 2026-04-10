import streamlit as st
import google.generativeai as genai

# --- OLDAL BEÁLLÍTÁSAI ---
st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# --- COPYRIGHT LÁBLÉC ---
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: grey; text-align: center; padding: 10px; font-size: 12px; border-top: 1px solid #eee; }
    </style>
    <div class="footer"><p>© 2026 Speaking Buddy AI Mentor | All Rights Reserved</p></div>
    """, unsafe_allow_html=True)

# --- API BEÁLLÍTÁS ---
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Próbáljuk a legbiztosabb modell nevet
        model = genai.GenerativeModel('models/gemini-1.5-flash')

        system_instruction = "You are Speaking Buddy, a friendly English mentor. Correct errors briefly and always end with a question."

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Módválasztó gombok
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        modes = {"📈 Test": "Start a Level Test", "🎮 Game": "Challenge Mode", "🖼️ Picture": "Picture Lab", "💬 Chat": "Casual conversation"}
        
        for i, (label, cmd) in enumerate(modes.items()):
            if cols[i].button(label):
                st.session_state.messages.append({"role": "user", "content": cmd})

        # Chat előzmények
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Üzenetküldés
        if prompt := st.chat_input("Write here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                try:
                    # Ez a formátum stabilabb a Streamlit felhőben
                    chat = model.start_chat(history=[])
                    full_prompt = f"{system_instruction}\n\nUser says: {prompt}"
                    response = chat.send_message(full_prompt)
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as ai_err:
                    st.error(f"AI Error: {ai_err}")
                
    except Exception as e:
        st.error(f"Connection Error: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot a bal oldalon!")
