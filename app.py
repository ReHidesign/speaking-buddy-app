import streamlit as st
import google.generativeai as genai

# --- OLDAL BEÁLLÍTÁSAI ---
st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧", layout="centered")

# --- COPYRIGHT LÁBLÉC ---
footer = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: white;
    color: grey;
    text-align: center;
    padding: 10px;
    font-size: 12px;
    border-top: 1px solid #eee;
}
</style>
<div class="footer">
    <p>© 2026 Speaking Buddy AI Mentor | All Rights Reserved | Educational Tool</p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)

# --- API BEÁLLÍTÁS ---
# Ide jön majd az API kulcsod titkosítva, de teszthez beírhatod a sidebarba
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # A Flash gyorsabb és ingyenesebb

    # --- INSTRUKCIÓK ---
    system_prompt = "You are a professional English Speaking Buddy for high school students. Always encourage them, use simple feedback, and end with a question. Modes: Casual Chat, Challenge Mode, Picture Lab, Level Test."

    # Chat memória kezelése
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- GOMBOK ---
    st.subheader("Choose a mode:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📈 Test"):
            st.session_state.messages.append({"role": "user", "content": "I want to start a Level Test."})
    with col2:
        if st.button("🎮 Game"):
            st.session_state.messages.append({"role": "user", "content": "Let's play Challenge Mode."})
    with col3:
        if st.button("🖼️ Picture"):
            st.session_state.messages.append({"role": "user", "content": "I want to do a Picture Lab task."})
    with col4:
        if st.button("💬 Chat"):
            st.session_state.messages.append({"role": "user", "content": "Let's just have a casual conversation."})

    # Chat megjelenítése
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Bevitel
    if prompt := st.chat_input("Speak to me..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            response = model.generate_content([system_prompt] + [m["content"] for m in st.session_state.messages])
            st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.info("Kérlek, add meg az API kulcsot a bal oldali sávban az indításhoz!")
