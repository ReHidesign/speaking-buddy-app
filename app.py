import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

# API Kulcs kezelése
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = next((m for m in available_models if 'flash' in m), available_models[0])
        model = genai.GenerativeModel(model_name)

        # EZ AZ IGAZI INSTRUKCIÓ (A "Lélek")
        system_instruction = """
        Te egy 'Speaking Buddy' nevű angol nyelvi mentor vagy. 
        MÓDSZERTANOD:
        1. Javítsd ki a diák nyelvtani hibáit a válaszod elején kékkel vagy félkövérrel.
        2. Mindig kérdezz valamit a végén.
        
        MÓDOK:
        - Start Level Test: 5 kérdéses szintfelmérő.
        - Challenge Mode: Te egy karakter vagy egy szituációban (pl. elveszett turista, pincér, recepciós). A diáknak meg kell oldania a helyzetet angolul.
        - Picture Lab: Írj le egy festményt vagy fotót, amit neki le kell írnia.
        """

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Gombok
        st.subheader("Choose a mode:")
        cols = st.columns(4)
        if cols[0].button("📈 Test"): st.session_state.messages.append({"role": "user", "content": "Start Level Test"})
        if cols[1].button("🎮 Game"): st.session_state.messages.append({"role": "user", "content": "Challenge Mode - Be a lost tourist in London!"})
        if cols[2].button("🖼️ Picture"): st.session_state.messages.append({"role": "user", "content": "Picture Lab"})
        if cols[3].button("💬 Chat"): st.session_state.messages.append({"role": "user", "content": "Casual conversation"})

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("Talk to your Buddy..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                # Itt adjuk át a rendszer-utasítást és az előzményeket
                full_prompt = f"{system_instruction}\n\nUser: {prompt}"
                response = model.generate_content(full_prompt)
                st.write(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
    except Exception as e:
        st.error(f"Hiba: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot!")
