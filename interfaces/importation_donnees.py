import streamlit as st

def show():
    st.title("Importation des Données")
    st.write("Veuillez importer les fichiers nécessaires :")
    bilan = st.file_uploader("Importer le bilan", type=["csv", "xlsx"])
    corep = st.file_uploader("Importer le COREP", type=["csv", "xlsx"])
    capital = st.file_uploader("Importer le Capital Planning", type=["csv", "xlsx"])
    if bilan and corep and capital:
        st.success("Tous les fichiers ont été importés avec succès.")
