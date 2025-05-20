import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Configurazione Streamlit ---
st.set_page_config(page_title="Lista della Spesa Fab & Vik", layout="wide")

# --- Autenticazione utenti ---
utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

# --- Google Sheets ---
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18gm99X8PTlhz5J7RkNhoYbyPPQlZc1QkT-TM9YRvu-A"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)
client = gspread.authorize(credentials)
sheet = client.open_by_url(SPREADSHEET_URL).sheet1

# --- Funzioni di utilità ---
@st.cache_data(ttl=60)
def carica_lista():
    try:
        dati = sheet.get_all_records()
        return pd.DataFrame(dati)
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return pd.DataFrame()

def salva_lista(df, msg_container=None):
    if msg_container:
        msg_container.info("💾 Sto salvando, attendi...")
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    if msg_container:
        msg_container.success("✅ Operazione completata!")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- Login ---
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
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.title("🛒 Lista della Spesa Fab & Vik")

    df_lista = carica_lista()

    # --- Estrai valori unici per i menu a tendina ---
    prodotti_esistenti = sorted(df_lista["Prodotto"].dropna().unique()) if "Prodotto" in df_lista else []
    negozi_esistenti = sorted(df_lista["Negozio"].dropna().unique()) if "Negozio" in df_lista else []
    mesi_esistenti = sorted(df_lista["Data"].dropna().unique()) if "Data" in df_lista else []

    # --- Aggiunta prodotto ---
    with st.form("Aggiungi prodotto"):
    prodotto_scelto = st.selectbox("Prodotto", options=[""] + (prodotti_esistenti if prodotti_esistenti else []))
    nuovo_prodotto = st.text_input("Nuovo prodotto")
    prodotto = nuovo_prodotto if nuovo_prodotto.strip() else prodotto_scelto

    quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
    unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])
    costo = st.number_input("Costo (€)", min_value=0.0, format="%.2f")

    data_scelta = st.selectbox("Data (mm-aaaa)", options=[""] + (mesi_esistenti if mesi_esistenti else []))
    nuova_data = st.text_input("Nuova data (mm-aaaa)")
    data = nuova_data if nuova_data.strip() else data_scelta

    negozio_scelto = st.selectbox("Negozio", options=[""] + (negozi_esistenti if negozi_esistenti else []))
    nuovo_negozio = st.text_input("Nuovo negozio")
    negozio = nuovo_negozio if nuovo_negozio.strip() else negozio_scelto

    submitted = st.form_submit_button("➕ Aggiungi")

    costo_input = st.text_input("Costo (€)", value="0,00")
    try:
        costo = float(costo_input.replace(",", "."))
    except ValueError:
        costo = 0.0

    data = st.selectbox("Data (mm-aaaa)", options=[""] + mesi_esistenti) or st.text_input("Nuova data (mm-aaaa)")
    negozio = st.selectbox("Negozio", options=[""] + negozi_esistenti) or st.text_input("Nuovo negozio")
    submitted = st.form_submit_button("➕ Aggiungi")

    if submitted and prodotto:
        nuovo = {
            "✔️ Elimina": False,
            "Prodotto": prodotto,
            "Quantità": quantita,
            "Unità": unita,
            "Costo (€)": round(costo, 2),
            "Data": data,
            "Negozio": negozio,
            "Acquistato": False
        }
        df_lista = pd.concat([df_lista, pd.DataFrame([nuovo])], ignore_index=True)
        salva_lista(df_lista)
        st.success("✅ Prodotto aggiunto!")
        st.rerun()

    # --- Filtri combinabili ---
    st.subheader("🔍 Filtri")
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_mese = st.selectbox("📅 Filtra per mese", options=[""] + mesi_esistenti)
    with col2:
        filtro_negozio = st.selectbox("🏪 Filtra per negozio", options=[""] + negozi_esistenti)
    with col3:
        filtro_prodotto = st.selectbox("🛍️ Filtra per prodotto", options=[""] + prodotti_esistenti)

    df_filtrato = df_lista.copy()
    if filtro_mese:
        df_filtrato = df_filtrato[df_filtrato["Data"] == filtro_mese]
    if filtro_negozio:
        df_filtrato = df_filtrato[df_filtrato["Negozio"] == filtro_negozio]
    if filtro_prodotto:
        df_filtrato = df_filtrato[df_filtrato["Prodotto"] == filtro_prodotto]

    # --- Tabella modificabile ---
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
                "Acquistato": st.column_config.CheckboxColumn()
            },
            hide_index=True
        )

        # --- Salvataggio modifiche ---
        if not df_modificato.equals(df_filtrato):
            idx_aggiornati = df_modificato.index
            df_lista.loc[idx_aggiornati] = df_modificato
            msg = st.empty()
            salva_lista(df_lista, msg)
            st.rerun()

       # --- Rimozione prodotti selezionati ---
        if df_modificato["✔️ Elimina"].any():
            if st.button("🗑️ Rimuovi selezionati"):
                # Assicuriamoci che "✔️ Elimina" sia booleano e senza NaN
                df_lista["✔️ Elimina"] = df_lista["✔️ Elimina"].fillna(False).astype(bool)
                df_lista = df_lista[~df_lista["✔️ Elimina"]]
                msg = st.empty()
                salva_lista(df_lista, msg)
                
                # Reset del flag elimina per evitare loop al reload
                df_lista["✔️ Elimina"] = False
                st.session_state["elimina_richiesto"] = False  # opzionale se usi session state per altri scopi
                
                st.rerun()
    else:
        st.info("La lista è vuota o nessun risultato corrisponde ai filtri.")
