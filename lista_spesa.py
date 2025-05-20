import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

# --- Impostazioni ---
st.set_page_config(page_title="Lista della Spesa", page_icon="🛒", layout="centered")

# --- Connessione a Google Sheets ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_URL = st.secrets["private_gsheets_url"]

credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(credentials)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1

# --- Utility ---
def carica_dati():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df["Data"] = pd.to_datetime(df["Data"], format="%Y-%m-%d")
        df["Costo (€)"] = pd.to_numeric(df["Costo (€)"], errors="coerce")
    return df

def salva_riga(data, prodotto, negozio, costo):
    sheet.append_row([data.strftime("%Y-%m-%d"), prodotto, negozio, f"{costo:.2f}", "", ""])

def aggiorna_google_sheet(df):
    sheet.clear()
    sheet.append_row(df.columns.tolist())
    sheet.append_rows(df.values.tolist())

# --- Login ---
def login():
    st.title("🔐 Login")
    password = st.text_input("Inserisci la password:", type="password")
    if st.button("Accedi"):
        if password == st.secrets["app_password"]:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("❌ Password errata")

if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    login()
    st.stop()

# --- App ---
st.title("🛒 Lista della Spesa")
df = carica_dati()

# --- Inserimento nuova riga ---
st.subheader("➕ Aggiungi prodotto")
col1, col2, col3, col4 = st.columns(4)

with col1:
    data = st.date_input("Data", value=datetime.today())
with col2:
    prodotti_esistenti = sorted(df["Prodotto"].dropna().unique()) if not df.empty else []
    prodotto = st.selectbox("Prodotto", options=prodotti_esistenti + ["Altro"], index=0)
    if prodotto == "Altro":
        prodotto = st.text_input("Inserisci nuovo prodotto")
with col3:
    negozi_esistenti = sorted(df["Negozio"].dropna().unique()) if not df.empty else []
    negozio = st.selectbox("Negozio", options=negozi_esistenti + ["Altro"], index=0)
    if negozio == "Altro":
        negozio = st.text_input("Inserisci nuovo negozio")
with col4:
    costo = st.number_input("Costo (€)", min_value=0.0, format="%.2f")

if st.button("Salva prodotto"):
    with st.spinner("💾 Sto salvando, attendi..."):
        salva_riga(data, prodotto, negozio, costo)
        st.success("✅ Prodotto salvato correttamente!")
        st.rerun()

# --- Filtri ---
st.subheader("🔍 Filtra la lista")
colf1, colf2, colf3 = st.columns(3)

with colf1:
    mesi = sorted(df["Data"].dt.strftime("%Y-%m").unique()) if not df.empty else []
    mese_scelto = st.selectbox("Filtro per mese", options=["Tutti"] + mesi)
with colf2:
    negozi = sorted(df["Negozio"].dropna().unique()) if not df.empty else []
    negozio_scelto = st.selectbox("Filtro per negozio", options=["Tutti"] + negozi)
with colf3:
    prodotti = sorted(df["Prodotto"].dropna().unique()) if not df.empty else []
    prodotto_scelto = st.selectbox("Filtro per prodotto", options=["Tutti"] + prodotti)

# --- Applica filtri ---
df_filtrato = df.copy()
if mese_scelto != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Data"].dt.strftime("%Y-%m") == mese_scelto]
if negozio_scelto != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Negozio"] == negozio_scelto]
if prodotto_scelto != "Tutti":
    df_filtrato = df_filtrato[df_filtrato["Prodotto"] == prodotto_scelto]

# --- Visualizza e modifica dati ---
if not df_filtrato.empty:
    st.subheader("📋 Lista attuale")

    df_modificato = st.data_editor(
        df_filtrato,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Costo (€)": st.column_config.NumberColumn("Costo (€)", format="%.2f"),
            "Eliminato": st.column_config.CheckboxColumn("❌ Elimina"),
            "Acquistato": st.column_config.CheckboxColumn("✅ Acquistato"),
        },
        disabled=["Data", "Prodotto", "Negozio"],
        key="editor"
    )

    if st.button("Salva modifiche"):
        with st.spinner("💾 Salvataggio in corso..."):
            df_finale = df.copy()
            df_finale.update(df_modificato)
            df_finale = df_finale[df_finale["Eliminato"] != True]
            aggiorna_google_sheet(df_finale)
            st.success("✅ Modifiche salvate con successo!")
            st.rerun()
else:
    st.info("Nessun dato disponibile con i filtri selezionati.")
