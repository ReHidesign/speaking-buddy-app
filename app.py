import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # FIX MODELL (Nincs több keresgélés, ez a legstabilabb)
        model = genai.GenerativeModel('gemini-1.5-flash')

        system_instruction = """
        Te egy Speaking Buddy nevű angol mentor vagy. 
        SZABÁLY: Mindig javítsd ki a diák hibáit az üzeneted elején!
        MÓDOK:
        - Start Level Test: 5 kérdéses szintfelmérő.
        - Challenge Mode: Te egy karakter vagy (pl. eltévedt turista).
        - Picture Lab: Írj le egy képet.
        """

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Gombok
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        
        # Funkció a válasz generáláshoz, hogy ne ismételjük a kódot
        def get_ai_response(prompt_text):
            try:
                time.sleep(1) # Biztonsági szünet a kvóta miatt
                return model.generate_content(prompt_text).text
            except Exception as e:
                return f"Hiba a kapcsolódásnál: {e}"

        if cols[0].button("📈 Test"):
            st.session_state.messages = [{"role": "assistant", "content": get_ai_response(system_instruction + " Start a Level Test!")}]
        if cols[1].button("🎮 Game"):
            st.session_state.messages = [{"role": "assistant", "content": get_ai_response(system_instruction + " Start a Roleplay: you are a lost tourist in London!")}]
        if cols[2].button("🖼️ Picture"):
            st.session_state.messages = [{"role": "assistant", "content": get_ai_response(system_instruction + " Describe a picture for me to explain!")}]
        if cols[3].button("💬 Chat"):
            st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your Speaking Buddy. How are you today?"}]

        # Chat megjelenítése
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Üzenetküldés
        if prompt := st.chat_input("Write here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                context = system_instruction + "\n"
                for m in st.session_state.messages[-5:]:
                    context += f"{m['role']}: {m['content']}\n"
                
                response_text = get_ai_response(context)
                st.write(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

    except Exception as e:
        st.error(f"Valami nem stimmel: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot a bal oldalon!")
