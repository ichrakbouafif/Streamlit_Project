import streamlit as st

def show():
    st.title("Résultats et Graphiques")
    st.write("Visualisez les résultats du test de stress et les graphiques comparatifs.")
    if st.button("Générer les graphiques"):
        st.success("Graphiques générés avec succès.")
