import streamlit as st

# Utenti autorizzati
utenti = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb",
    "admin": "adminpass"
}

st.title("🛒 Lista della spesa con login")

# Inizializza stato sessione
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "liste_utente" not in st.session_state:
    st.session_state.liste_utente = {}

# BLOCCO LOGIN
if not st.session_state.logged_in:
    username = st.text_input("👤 Nome utente")
    password = st.text_input("🔑 Password", type="password")

    if st.button("Accedi"):
        if utenti.get(username) == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Benvenuto, {username}!")
            st.experimental_rerun()
        else:
            st.error("Credenziali errate.")
else:
    # BLOCCO LOGOUT
    st.sidebar.success(f"Sei loggato come {st.session_state.username}")
    if st.sidebar.button("🔓 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.experimental_rerun()

    # BLOCCO LISTA SPESA
    st.header("📋 Lista della spesa personale")

    user = st.session_state.username
    if user not in st.session_state.liste_utente:
        st.session_state.liste_utente[user] = []

    lista = st.session_state.liste_utente[user]

    nuovo = st.text_input("Aggiungi un elemento")
    if st.button("➕ Aggiungi"):
        if nuovo:
            lista.append(nuovo)
            st.success(f"{nuovo} aggiunto!")

    if lista:
        st.subheader("📝 Lista attuale:")
        for i, el in enumerate(lista, 1):
            st.write(f"{i}. {el}")
    else:
        st.info("La lista è vuota.")

    da_rimuovere = st.selectbox("❌ Rimuovi un elemento", [""] + lista)
    if st.button("🗑️ Rimuovi"):
        if da_rimuovere in lista:
            lista.remove(da_rimuovere)
            st.success(f"{da_rimuovere} rimosso!")
