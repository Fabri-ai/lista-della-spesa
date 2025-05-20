import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 🌐 Configurazione iniziale
st.set_page_config(page_title="🛒 Lista della Spesa Fab & Vik", layout="wide")

# 🔐 Login - utenti autorizzati
utenti_autorizzati = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb"
}

# 🔑 Google Sheets setup
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/18gm99X8PTlhz5J7RkNhoYbyPPQlZc1QkT-TM9YRvu-A"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

client = gspread.authorize(credentials)
spreadsheet = client.open_by_url(SPREADSHEET_URL)
sheet = spreadsheet.sheet1

# 📥 Carica lista
@st.cache_data(ttl=60)
def carica_lista():
    try:
        dati = sheet.get_all_records()
        return pd.DataFrame(dati)
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return pd.DataFrame()

# 💾 Salva lista
def salva_lista(df):
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# 🧠 Sessione
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# 🔐 Login
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

    # 🧩 Selezione da menu a tendina dinamico
    prodotti_unici = sorted(df_lista["Prodotto"].dropna().unique().tolist())
    negozi_unici = sorted(df_lista["Negozio"].dropna().unique().tolist())
    date_uniche = sorted(df_lista["Data"].dropna().unique().tolist())

    # ➕ Aggiungi prodotto
    with st.form("Aggiungi prodotto"):
        col1, col2 = st.columns([2, 1])
        with col1:
            prodotto = st.selectbox("Prodotto", prodotti_unici + ["🆕 Aggiungi nuovo"], index=0)
            if prodotto == "🆕 Aggiungi nuovo":
                prodotto = st.text_input("Nuovo prodotto")

        quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
        unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])

        costo_input = st.text_input("Costo (€)", placeholder="es. 4,50")

        data = st.selectbox("Data (mm-aaaa)", date_uniche + ["🆕 Aggiungi nuova"])
        if data == "🆕 Aggiungi nuova":
            data = st.text_input("Inserisci nuova data (mm-aaaa)")

        negozio = st.selectbox("Negozio", negozi_unici + ["🆕 Aggiungi nuovo"])
        if negozio == "🆕 Aggiungi nuovo":
            negozio = st.text_input("Nuovo negozio")

        submitted = st.form_submit_button("➕ Aggiungi")

        if submitted and prodotto:
            costo = costo_input.replace(",", ".").strip()
            nuovo = {
                "✔️ Elimina": False,
                "Prodotto": prodotto,
                "Quantità": quantita,
                "Unità": unita,
                "Costo (€)": costo,
                "Data": data,
                "Negozio": negozio,
                "Acquistato": False
            }
            df_lista = pd.concat([df_lista, pd.DataFrame([nuovo])], ignore_index=True)
            salva_lista(df_lista)
            st.success("✅ Prodotto aggiunto!")
            st.rerun()

    # 📊 Filtri multipli
    with st.expander("🔍 Filtri"):
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            filtro_data = st.multiselect("📆 Filtra per Data", date_uniche)
        with colf2:
            filtro_negozio = st.multiselect("🏪 Filtra per Negozio", negozi_unici)
        with colf3:
            filtro_prodotto = st.multiselect("🛍️ Filtra per Prodotto", prodotti_unici)

    df_filtrato = df_lista.copy()

    if filtro_data:
        df_filtrato = df_filtrato[df_filtrato["Data"].isin(filtro_data)]
    if filtro_negozio:
        df_filtrato = df_filtrato[df_filtrato["Negozio"].isin(filtro_negozio)]
    if filtro_prodotto:
        df_filtrato = df_filtrato[df_filtrato["Prodotto"].isin(filtro_prodotto)]

    # 📋 Tabella modificabile
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
                "Costo (€)": st.column_config.TextColumn(),
                "Data": st.column_config.TextColumn(help="Formato mm-aaaa"),
                "Negozio": st.column_config.TextColumn(),
                "Acquistato": st.column_config.CheckboxColumn()
            },
            hide_index=True
        )

        # 🔄 Salva modifiche
        if not df_modificato.equals(df_filtrato):
            # Unione con il dataframe originale mantenendo gli altri dati
            df_lista.update(df_modificato)
            salva_lista(df_lista)
            st.success("💾 Modifiche salvate!")
            st.rerun()

        # 🗑️ Elimina selezionati
        if df_modificato["✔️ Elimina"].any():
            if st.button("🗑️ Rimuovi selezionati"):
                df_lista = df_lista[~df_lista.index.isin(df_modificato[df_modificato["✔️ Elimina"]].index)]
                salva_lista(df_lista)
                st.success("🗑️ Elementi eliminati")
                st.rerun()
    else:
        st.info("Nessun elemento da mostrare con i filtri attuali.")
