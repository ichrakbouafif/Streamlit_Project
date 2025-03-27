import streamlit as st

def show():
    st.title("Choix du Scénario de Stress")
    st.write("Sélectionnez le scénario de stress à appliquer.")
    scenario = st.selectbox("Choisir un scénario", ["Scénario Macro", "Scénario Idio", "Scénario Combiné"])
    if st.button("Appliquer le scénario"):
        st.success(f"{scenario} appliqué avec succès.")
