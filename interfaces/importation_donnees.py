import streamlit as st
import os

def save_uploaded_file(uploaded_file, folder, filename):
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getvalue())
    return file_path

def show():
    st.title("Importation des Données")
    st.write("Veuillez importer les fichiers nécessaires :")

    data_folder = "data"

    # Importer le bilan
    st.subheader("Importer le Bilan")
    bilan = st.file_uploader("Choisissez un fichier Bilan :", type=["csv", "xlsx"], key="bilan_uploader")
    if bilan is not None:
        bilan_path = save_uploaded_file(bilan, data_folder, "bilan.xlsx")
        st.success(f"Fichier 'Bilan' enregistré avec succès")

    # Importer les fichiers COREP
    st.subheader("Importer les fichiers COREP")
    corep_files = st.file_uploader(
        "Choisissez les fichiers COREP :", 
        type=["csv", "xlsx"], 
        key="corep_uploader", 
        accept_multiple_files=True
    )
    
    expected_files = {"lcr": False, "nsfr": False, "solvabilite": False, "levier": False}

    if corep_files:
        for uploaded_file in corep_files:
            file_name = uploaded_file.name.lower()

            if "lcr" in file_name:
                save_uploaded_file(uploaded_file, data_folder, "LCR.csv")
                expected_files["lcr"] = True
                st.success("Fichier 'LCR' enregistré avec succès")
            elif "nsfr" in file_name:
                save_uploaded_file(uploaded_file, data_folder, "NSFR.csv")
                expected_files["nsfr"] = True
                st.success("Fichier 'NSFR' enregistré avec succès")
            elif "solvabilite" in file_name or "solvabilité" in file_name:
                save_uploaded_file(uploaded_file, data_folder, "solvabilite.csv")
                expected_files["solvabilite"] = True
                st.success("Fichier 'Solvabilité' enregistré avec succès")
            elif "levier" in file_name:
                save_uploaded_file(uploaded_file, data_folder, "levier.csv")
                expected_files["levier"] = True
                st.success("Fichier 'Levier' enregistré avec succès")
            else:
                st.warning(f"Fichier non reconnu : {uploaded_file.name}")

    st.markdown("---")
    if st.button("Suivant"):
        st.session_state.selected_page = "Calcul des Ratios Baseline"
            

    # Bouton suivant
"""     if st.button("Suivant"):
        if bilan and all(expected_files.values()):
            st.session_state.selected_page = "Calcul des Ratios Basel   ine"
        else:
            st.error("Erreur : Veuillez importer tous les fichiers requis avant de continuer.") """

