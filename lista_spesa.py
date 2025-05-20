import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Lista della Spesa Fab & Vik", layout="wide")

# --- Configurazioni ---
utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18gm99X8PTlhz5J7RkNhoYbyPPQlZc1QkT-TM9YRvu-A"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(credentials)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1

@st.cache_data(ttl=60)
def carica_lista():
    dati = sheet.get_all_records()
    df = pd.DataFrame(dati)
    if not df.empty:
        df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce").fillna(0)
        df["Costo (€)"] = pd.to_numeric(df["Costo (€)"], errors="coerce").fillna(0.0)
        df["✔️ Elimina"] = df["✔️ Elimina"].astype(bool)
        df["Acquistato"] = df["Acquistato"].astype(bool)
    return df

def salva_lista(df):
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# --- SESSION STATE INIT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "login_success" not in st.session_state:
    st.session_state.login_success = False
if "is_saving" not in st.session_state:
    st.session_state.is_saving = False

def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_click = st.button("Entra")

    if login_click:
        if username in utenti_autorizzati and utenti_autorizzati[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.login_success = True  # Flag per rerun
        else:
            st.error("Credenziali non valide")

# --- MAIN ---
if not st.session_state.logged_in:
    login()
    if st.session_state.login_success:
        # Qui chiamiamo st.experimental_rerun solo in main, fuori dalla funzione
        st.session_state.login_success = False  # Reset flag
        st.experimental_rerun()
    st.stop()

# Ora utente è loggato

def logout():
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

logout()

st.title(f"🛒 Lista della Spesa Fab & Vik - Benvenuto {st.session_state.username}")

# Carica dati
df_lista = carica_lista()

# Filtri (prodotti, negozi, date)
prodotti_unici = sorted(df_lista["Prodotto"].dropna().unique()) if not df_lista.empty else []
negozi_unici = sorted(df_lista["Negozio"].dropna().unique()) if not df_lista.empty else []
date_uniche = sorted(df_lista["Data"].dropna().unique()) if not df_lista.empty else []

with st.expander("Filtri"):
    filtro_prodotto = st.multiselect("Filtra per prodotto", prodotti_unici)
    filtro_negozio = st.multiselect("Filtra per negozio", negozi_unici)
    filtro_data = st.multiselect("Filtra per data (mm-aaaa)", date_uniche)

# Applica filtri
df_filtrato = df_lista.copy()
if filtro_prodotto:
    df_filtrato = df_filtrato[df_filtrato["Prodotto"].isin(filtro_prodotto)]
if filtro_negozio:
    df_filtrato = df_filtrato[df_filtrato["Negozio"].isin(filtro_negozio)]
if filtro_data:
    df_filtrato = df_filtrato[df_filtrato["Data"].isin(filtro_data)]

# Form per aggiungere
with st.form("aggiungi_prodotto"):
    st.subheader("➕ Aggiungi Prodotto")

    nuovo_prodotto = st.text_input("Prodotto")
    if prodotti_unici:
        prodotto_scelto = st.selectbox("Scegli prodotto esistente", [""] + prodotti_unici)
        if prodotto_scelto:
            nuovo_prodotto = prodotto_scelto

    quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
    unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])
    costo = st.number_input("Costo (€)", min_value=0.0, format="%.2f", step=0.01)

    data = st.text_input("Data (mm-aaaa)", placeholder="es. 05-2025")
    if date_uniche:
        data_scelta = st.selectbox("Scegli data esistente", [""] + date_uniche)
        if data_scelta:
            data = data_scelta

    negozio = st.text_input("Negozio")
    if negozi_unici:
        negozio_scelto = st.selectbox("Scegli negozio esistente", [""] + negozi_unici)
        if negozio_scelto:
            negozio = negozio_scelto

    submitted = st.form_submit_button("➕ Aggiungi")

    if submitted:
        if not nuovo_prodotto.strip():
            st.error("Inserisci un prodotto valido.")
        else:
            nuovo_elemento = {
                "✔️ Elimina": False,
                "Prodotto": nuovo_prodotto.strip(),
                "Quantità": quantita,
                "Unità": unita,
                "Costo (€)": round(costo, 2),
                "Data": data.strip(),
                "Negozio": negozio.strip(),
                "Acquistato": False
            }
            df_lista = pd.concat([df_lista, pd.DataFrame([nuovo_elemento])], ignore_index=True)
            if not st.session_state.is_saving:
                st.session_state.is_saving = True
                with st.spinner("Sto salvando, attendi..."):
                    salva_lista(df_lista)
                st.success("✅ Prodotto aggiunto e salvato!")
                st.session_state.is_saving = False
                st.experimental_rerun()

# Mostra lista modificabile
if not df_filtrato.empty:
    st.subheader("📋 Lista Attuale")
    df_modificato = st.data_editor(
        df_filtrato,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "✔️ Elimina": st.column_config.CheckboxColumn(),
            "Prodotto": st.column_config.TextColumn(),
            "Quantità": st.column_config.NumberColumn(format="%.2f"),
            "Unità": st.column_config.TextColumn(),
            "Costo (€)": st.column_config.NumberColumn(format="%.2f"),
            "Data": st.column_config.TextColumn(help="Formato mm-aaaa"),
            "Negozio": st.column_config.TextColumn(),
            "Acquistato": st.column_config.CheckboxColumn(),
        },
        hide_index=True,
    )

    if not df_modificato.equals(df_filtrato):
        if not st.session_state.is_saving:
            st.session_state.is_saving = True
            with st.spinner("Sto salvando, attendi..."):
                df_non_filtrato = df_lista[~df_lista.index.isin(df_filtrato.index)]
                df_lista_aggiornato = pd.concat([df_non_filtrato, df_modificato], ignore_index=True)
                salva_lista(df_lista_aggiornato)
            st.success("💾 Modifiche salvate!")
            st.session_state.is_saving = False
            st.experimental_rerun()
else:
    st.info("Nessun elemento corrisponde ai filtri selezionati.")
