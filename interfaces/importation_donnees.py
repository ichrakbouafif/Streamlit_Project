import streamlit as st

def show():
    st.title("Importation des Données")
    st.write("Veuillez importer les fichiers nécessaires :")
    bilan = st.file_uploader("Importer le bilan", type=["csv", "xlsx"])
    corep = st.file_uploader("Importer le COREP", type=["csv", "xlsx"])
    capital = st.file_uploader("Importer le Capital Planning", type=["csv", "xlsx"])
    if bilan and corep and capital:
        st.success("Tous les fichiers ont été importés avec succès.")
    
    if st.button("Suivant"):
        # Navigate to the "Calcul des Ratios Baseline" page
        st.session_state.selected_page = "Calcul des Ratios Baseline"
