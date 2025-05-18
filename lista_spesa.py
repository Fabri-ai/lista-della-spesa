import streamlit as st
import json
import os

st.set_page_config(page_title="Lista della Spesa Fab & Vik", layout="wide")

FILE_LISTA = "dati_lista.json"

utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if "lista" not in st.session_state:
    if os.path.exists(FILE_LISTA):
        with open(FILE_LISTA, "r") as f:
            st.session_state.lista = json.load(f)
    else:
        st.session_state.lista = []

# 🔐 Login
if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Entra"):
        if username in utenti_autorizzati and utenti_autorizzati[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Credenziali non valide")
else:
    # 🔓 Logout
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.title("🛒 Lista della Spesa Fab & Vik")

    # ➕ Aggiunta prodotti
    with st.form("Aggiungi prodotto"):
        prodotto = st.text_input("Prodotto")
        quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
        unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])
        costo_input = st.text_input("Costo (€)", placeholder="es. 4,50")
        data_acquisto = st.text_input("Data (mm-aaaa)", placeholder="es. 05-2025")
        negozio = st.text_input("Negozio", placeholder="es. Supermercato")
        submitted = st.form_submit_button("➕ Aggiungi")

        if submitted and prodotto:
            # Sostituzione virgola con punto per compatibilità
            costo = costo_input.replace(",", ".").strip()
            st.session_state.lista.append({
                "✔️ Elimina": False,
                "Prodotto": prodotto,
                "Quantità": quantita,
                "Unità": unita,
                "Costo (€)": costo,
                "Data": data_acquisto,
                "Negozio": negozio,
                "Acquistato": False
            })
            with open(FILE_LISTA, "w") as f:
                json.dump(st.session_state.lista, f, indent=2)
            st.success("✅ Prodotto aggiunto!")
            st.rerun()

    # 📋 Tabella modificabile
    if st.session_state.lista:
        st.subheader("📋 Lista Attuale")

        df = st.data_editor(
            st.session_state.lista,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "✔️ Elimina": st.column_config.CheckboxColumn(),
                "Prodotto": st.column_config.TextColumn(),
                "Quantità": st.column_config.NumberColumn(format="%.2f"),
                "Unità": st.column_config.TextColumn(),
                "Costo (€)": st.column_config.TextColumn(),
                "Data": st.column_config.TextColumn(help="Formato mm-aaaa"),
                "Negozio": st.column_config.TextColumn(),
                "Acquistato": st.column_config.CheckboxColumn()
            },
            hide_index=True
        )

        # 🔄 Salvataggio modifiche
        if df != st.session_state.lista:
            st.session_state.lista = df
            with open(FILE_LISTA, "w") as f:
                json.dump(df, f, indent=2)
            st.success("💾 Modifiche salvate!")

        # 🗑️ Rimozione elementi selezionati
        if any(item.get("✔️ Elimina") for item in st.session_state.lista):
            if st.button("🗑️ Rimuovi selezionati"):
                st.session_state.lista = [
                    item for item in st.session_state.lista if not item.get("✔️ Elimina", False)
                ]
                with open(FILE_LISTA, "w") as f:
                    json.dump(st.session_state.lista, f, indent=2)
                st.success("🗑️ Elementi eliminati")
                st.rerun()

    else:
        st.info("La lista è vuota. Aggiungi un prodotto.")
