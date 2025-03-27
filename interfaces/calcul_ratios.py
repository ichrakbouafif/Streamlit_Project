import streamlit as st

def show():
    st.title("Calcul des Ratios Baseline")
    st.write("Effectuez le calcul des ratios de référence (LCR, NSFR) et affichez les résultats.")
    if st.button("Calculer les ratios"):
        st.success("Ratios calculés avec succès.")
