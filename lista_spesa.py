import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Lista della Spesa Fab & Vik", page_icon="🛒")

# 👥 Credenziali
UTENTI = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

# 📁 Percorso file CSV condiviso
PERCORSO_FILE = "lista_spesa.csv"

# 📦 Carica lista
def carica_lista():
    try:
        df = pd.read_csv(PERCORSO_FILE)
        df["Acquistato"] = df["Acquistato"].fillna(False).astype(bool)
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=["Prodotto", "Quantità", "Unità", "Costo", "Data", "Negozio", "Acquistato"])

# 💾 Salva lista
def salva_lista(df):
    df.to_csv(PERCORSO_FILE, index=False)

# 🧾 LOGIN
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

st.title("🛍️ Lista della Spesa Fab & Vik")

if not st.session_state.logged_in:
    with st.form("login"):
        st.subheader("🔐 Login")
        username = st.text_input("👤 Nome utente")
        password = st.text_input("🔑 Password", type="password")
        submitted = st.form_submit_button("Entra")

        if submitted:
            if username in UTENTI and UTENTI[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Benvenuto, {username}!")
                st.rerun()
            else:
                st.error("Credenziali non valide.")
else:
    st.sidebar.success(f"👋 Ciao, {st.session_state.username}")

    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.subheader("➕ Aggiungi nuovo prodotto")

    prodotto = st.text_input("📦 Nome prodotto")
    quantita = st.text_input("🔢 Quantità")
    unita = st.selectbox("⚖️ Unità di misura", ["", "pz", "kg", "g", "L", "ml", "bottiglia", "scatola", "altro"])
    costo = st.text_input("💰 Costo (facoltativo)")
    data = st.date_input("📅 Data di acquisto (facoltativa)", value=datetime.today())
    negozio = st.text_input("🏪 Negozio (facoltativo)")

    df_lista = carica_lista()

    if st.button("✅ Aggiungi alla lista"):
        if prodotto:
            nuova_riga = {
                "Prodotto": prodotto,
                "Quantità": quantita,
                "Unità": unita,
                "Costo": float(costo) if costo else 0.0,
                "Data": data.strftime("%m-%Y"),  # 📅 Formato mm-aaaa
                "Negozio": negozio,
                "Acquistato": False  # ⬜ Checkbox inizialmente non spuntato
            }
            df_lista = pd.concat([df_lista, pd.DataFrame([nuova_riga])], ignore_index=True)
            salva_lista(df_lista)
            st.success(f"{prodotto} aggiunto!")
            st.rerun()
        else:
            st.warning("⚠️ Il nome del prodotto è obbligatorio.")

    st.divider()
    st.subheader("📋 Modifica la lista")

    if df_lista.empty:
        st.info("La lista è vuota.")
    else:
        # 📝 Editor tipo Excel con checkbox
        df_modificato = st.data_editor(
            df_lista,
            column_config={
                "Prodotto": st.column_config.TextColumn("🛒 Prodotto"),
                "Quantità": st.column_config.TextColumn("🔢 Quantità"),
                "Unità": st.column_config.TextColumn("⚖️ Unità"),
                "Costo": st.column_config.NumberColumn("💰 Costo"),
                "Data": st.column_config.TextColumn("📅 Data (mm-aaaa)"),
                "Negozio": st.column_config.TextColumn("🏪 Negozio"),
                "Acquistato": st.column_config.CheckboxColumn("✅ Acquistato")
            },
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("💾 Salva modifiche"):
            salva_lista(df_modificato)
            st.success("Lista aggiornata con successo!")
            st.rerun()

        # 📈 Grafico spese (solo se ci sono date valide)
        st.subheader("📈 Totale spese per mese")
        try:
            spese_per_data = df_lista.copy()
            spese_per_data["Data"] = pd.to_datetime(spese_per_data["Data"], format="%m-%Y")
            grafico = spese_per_data.groupby("Data")["Costo"].sum().reset_index()
            st.line_chart(grafico.rename(columns={"Data": "index"}).set_index("index"))
        except:
            st.info("Formato date non valido per il grafico.")

        # 🗑️ Rimozione
        st.subheader("❌ Rimuovi un prodotto")
        da_rimuovere = st.selectbox("Seleziona", [""] + list(df_lista["Prodotto"]))

        if st.button("🗑️ Rimuovi"):
            df_lista = df_lista[df_lista["Prodotto"] != da_rimuovere]
            salva_lista(df_lista)
            st.success(f"{da_rimuovere} rimosso!")
            st.rerun()
