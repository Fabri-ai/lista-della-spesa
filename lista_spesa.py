import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configurazione pagina
st.set_page_config(page_title="Lista della Spesa Fab & Vik", layout="wide")

# Utenti autorizzati
utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

# Google Sheet info
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18gm99X8PTlhz5J7RkNhoYbyPPQlZc1QkT-TM9YRvu-A"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Carica credenziali da secrets.toml
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

client = gspread.authorize(credentials)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1

# Funzioni utilità
@st.cache_data(ttl=60)
def carica_lista():
    try:
        dati = sheet.get_all_records()
        df = pd.DataFrame(dati)
        # Assicuriamoci i tipi corretti
        if not df.empty:
            df["Quantità"] = pd.to_numeric(df["Quantità"], errors="coerce").fillna(0)
            df["Costo (€)"] = pd.to_numeric(df["Costo (€)"], errors="coerce").fillna(0.0)
            df["✔️ Elimina"] = df["✔️ Elimina"].astype(bool)
            df["Acquistato"] = df["Acquistato"].astype(bool)
        return df
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return pd.DataFrame()

def salva_lista(df):
    # Converti i bool in stringhe booleane
    df_salva = df.copy()
    df_salva["✔️ Elimina"] = df_salva["✔️ Elimina"].astype(bool)
    df_salva["Acquistato"] = df_salva["Acquistato"].astype(bool)
    sheet.clear()
    sheet.update([df_salva.columns.values.tolist()] + df_salva.values.tolist())

# --- SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if "is_saving" not in st.session_state:
    st.session_state.is_saving = False

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Entra"):
        if username in utenti_autorizzati and utenti_autorizzati[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.experimental_rerun()
        else:
            st.error("Credenziali non valide")
    st.stop()

# --- LOGOUT ---
if st.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.experimental_rerun()

st.title("🛒 Lista della Spesa Fab & Vik")

# Carica dati
df_lista = carica_lista()

# Filtri dinamici
prodotti_unici = sorted(df_lista["Prodotto"].dropna().unique().tolist()) if not df_lista.empty else []
negozi_unici = sorted(df_lista["Negozio"].dropna().unique().tolist()) if not df_lista.empty else []
date_uniche = sorted(df_lista["Data"].dropna().unique().tolist()) if not df_lista.empty else []

# Dropdown filtri multipli
with st.expander("Filtri"):
    filtro_prodotto = st.multiselect("Filtra per prodotto", prodotti_unici)
    filtro_negozio = st.multiselect("Filtra per negozio", negozi_unici)
    filtro_data = st.multiselect("Filtra per data (mm-aaaa)", date_uniche)

# Filtra il dataframe in base ai filtri
df_filtrato = df_lista.copy()
if filtro_prodotto:
    df_filtrato = df_filtrato[df_filtrato["Prodotto"].isin(filtro_prodotto)]
if filtro_negozio:
    df_filtrato = df_filtrato[df_filtrato["Negozio"].isin(filtro_negozio)]
if filtro_data:
    df_filtrato = df_filtrato[df_filtrato["Data"].isin(filtro_data)]

# --- FORM AGGIUNGI PRODOTTO ---
with st.form("aggiungi_prodotto"):
    st.subheader("➕ Aggiungi Prodotto")
    
    # Dropdown dinamici per prodotto, negozio, data
    nuovo_prodotto = st.text_input("Prodotto")
    if prodotti_unici:
        prodotto_scelto = st.selectbox("Scegli prodotto esistente", [""] + prodotti_unici)
        if prodotto_scelto:
            nuovo_prodotto = prodotto_scelto

    quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
    unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])
    costo = st.number_input("Costo (€)", min_value=0.0, format="%.2f", step=0.01)
    
    # Per la data, dropdown da date uniche o testo libero
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
            # Salvataggio con messaggi e lock per evitare chiamate multiple
            if not st.session_state.is_saving:
                st.session_state.is_saving = True
                with st.spinner("Sto salvando, attendi..."):
                    salva_lista(df_lista)
                st.success("✅ Prodotto aggiunto e salvato!")
                st.session_state.is_saving = False
                st.experimental_rerun()

# Mostra lista se non vuota
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

    # Salvataggio modifiche con lock e messaggi
    if not df_modificato.equals(df_filtrato):
        if not st.session_state.is_saving:
            st.session_state.is_saving = True
            with st.spinner("Sto salvando, attendi..."):
                # ATTENZIONE: dobbiamo salvare su foglio intero, quindi unire con dati non filtrati
                # Ricostruiamo df_lista aggiornato:
                # 1. Rimuoviamo dal df_lista i record filtrati attuali
                df_non_filtrato = df_lista[~df_lista.index.isin(df_filtrato.index)]
                # 2. Uniamo df_non_filtrato con df_modificato
                df_lista_aggiornato = pd.concat([df_non_filtrato, df_modificato], ignore_index=True)
                salva_lista(df_lista_aggiornato)
            st.success("💾 Modifiche salvate!")
            st.session_state.is_saving = False
            st.experimental_rerun()
else:
    st.info("Nessun elemento corrisponde ai filtri selezionati.")

