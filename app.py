import streamlit as st
import google.generativeai as genai
import time

st.set_page_config(page_title="Speaking Buddy AI", page_icon="🇬🇧")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- GOLYÓÁLLÓ MODELL VÁLASZTÓ ---
        if "active_model" not in st.session_state:
            # Végigpróbáljuk a leggyakoribb neveket
            potential_names = ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro']
            found_model = None
            for name in potential_names:
                try:
                    m = genai.GenerativeModel(name)
                    m.generate_content("test", generation_config={"candidate_count": 1})
                    found_model = name
                    break
                except:
                    continue
            st.session_state.active_model = found_model

        if not st.session_state.active_model:
            st.error("Nem sikerült elérhető AI modellt találni. Ellenőrizd az API kulcsod!")
        else:
            model = genai.GenerativeModel(st.session_state.active_model)

            system_instruction = """
            Te egy Speaking Buddy nevű angol mentor vagy. 
            SZABÁLY: Mindig javítsd ki a diák hibáit az üzeneted elején!
            MÓDOK:
            - Start Level Test: 5 kérdéses szintfelmérő.
            - Challenge Mode: Te egy karakter vagy (pl. elveszett turista).
            - Picture Lab: Írj le egy képet.
            """

            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Gombok
            st.subheader("Choose a mode:")
            cols = st.columns(4)
            modes = [
                ("📈 Test", "Start the Level Test!"),
                ("🎮 Game", "Start Challenge Mode: be a lost tourist!"),
                ("🖼️ Picture", "Start Picture Lab!"),
                ("💬 Chat", "Let's just chat!")
            ]

            for i, (label, cmd) in enumerate(modes):
                if cols[i].button(label):
                    st.session_state.messages = [{"role": "user", "content": f"SYSTEM_CMD: {cmd}"}]
                    try:
                        resp = model.generate_content(system_instruction + " " + cmd)
                        st.session_state.messages.append({"role": "assistant", "content": resp.text})
                    except Exception as e:
                        st.error(f"Gomb hiba: {e}")

            # Chat megjelenítése
            for msg in st.session_state.messages:
                if "SYSTEM_CMD" not in msg["content"]:
                    with st.chat_message(msg["role"]):
                        st.write(msg["content"])

            # Válasz beküldése
            if prompt := st.chat_input("Speak to Buddy..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.write(prompt)

                with st.chat_message("assistant"):
                    history = system_instruction + "\n"
                    for m in st.session_state.messages[-5:]:
                        history += f"{m['role']}: {m['content']}\n"
                    
                    time.sleep(1) # Kvóta védelem
                    response = model.generate_content(history)
                    st.write(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        if "404" in str(e):
            st.warning("A Google még frissíti a modellt a kulcsodhoz. Próbáld meg 1 perc múlva!")
        elif "429" in str(e):
            st.error("Túl sok kérés! Várj 30 másodpercet.")
        else:
            st.error(f"Hiba: {e}")
else:
    st.info("Kérlek, add meg az API kulcsot!")
