import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

# API Kulcs kezelése
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # A PROFI INSTRUKCIÓ (A "Lélek")
        system_instruction = """
        Te egy Speaking Buddy nevű angol mentor vagy. 
        SZABÁLY: Mindig javítsd ki a diák hibáit az üzeneted elején!
        MÓDOK:
        - Start Level Test: 5 kérdéses szintfelmérő.
        - Challenge Mode: Te egy karakter vagy (pl. elveszett turista). Indítsd te a párbeszédet!
        - Picture Lab: Írj le egy képet, amit neki le kell írnia.
        """

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # --- ITT VAN AZ ÖSSZES GOMB ÚJRA ---
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        
        if cols[0].button("📈 Test"):
            st.session_state.messages = [{"role": "user", "content": "START TEST"}]
            response = model.generate_content(system_instruction + " Start the Level Test with the first question!")
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        if cols[1].button("🎮 Game"):
            st.session_state.messages = [{"role": "user", "content": "START GAME"}]
            response = model.generate_content(system_instruction + " Start the game as a lost tourist in London!")
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        if cols[2].button("🖼️ Picture"):
            st.session_state.messages = [{"role": "user", "content": "START PICTURE LAB"}]
            response = model.generate_content(system_instruction + " Describe a picture for me to talk about!")
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        if cols[3].button("💬 Chat"):
            st.session_state.messages = [{"role": "user", "content": "Casual conversation"}]
            st.session_state.messages.append({"role": "assistant", "content": "Hi! I'm your Speaking Buddy. What's on your mind?"})

        # Chat megjelenítése (elrejtve a belső parancsokat)
        for msg in st.session_state.messages:
            if "START " not in msg["content"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        # Válaszadás logikája
        if prompt := st.chat_input("Help the tourist / Answer Buddy..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Előzmények összefűzése a memóriához
                history_text = system_instruction + "\n"
                for m in st.session_state.messages[-6:]:
                    history_text += f"{m['role']}: {m['content']}\n"
                
                time.sleep(1) # Megelőzzük a kvóta-hibát
                response = model.generate_content(history_text)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        if "429" in str(e):
            st.error("Lassítsunk egy kicsit! A Google ingyenes rendszere várni kér kb. 30 másodpercet.")
        else:
            st.error(f"Hiba történt: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot a kezdéshez!")
