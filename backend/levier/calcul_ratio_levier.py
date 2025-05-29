import pandas as pd
import os
import streamlit as st
import numpy as np
def recuperer_corep_levier_projete(resultats_levier: dict, annee: str) -> pd.DataFrame:
    """
    Récupère le tableau C47.00 projeté (levier) pour une année donnée.
    """
    donnees = resultats_levier.get(annee, {})
    return donnees.get("df_c4700", pd.DataFrame()).copy()
def appliquer_stress_montant_sur_c4700(df_c4700: pd.DataFrame, montant_stress: float, debug=False) -> pd.DataFrame:
    """
    Applique un stress monétaire à la ligne 190 ('Other assets') du tableau C47.00.
    Le montant est ajouté à la colonne '0010' de cette ligne.
    """
    df_modifie = df_c4700.copy()
    idx = df_modifie[df_modifie["Row"] == 190].index

    if not idx.empty:
        df_modifie.loc[idx[0], "0010"] += montant_stress
    else:
        new_row = pd.DataFrame([{"Row": 190, "0010": montant_stress}])
        df_modifie = pd.concat([df_modifie, new_row], ignore_index=True)

    if debug:
        st.write("📌 Stress appliqué à la ligne 190 (Other assets)")
        st.write(df_modifie[df_modifie["Row"] == 190])

    return df_modifie
def calcul_total_exposure(df_c4700: pd.DataFrame) -> tuple:
    """
    Calcule l'exposition totale pour le ratio de levier à partir du tableau C47.00 modifié.
    """
    rows_a_inclure = [
        10, 20, 30, 40, 50, 61, 65, 71, 81, 91, 92, 93,
        101, 102, 103, 104, 110, 120, 130, 140, 150, 160, 170, 180,
        181, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 196,
        197, 198, 200, 210, 220, 230, 235, 240, 250, 251, 252, 253,
        254, 255, 256, 257, 260, 261, 262, 263, 264, 265, 266, 267, 270
    ]

    df_temp = df_c4700.copy()

    total_exposure = (
        df_temp[df_temp["Row"].isin(rows_a_inclure)]
        .apply(lambda row: somme_sans_nan(row, ["0010"]), axis=1)
        .sum()
    )

    return total_exposure, df_temp


def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(row.get(c, 0) for c in cols if pd.notna(row.get(c, 0)))
def executer_stress_event1_levier_pluriannuel(
    resultats_proj: dict,
    resultats_solva: dict,
    annee_debut: str,
    montant_stress_total: float,
    horizon: int,
    debug: bool = False
) -> dict:
    resultats_stress = {}
    montant_annuel = montant_stress_total / horizon

    df_c4700_base = resultats_proj.get(annee_debut, {}).get("df_c4700", pd.DataFrame()).copy()

    for i in range(horizon):
        annee = str(int(annee_debut) + i)
        donnees_solva = resultats_solva.get(annee, {})

        # Fonds propres
        fonds_propres = donnees_solva.get("fonds_propres", 0)
        if fonds_propres == 0:
            df_c01 = donnees_solva.get("df_c01", pd.DataFrame())
            if not df_c01.empty and "row" in df_c01.columns and "0010" in df_c01.columns:
                ligne_tier1 = df_c01[df_c01["row"] == 10.0]
                if not ligne_tier1.empty:
                    valeur = ligne_tier1["0010"].values[0]
                    fonds_propres = 0 if pd.isna(valeur) else float(valeur)

        if df_c4700_base.empty:
            st.warning(f"⚠️ Tableau C47.00 introuvable pour l'année {annee}")
            continue

        if debug:
            st.write(f"🔍 Année {annee}")
            st.write(f"➡️ Montant annuel : {montant_annuel:,.0f}")
            st.write(f"➡️ Fonds propres : {fonds_propres:,.0f}")

        # Appliquer le stress sur la version précédente
        df_c4700_stresse = appliquer_stress_montant_sur_c4700(df_c4700_base, montant_annuel, debug)

        # Recalcul de l’exposition totale
        total_exposure_stresse, df_c4700_final = calcul_total_exposure(df_c4700_stresse)

        ratio_levier_stresse = (fonds_propres / total_exposure_stresse) * 100 if total_exposure_stresse > 0 else 0

        # Stockage
        resultats_stress[annee] = {
            "df_c4700_stresse": df_c4700_final,
            "total_exposure_stresse": total_exposure_stresse,
            "tier1": fonds_propres,
            "ratio_levier_stresse": round(ratio_levier_stresse, 2)
        }

        # ⏭️ Propagation à l’année suivante
        df_c4700_base = df_c4700_stresse.copy()

    return resultats_stress