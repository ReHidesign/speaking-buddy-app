import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # A PROFI INSTRUKCIÓ
        system_instruction = """
        Te egy Speaking Buddy nevű angol mentor vagy. 
        SZABÁLY: Mindig javítsd ki a diák hibáit az üzeneted elején!
        GAME MODE: Te egy Londonban eltévedt turista vagy. Kérj segítséget a diáktól, és maradj végig szerepben!
        """

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Gombok kezelése - ÚGY, HOGY AZ AI INDÍTSON
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        
        if cols[1].button("🎮 Game"):
            # Töröljük a régi chatet, hogy tiszta lappal induljon a játék
            st.session_state.messages = [{"role": "user", "content": "START GAME: Be the lost tourist now!"}]
            # Itt rögtön legeneráljuk az AI első mondatát
            response = model.generate_content(system_instruction + " Start the game as the lost tourist!")
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        # Chat megjelenítése
        for msg in st.session_state.messages:
            if "START GAME" not in msg["content"]: # A belső parancsot ne mutassuk
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        # Válaszadás
        if prompt := st.chat_input("Help the tourist..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Küldjük az egészet, hogy ne essen ki a szerepből
                full_history = system_instruction + "\n"
                for m in st.session_state.messages[-5:]:
                    full_history += f"{m['role']}: {m['content']}\n"
                
                # Egy kis szünet a 429-es hiba elkerülésére
                time.sleep(1) 
                response = model.generate_content(full_history)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        if "429" in str(e):
            st.error("Lassítsunk egy kicsit! A Google ingyenes rendszere várni kér kb. 30 másodpercet.")
        else:
            st.error(f"Hiba: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot!")
