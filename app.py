import streamlit as st
import google.generativeai as genai

# Oldal konfiguráció
st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

# Lábléc
st.markdown("""
    <style>
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: grey; text-align: center; padding: 10px; font-size: 12px; border-top: 1px solid #eee; z-index: 1000;}
    </style>
    <div class="footer"><p>© 2026 Speaking Buddy AI Mentor | All Rights Reserved | Created for Education</p></div>
    """, unsafe_allow_html=True)

# API Kulcs a sidebarban
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Automatikus modell választás (az előbb bevált módszer)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if 'flash' in m), available_models[0])
        model = genai.GenerativeModel(model_name)

        # Részletes pedagógiai utasítás (A "Lélek")
        system_instruction = """
        Te egy 'Speaking Buddy' nevű angol nyelvi mentor vagy. 
        A feladatod: segíteni középiskolás diákoknak (A1-C1 szint) az angol beszédben.
        
        MÓDSZERTANOD:
        1. Ha a diák hibázik, a válaszod elején javítsd ki finoman (pl. "You said 'I have 15 years old', but correctly: 'I am 15 years old'").
        2. Mindig válaszolj az üzenetére, majd tegyél fel EGY izgalmas kérdést, ami fenntartja a beszélgetést.
        3. Stílusod: bátorító, modern, barátságos.
        
        SPECIÁLIS MÓDOK (ha a felhasználó kéri):
        - Start Level Test: Tegyél fel 5 kérdést egymás után (egyesével), majd a végén értékeld a szintjét.
        - Challenge Mode: Adj egy vicces vagy életszerű szituációt (pl. eltévedtél Londonban), amit meg kell oldania.
        - Picture Lab: Írj le egy részletes, érdekes képet, amit neki el kell képzelnie, és mesélnie kell róla.
        """

        if "messages" not in st.session_state:
            st.session_state.messages = []

        st.subheader("Choose a mode to start:")
        cols = st.columns(4)
        if cols[0].button("📈 Test"): st.session_state.messages.append({"role": "user", "content": "Start Level Test"})
        if cols[1].button("🎮 Game"): st.session_state.messages.append({"role": "user", "content": "Challenge Mode"})
        if cols[2].button("🖼️ Picture"): st.session_state.messages.append({"role": "user", "content": "Picture Lab"})
        if cols[3].button("💬 Chat"): st.session_state.messages.append({"role": "user", "content": "Casual Chat"})

        # Előzmények
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Üzenetküldés
        if prompt := st.chat_input("Speak to your Buddy..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Itt adjuk át a teljes környezetet az AI-nak
                full_context = f"{system_instruction}\n\nChat history so far:\n"
                for m in st.session_state.messages[-5:]: # Az utolsó 5 üzenetet látja
                    full_context += f"{m['role']}: {m['content']}\n"
                
                response = model.generate_content(full_context)
                if response:
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                
    except Exception as e:
        st.error(f"Hiba: {e}")
else:
    st.info("Kérlek, add meg az API kulcsodat a bal oldalon a kezdéshez!")
