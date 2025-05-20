import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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

# Caricamento dati iniziali
@st.cache_data(ttl=60)
def carica_lista():
    try:
        dati = sheet.get_all_records()
        return pd.DataFrame(dati)
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return pd.DataFrame()

# Salvataggio dati
def salva_lista(df):
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# Login
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

    # Raccogli prodotti e negozi unici per i menu a tendina
    prodotti_esistenti = sorted(df_lista["Prodotto"].dropna().unique()) if not df_lista.empty else []
    negozi_esistenti = sorted(df_lista["Negozio"].dropna().unique()) if not df_lista.empty else []

    # ➕ Form per aggiungere prodotto
    with st.form("Aggiungi prodotto"):
        prodotto = st.selectbox("Prodotto (scegli o scrivi)", prodotti_esistenti, index=0 if prodotti_esistenti else None, placeholder="Scrivi o scegli", key="prodotto_select")
        prodotto_custom = st.text_input("...oppure inserisci nuovo prodotto", key="prodotto_input")
        prodotto_finale = prodotto_custom if prodotto_custom else prodotto

        quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
        unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])
        costo_input = st.text_input("Costo (€)", placeholder="es. 4,50")
        data_acquisto = st.text_input("Data (mm-aaaa)", placeholder="es. 05-2025")

        negozio = st.selectbox("Negozio (scegli o scrivi)", negozi_esistenti, index=0 if negozi_esistenti else None, placeholder="Scrivi o scegli", key="negozio_select")
        negozio_custom = st.text_input("...oppure inserisci nuovo negozio", key="negozio_input")
        negozio_finale = negozio_custom if negozio_custom else negozio

        submitted = st.form_submit_button("➕ Aggiungi")

        if submitted and prodotto_finale:
            costo = costo_input.replace(",", ".").strip()
            nuovo_elemento = {
                "✔️ Elimina": False,
                "Prodotto": prodotto_finale,
                "Quantità": quantita,
                "Unità": unita,
                "Costo (€)": costo,
                "Data": data_acquisto,
                "Negozio": negozio_finale,
                "Acquistato": False
            }
            df_lista = pd.concat([df_lista, pd.DataFrame([nuovo_elemento])], ignore_index=True)
            salva_lista(df_lista)
            st.success("✅ Prodotto aggiunto!")
            st.rerun()

    # 📋 Tabella modificabile
    if not df_lista.empty:
        st.subheader("📋 Lista Attuale")

        df_modificato = st.data_editor(
            df_lista,
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

        if not df_modificato.equals(df_lista):
            salva_lista(df_modificato)
            st.success("💾 Modifiche salvate!")
            st.rerun()

        if df_modificato["✔️ Elimina"].any():
            if st.button("🗑️ Rimuovi selezionati"):
                df_modificato = df_modificato[~df_modificato["✔️ Elimina"]]
                salva_lista(df_modificato)
                st.success("🗑️ Elementi eliminati")
                st.rerun()
    else:
        st.info("La lista è vuota. Aggiungi un prodotto.")
