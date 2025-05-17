import streamlit as st
import pandas as pd
from datetime import datetime
import os

# 🔐 Utenti autorizzati
utenti = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb",
    "admin": "adminpass"
}

st.set_page_config(page_title="Lista della Spesa", page_icon="🛒")

st.title("🛒 Lista della Spesa Fab & Vik")

# 📁 File CSV per la persistenza
FILE_PATH = "lista.csv"

# 📦 Inizializzazione stato
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ✅ Funzione per caricare la lista dal file
def carica_lista():
    if os.path.exists(FILE_PATH):
        return pd.read_csv(FILE_PATH)
    else:
        return pd.DataFrame(columns=["Prodotto", "Costo", "Data"])

# ✅ Funzione per salvare la lista nel file
def salva_lista(df):
    df.to_csv(FILE_PATH, index=False)

# ✅ LOGIN
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

# ✅ LISTA DOPO LOGIN
else:
    st.sidebar.success(f"👋 Ciao, {st.session_state.username}")

    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.header("📝 Aggiungi un prodotto alla lista")

    prodotto = st.text_input("📦 Nome prodotto")
    costo = st.text_input("💰 Costo (facoltativo)")
    data = st.date_input("📅 Data di acquisto (facoltativa)", value=datetime.today())

    df_lista = carica_lista()

    if st.button("➕ Aggiungi"):
        if prodotto:
            nuova_riga = {
                "Prodotto": prodotto,
                "Costo": costo if costo else "",
                "Data": data.strftime("%Y-%m-%d") if data else ""
            }
            df_lista = pd.concat([df_lista, pd.DataFrame([nuova_riga])], ignore_index=True)
            salva_lista(df_lista)
            st.success(f"✅ {prodotto} aggiunto!")
            st.rerun()
        else:
            st.warning("Inserisci almeno il nome del prodotto.")

    st.divider()

    st.subheader("📋 Lista della spesa")

    if df_lista.empty:
        st.info("La lista è vuota.")
    else:
        st.dataframe(df_lista, use_container_width=True)

        prodotto_rimuovi = st.selectbox("❌ Rimuovi un prodotto", [""] + list(df_lista["Prodotto"]))

        if st.button("🗑️ Rimuovi"):
            df_lista = df_lista[df_lista["Prodotto"] != prodotto_rimuovi]
            salva_lista(df_lista)
            st.success(f"{prodotto_rimuovi} rimosso!")
            st.rerun()
