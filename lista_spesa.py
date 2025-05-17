import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 🔐 Utenti autorizzati
utenti = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

st.set_page_config(page_title="Lista della Spesa Fab & Vik", page_icon="🛍️")

st.title("🛍️ Lista della Spesa Fab & Vik")

# 📁 File CSV per la persistenza
FILE_PATH = "lista.csv"

# 📦 Stato iniziale
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# 📥 Funzione caricamento lista
def carica_lista():
    if os.path.exists(FILE_PATH):
        return pd.read_csv(FILE_PATH)
    else:
        return pd.DataFrame(columns=["Prodotto", "Costo", "Data"])

# 💾 Funzione salvataggio
def salva_lista(df):
    df.to_csv(FILE_PATH, index=False)

# 🔐 LOGIN
if not st.session_state.logged_in:
    username = st.text_input("👤 Nome utente")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Accedi"):
        if utenti.get(username) == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Credenziali errate.")

# 🛒 APP - Lista visibile solo dopo login
else:
    st.sidebar.success(f"👋 Ciao, {st.session_state.username}")

    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Carica la lista
    df_lista = carica_lista()

    st.subheader("➕ Aggiungi nuovo prodotto")

    col1, col2 = st.columns([2, 1])
    with col1:
        prodotto = st.text_input("📦 Nome prodotto")
    with col2:
        costo = st.text_input("💰 Costo (facoltativo)")

    data = st.date_input("📅 Data di acquisto (facoltativa)", value=datetime.today())

    if st.button("✅ Aggiungi alla lista"):
        if prodotto:
            nuova_riga = {
                "Prodotto": prodotto,
                "Costo": costo if costo else "",
                "Data": data.strftime("%Y-%m-%d") if data else ""
            }
            df_lista = pd.concat([df_lista, pd.DataFrame([nuova_riga])], ignore_index=True)
            salva_lista(df_lista)
            st.success(f"{prodotto} aggiunto!")
            st.rerun()
        else:
            st.warning("Il prodotto è obbligatorio.")

    st.divider()
    st.subheader("📋 Lista attuale")

    if df_lista.empty:
        st.info("La lista è vuota.")
    else:
        # ✅ Modifica campi esistenti
        for i in range(len(df_lista)):
            st.markdown(f"**🛒 {df_lista.at[i, 'Prodotto']}**")

            col1, col2 = st.columns(2)
            with col1:
                nuovo_costo = st.text_input(f"Costo", value=str(df_lista.at[i, "Costo"]), key=f"costo_{i}")
            with col2:
                nuova_data = st.date_input("Data", 
                                           value=pd.to_datetime(df_lista.at[i, "Data"]) if df_lista.at[i, "Data"] else datetime.today(), 
                                           key=f"data_{i}")

            # Aggiorna nel DataFrame temporaneamente
            df_lista.at[i, "Costo"] = nuovo_costo
            df_lista.at[i, "Data"] = nuova_data.strftime("%Y-%m-%d")

            st.markdown("---")

        if st.button("💾 Salva modifiche"):
            salva_lista(df_lista)
            st.success("Lista aggiornata con successo!")
            st.rerun()

        # 🔴 Rimozione prodotto
        st.subheader("❌ Rimuovi un prodotto")
        da_rimuovere = st.selectbox("Seleziona", [""] + list(df_lista["Prodotto"]))

        if st.button("🗑️ Rimuovi"):
            df_lista = df_lista[df_lista["Prodotto"] != da_rimuovere]
            salva_lista(df_lista)
            st.success(f"{da_rimuovere} rimosso!")
            st.rerun()
