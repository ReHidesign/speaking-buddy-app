import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Speaking Buddy", page_icon="🇬🇧")

# API Kulcs kezelése a sidebarban
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # MEGOLDÁS: Megkeressük, mi érhető el a kulcsoddal
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Kiválasztjuk a flasht, ha van, különben az első elérhetőt
        model_name = next((m for m in available_models if 'flash' in m), available_models[0])
        model = genai.GenerativeModel(model_name)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Felület és gombok
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        if cols[0].button("📈 Test"): st.session_state.messages.append({"role": "user", "content": "Start Level Test"})
        if cols[1].button("🎮 Game"): st.session_state.messages.append({"role": "user", "content": "Challenge Mode"})
        if cols[2].button("🖼️ Picture"): st.session_state.messages.append({"role": "user", "content": "Picture Lab"})
        if cols[3].button("💬 Chat"): st.session_state.messages.append({"role": "user", "content": "Casual Chat"})

        # Chat előzmények megjelenítése
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # Üzenetküldés
        if prompt := st.chat_input("Write here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Egyszerű válaszadás
                full_prompt = f"System: You are an English mentor. User: {prompt}"
                response = model.generate_content(full_prompt)
                if response.text:
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                
    except Exception as e:
        st.error(f"Hiba történt: {e}")
else:
    st.info("Kérlek, másold be az API kulcsot a bal oldali mezőbe!")
