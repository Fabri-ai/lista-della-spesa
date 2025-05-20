import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configura pagina Streamlit
st.set_page_config(page_title="Lista della Spesa Fab & Vik", layout="wide")

# Autenticazione utenti
utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

# URL e credenziali Google Sheet
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18gm99X8PTlhz5J7RkNhoYbyPPQlZc1QkT-TM9YRvu-A"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Carica credenziali da secrets.toml
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

client = gspread.authorize(credentials)
spreadsheet = client.open_by_url(SPREADSHEET_URL)
sheet = spreadsheet.sheet1

# --- Funzioni di utilità ---
@st.cache_data(ttl=60)
def carica_lista():
    try:
        dati = sheet.get_all_records()
        return pd.DataFrame(dati)
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return pd.DataFrame()

def salva_lista(df):
    try:
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Errore nel salvataggio: {e}")
        return False

def estrai_valori_unici(df, colonna):
    if colonna in df.columns:
        return sorted(df[colonna].dropna().unique().tolist())
    else:
        return []

# --- Session state ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if "saving" not in st.session_state:
    st.session_state.saving = False

# --- Login ---
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
else:
    if st.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    st.title("🛒 Lista della Spesa Fab & Vik")

    # Carica dati da Google Sheets
    df_lista = carica_lista()

    # Estrai valori unici per dropdown dinamici
    prodotti_unici = estrai_valori_unici(df_lista, "Prodotto")
    negozi_unici = estrai_valori_unici(df_lista, "Negozio")
    date_uniche = estrai_valori_unici(df_lista, "Data")  # formattata come mm-aaaa

    # Filtri multipli combinabili
    st.sidebar.header("Filtri Lista")
    filtro_prodotto = st.sidebar.multiselect("Filtra per prodotto", prodotti_unici, default=prodotti_unici)
    filtro_negozio = st.sidebar.multiselect("Filtra per negozio", negozi_unici, default=negozi_unici)
    filtro_data = st.sidebar.multiselect("Filtra per data (mm-aaaa)", date_uniche, default=date_uniche)

    # Applica filtri
    df_filtrato = df_lista[
        (df_lista["Prodotto"].isin(filtro_prodotto)) &
        (df_lista["Negozio"].isin(filtro_negozio)) &
        (df_lista["Data"].isin(filtro_data))
    ]

    # Form per aggiungere prodotto
    with st.form("Aggiungi prodotto"):
        # Input con dropdown dinamici per prodotto, negozio e data
        prodotto = st.selectbox("Prodotto", options=[""] + prodotti_unici, index=0)
        prodotto = st.text_input("Oppure inserisci nuovo prodotto", value="") if prodotto == "" else prodotto

        quantita = st.number_input("Quantità", min_value=0.0, step=1.0)

        unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])

        costo = st.number_input("Costo (€)", min_value=0.0, format="%.2f")

        data_inserimento = st.selectbox(
            "Data (mm-aaaa)", options=[""] + date_uniche, index=0)
        if data_inserimento == "":
            data_inserimento = st.text_input("Oppure inserisci data (mm-aaaa)", value="")
        negozio = st.selectbox("Negozio", options=[""] + negozi_unici, index=0)
        if negozio == "":
            negozio = st.text_input("Oppure inserisci nuovo negozio", value="")

        submitted = st.form_submit_button("➕ Aggiungi")

        if submitted:
            if prodotto == "":
                st.error("Inserisci un prodotto!")
            else:
                # Costruisci nuovo elemento
                nuovo_elemento = {
                    "✔️ Elimina": False,
                    "Prodotto": prodotto,
                    "Quantità": quantita,
                    "Unità": unita,
                    "Costo (€)": float(f"{costo:.2f}"),  # Assicura due decimali
                    "Data": data_inserimento if data_inserimento else "",
                    "Negozio": negozio if negozio else "",
                    "Acquistato": False
                }

                df_lista = pd.concat([df_lista, pd.DataFrame([nuovo_elemento])], ignore_index=True)

                st.session_state.saving = True
                with st.spinner("Sto salvando, attendi..."):
                    if salva_lista(df_lista):
                        st.success("✅ Prodotto aggiunto e salvato!")
                    else:
                        st.error("❌ Errore nel salvataggio.")

                st.session_state.saving = False
                st.experimental_rerun()

    if not df_filtrato.empty:
        st.subheader("📋 Lista Attuale")

        # Configurazione colonne per data_editor
        col_config = {
            "✔️ Elimina": st.column_config.CheckboxColumn(),
            "Prodotto": st.column_config.TextColumn(),
            "Quantità": st.column_config.NumberColumn(format="%.2f"),
            "Unità": st.column_config.TextColumn(),
            "Costo (€)": st.column_config.NumberColumn(format="%.2f"),
            "Data": st.column_config.TextColumn(help="Formato mm-aaaa"),
            "Negozio": st.column_config.TextColumn(),
            "Acquistato": st.column_config.CheckboxColumn()
        }

        # Disabilita editing se stai salvando per evitare chiamate multiple
        disabled = st.session_state.saving

        df_modificato = st.data_editor(
            df_filtrato,
            use_container_width=True,
            num_rows="dynamic",
            column_config=col_config,
            hide_index=True,
            disabled=disabled
        )

        # Salvataggio modifiche
        if not df_modificato.equals(df_filtrato) and not st.session_state.saving:
            st.session_state.saving = True
            with st.spinner("Sto salvando, attendi..."):
                if salva_lista(df_modificato):
                    st.success("💾 Modifiche salvate!")
                else:
                    st.error("❌ Errore nel salvataggio.")
            st.session_state.saving = False
            st.experimental_rerun()

        # Gestione eliminazione righe flaggate
        if df_modificato["✔️ Elimina"].any() and not st.session_state.saving:
            if st.button("🗑️ Rimuovi selezionati", disabled=st.session_state.saving):
                st.session_state.saving = True
                with st.spinner("Sto eliminando, attendi..."):
                    df_modificato = df_modificato[~df_modificato["✔️ Elimina"]]
                    if salva_lista(df_modificato):
                        st.success("🗑️ Elementi eliminati e salvati!")
                    else:
                        st.error("❌ Errore nel salvataggio durante l'eliminazione.")
                st.session_state.saving = False
                st.experimental_rerun()

    else:
        st.info("La lista è vuota. Aggiungi un prodotto.")
