import streamlit as st

# Dizionario utenti (username: password)
utenti = {
    "fabrizio": "fabridig",
    "vittoria": "vitbarb",
    "admin": "adminpass"
}

# Login
st.title("🔒 Login")
username = st.text_input("Nome utente")
password = st.text_input("Password", type="password")

# Se credenziali corrette
if st.button("Accedi"):
    if utenti.get(username) == password:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.success(f"Benvenuto, {username}!")
    else:
        st.error("Credenziali errate.")

# Se già loggato, mostra il contenuto dell'app
if st.session_state.get("logged_in"):
    st.markdown("---")
    st.subheader(f"Ciao {st.session_state['username']}! Ecco la tua lista della spesa:")

if st.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.experimental_rerun()


    # Lista iniziale
    if "lista" not in st.session_state:
        st.session_state.lista = []

    # Aggiunta
    item = st.text_input("Aggiungi un elemento:")
    if st.button("Aggiungi"):
        if item:
            st.session_state.lista.append(item)
            st.success(f"{item} aggiunto!")
        else:
            st.warning("Inserisci qualcosa!")

    # Mostra lista
    st.subheader("📋 Lista attuale:")
    if st.session_state.lista:
        for i, el in enumerate(st.session_state.lista, start=1):
            st.write(f"{i}. {el}")
    else:
        st.info("La lista è vuota.")

    # Rimozione
    st.subheader("❌ Rimuovi un elemento:")
    da_rimuovere = st.selectbox("Scegli cosa vuoi rimuovere", [""] + st.session_state.lista)
    if st.button("Rimuovi"):
        if da_rimuovere in st.session_state.lista:
            st.session_state.lista.remove(da_rimuovere)
            st.success(f"{da_rimuovere} rimosso!")
