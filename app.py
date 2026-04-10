import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# API Kulcs
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # A legeslegbiztosabb modellnév
    model = genai.GenerativeModel('gemini-1.5-flash')

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.subheader("Choose a mode:")
    cols = st.columns(4)
    
    # Gombok - most csak sima szöveget küldünk, hátha a bonyolultabb kérés zavarta meg
    if cols[0].button("📈 Test"):
        st.session_state.messages.append({"role": "user", "content": "Let's start an English test."})
    if cols[1].button("🎮 Game"):
        st.session_state.messages.append({"role": "user", "content": "Play a game with me: you are a tourist."})
    if cols[2].button("🖼️ Picture"):
        st.session_state.messages.append({"role": "user", "content": "Describe a picture for me."})
    if cols[3].button("💬 Chat"):
        st.session_state.messages.append({"role": "user", "content": "Hello Buddy!"})

    # Chat megjelenítése
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Válaszadás - ez a rész volt az, ami az elején működött
    if prompt := st.chat_input("Type here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            try:
                # Minimális instrukció, hogy ne zavarjuk össze a rendszert
                response = model.generate_content("You are an English mentor. " + prompt)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Hiba történt: {e}")
else:
    st.info("Please enter your API key on the left.")
