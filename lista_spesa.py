import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Lista della Spesa Fab & Vik", layout="centered")
st.title("📝 Lista della Spesa Fab & Vik")

# --- Credenziali utente ---
utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

# --- Inizializza sessione ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- Login ---
if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Entra"):
        if username in utenti_autorizzati and utenti_autorizzati[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.error("Credenziali non valide")

# --- Dopo login ---
if st.session_state.logged_in:
    st.success(f"Benvenuto, {st.session_state.username.capitalize()} 👋")
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    # --- Caricamento dati ---
    file_path = "lista_spesa.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=[
            "Prodotto", "Quantità", "Unità", "Costo (€)",
            "Data di acquisto", "Negozio", "Acquistato"
        ])

    # --- Aggiunta nuovo elemento ---
    with st.form("Aggiungi elemento"):
        st.subheader("➕ Aggiungi prodotto")
        col1, col2, col3 = st.columns(3)
        with col1:
            prodotto = st.text_input("Prodotto")
        with col2:
            quantita = st.number_input("Quantità", min_value=0.0, step=1.0, format="%.1f")
        with col3:
            unita = st.text_input("Unità", placeholder="es. kg, pezzi")

        col4, col5, col6 = st.columns(3)
        with col4:
            costo = st.number_input("Costo (€)", min_value=0.0, step=0.5, format="%.2f")
        with col5:
            data_acquisto = st.text_input("Data di acquisto (mm-aaaa)")
        with col6:
            negozio = st.text_input("Negozio")

        submitted = st.form_submit_button("Aggiungi")
        if submitted and prodotto.strip():
            nuovo = {
                "Prodotto": prodotto.strip(),
                "Quantità": quantita,
                "Unità": unita.strip(),
                "Costo (€)": costo,
                "Data di acquisto": data_acquisto.strip(),
                "Negozio": negozio.strip(),
                "Acquistato": False
            }
            df = df.append(nuovo, ignore_index=True)
            df.to_csv(file_path, index=False)
            st.success(f"✅ {prodotto} aggiunto!")
            st.experimental_rerun()

    # --- Editor tabella interattiva ---
    st.subheader("📋 La tua lista")
    df["Acquistato"] = df["Acquistato"].fillna(False).astype(bool)
    df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce").fillna(1)
    df["Costo (€)"] = pd.to_numeric(df["Costo (€)"], errors="coerce").fillna(0.0)
    df["Data di acquisto"] = df["Data di acquisto"].astype(str)

    df_mod = st.data_editor(
        df,
        column_config={
            "Prodotto": st.column_config.TextColumn("Prodotto"),
            "Quantità": st.column_config.NumberColumn("Quantità", step=1),
            "Unità": st.column_config.TextColumn("Unità"),
            "Costo (€)": st.column_config.NumberColumn("Costo (€)", format="%.2f"),
            "Data di acquisto": st.column_config.TextColumn("Data (mm-aaaa)"),
            "Negozio": st.column_config.TextColumn("Negozio"),
            "Acquistato": st.column_config.CheckboxColumn("✓ Acquistato")
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )

    # --- Salvataggio modifiche ---
    if df_mod.to_dict() != df.to_dict():
        df_mod.to_csv(file_path, index=False)
        st.success("💾 Lista aggiornata!")

