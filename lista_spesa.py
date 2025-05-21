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
        df = pd.DataFrame(dati)
        
        # Converti correttamente la colonna del costo se presente
        if "Costo (€)" in df.columns:
            # Assicurati che i costi siano interpretati come numeri con punto decimale
            df["Costo (€)"] = df["Costo (€)"].apply(
                lambda x: float(str(x).replace(",", ".")) if pd.notna(x) else 0.0
            )
        
        # Assicurati che la colonna Acquistato sia interpretata come booleana
        if "Acquistato" in df.columns:
            df["Acquistato"] = df["Acquistato"].apply(
                lambda x: True if str(x).upper() == "TRUE" else False
            )
            
        # Assicurati che la colonna ✔️ Elimina sia interpretata come booleana
        if "✔️ Elimina" in df.columns:
            df["✔️ Elimina"] = df["✔️ Elimina"].apply(
                lambda x: True if str(x).upper() == "TRUE" else False
            )
            
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento dati: {e}")
        return pd.DataFrame()

def salva_lista(df, msg_container=None):
    if msg_container:
        msg_container.info("💾 Sto salvando, attendi...")
    
    # Crea una copia del dataframe per evitare modifiche all'originale
    df_da_salvare = df.copy()
    
    # Assicurati che il costo sia formattato correttamente per il salvataggio
    if "Costo (€)" in df_da_salvare.columns:
        df_da_salvare["Costo (€)"] = df_da_salvare["Costo (€)"].apply(
            lambda x: f"{float(x):.2f}" if pd.notna(x) else "0.00"
        )
    
    # Assicurati che i valori booleani siano convertiti in stringhe "TRUE"/"FALSE" per Google Sheets
    if "Acquistato" in df_da_salvare.columns:
        df_da_salvare["Acquistato"] = df_da_salvare["Acquistato"].apply(
            lambda x: "TRUE" if x else "FALSE"
        )
    
    if "✔️ Elimina" in df_da_salvare.columns:
        df_da_salvare["✔️ Elimina"] = df_da_salvare["✔️ Elimina"].apply(
            lambda x: "TRUE" if x else "FALSE"
        )
    
    sheet.clear()
    sheet.update([df_da_salvare.columns.values.tolist()] + df_da_salvare.values.tolist())
    if msg_container:
        msg_container.success("✅ Operazione completata!")

# --- Session State ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# Per evitare loop di salvataggio
if "last_save_hash" not in st.session_state:
    st.session_state.last_save_hash = None

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

    # --- Estrai valori unici ---
    prodotti_esistenti = sorted(df_lista["Prodotto"].dropna().unique()) if "Prodotto" in df_lista else []
    negozi_esistenti = sorted(df_lista["Negozio"].dropna().unique()) if "Negozio" in df_lista else []
    mesi_esistenti = sorted(df_lista["Data"].dropna().unique()) if "Data" in df_lista else []

    # --- Aggiunta prodotto ---
    with st.form("Aggiungi prodotto"):
        prodotto_scelto = st.selectbox("Prodotto", options=[""] + prodotti_esistenti)
        nuovo_prodotto = st.text_input("Nuovo prodotto")
        prodotto = nuovo_prodotto.strip() if nuovo_prodotto.strip() else prodotto_scelto

        quantita = st.number_input("Quantità", min_value=0.0, step=1.0)
        unita = st.selectbox("Unità di misura", ["pz", "kg", "gr", "lt", "ml"])

        costo_input = st.text_input("Costo (€)", value="0,00")
        try:
            # Correzione per gestire correttamente i costi con virgola
            costo = float(costo_input.replace(",", "."))
        except ValueError:
            st.warning("❌ Inserisci un costo valido (es. 3,50)")
            costo = 0.0

        data_scelta = st.selectbox("Data (mm-aaaa)", options=[""] + mesi_esistenti)
        nuova_data = st.text_input("Nuova data (mm-aaaa)")
        data = nuova_data.strip() if nuova_data.strip() else data_scelta

        negozio_scelto = st.selectbox("Negozio", options=[""] + negozi_esistenti)
        nuovo_negozio = st.text_input("Nuovo negozio")
        negozio = nuovo_negozio.strip() if nuovo_negozio.strip() else negozio_scelto

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

    # --- Filtri ---
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
                "Costo (€)": st.column_config.NumberColumn(format="%.2f", step=0.01),
                "Data": st.column_config.TextColumn(help="Formato mm-aaaa"),
                "Negozio": st.column_config.TextColumn(),
                "Acquistato": st.column_config.CheckboxColumn(default=False)
            },
            hide_index=True,
            key="data_editor"
        )

        # Calcola un hash dei dati per evitare loop di salvataggio
        current_hash = hash(str(df_modificato.values.tolist()))
        
        # --- Gestione delle modifiche e rimozioni ---
        eliminazioni_selezionate = df_modificato["✔️ Elimina"].any()
        modifiche_rilevate = not df_modificato.equals(df_filtrato)
        
        # Gestisci prima le eliminazioni
        if eliminazioni_selezionate:
            if st.button("🗑️ Rimuovi selezionati"):
                # Trova le righe da eliminare
                indici_da_eliminare = []
                
                for i in range(len(df_modificato)):
                    if df_modificato.iloc[i]["✔️ Elimina"]:
                        riga_da_eliminare = df_filtrato.iloc[i]
                        
                        # Trova l'indice corrispondente nel dataframe completo
                        for idx in df_lista.index:
                            riga_lista = df_lista.loc[idx]
                            if (riga_da_eliminare["Prodotto"] == riga_lista["Prodotto"] and 
                                riga_da_eliminare["Data"] == riga_lista["Data"] and 
                                riga_da_eliminare["Negozio"] == riga_lista["Negozio"] and
                                riga_da_eliminare["Quantità"] == riga_lista["Quantità"]):
                                indici_da_eliminare.append(idx)
                                break
                
                if indici_da_eliminare:
                    df_lista = df_lista.drop(indici_da_eliminare).reset_index(drop=True)
                    msg = st.empty()
                    salva_lista(df_lista, msg)
                    st.session_state.last_save_hash = None  # Reset hash per permettere prossimi salvataggi
                    st.rerun()
        
        # Gestisci le modifiche solo se non ci sono eliminazioni selezionate
        elif modifiche_rilevate and current_hash != st.session_state.last_save_hash:
            # Trova e applica le modifiche
            df_aggiornato = df_lista.copy()
            modifiche_applicate = False
            
            for i in range(len(df_modificato)):
                riga_modificata = df_modificato.iloc[i]
                riga_originale = df_filtrato.iloc[i]
                
                # Verifica se la riga è stata effettivamente modificata
                if not riga_modificata.equals(riga_originale):
                    # Trova la riga corrispondente nel dataframe completo
                    for idx in df_lista.index:
                        riga_lista = df_lista.loc[idx]
                        if (riga_originale["Prodotto"] == riga_lista["Prodotto"] and 
                            riga_originale["Data"] == riga_lista["Data"] and 
                            riga_originale["Negozio"] == riga_lista["Negozio"] and
                            riga_originale["Quantità"] == riga_lista["Quantità"]):
                            
                            # Aggiorna solo i campi che sono effettivamente cambiati
                            for col in df_modificato.columns:
                                if riga_modificata[col] != riga_originale[col]:
                                    df_aggiornato.loc[idx, col] = riga_modificata[col]
                            
                            modifiche_applicate = True
                            break
            
            if modifiche_applicate:
                df_lista = df_aggiornato.copy()
                msg = st.empty()
                salva_lista(df_lista, msg)
                st.session_state.last_save_hash = current_hash
                st.rerun()

    else:
        st.info("La lista è vuota o nessun risultato corrisponde ai filtri.")
