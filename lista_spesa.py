import streamlit as st

# Inizializza la lista nella sessione
if "lista" not in st.session_state:
    st.session_state.lista = []

st.title("🛒 Lista della Spesa")

# Aggiunta elementi
item = st.text_input("Aggiungi un elemento alla lista:")
if st.button("Aggiungi"):
    if item:
        st.session_state.lista.append(item)
        st.success(f"{item} aggiunto!")
    else:
        st.warning("Inserisci qualcosa prima di cliccare!")

# Mostra la lista
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
    if da_rimuovere and da_rimuovere in st.session_state.lista:
        st.session_state.lista.remove(da_rimuovere)
        st.success(f"{da_rimuovere} rimosso!")
