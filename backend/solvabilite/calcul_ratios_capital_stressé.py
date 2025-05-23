import streamlit as st
import pandas as pd 
import numpy as np
import os 
# === Chargement des données ===
def charger_donnees():
    dossier = "data"
    bilan_path = os.path.join(dossier, "bilan.xlsx")
    corep_path = os.path.join(dossier, "solvabilite.xlsx")

    # === BILAN ===
    bilan = pd.read_excel(bilan_path)
    bilan = bilan.iloc[2:].reset_index(drop=True)
    if "Unnamed: 1" in bilan.columns:
        bilan = bilan.drop(columns=["Unnamed: 1"])
    for i, col in enumerate(bilan.columns):
        if str(col).startswith("Unnamed: 6"):
            bilan = bilan.iloc[:, :i]
            break
    bilan.columns.values[0] = "Poste du Bilan"
    bilan.columns.values[1] = "2024"
    bilan.columns.values[2] = "2025"
    bilan.columns.values[3] = "2026"
    bilan.columns.values[4] = "2027"
    bilan = bilan.dropna(how="all").reset_index(drop=True)
    if 25 in bilan.index:
        bilan = bilan.drop(index=25).reset_index(drop=True)

    # === C01 ===
    df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
    if "Unnamed: 2" in df_c01.columns:
        df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
    df_c01 = df_c01[["row", "0010"]] if "row" in df_c01.columns and "0010" in df_c01.columns else df_c01
    df_c01 = df_c01.reset_index(drop=True)

    # === C02 ===
    df_c02 = pd.read_excel(corep_path, sheet_name="C0200", header=8)
    df_c02 = df_c02.drop(columns=["Unnamed: 0", "Unnamed: 1"], errors='ignore')
    if "Unnamed: 2" in df_c02.columns:
        df_c02 = df_c02.rename(columns={"Unnamed: 2": "row"})
    if "Unnamed: 4" in df_c02.columns:
        df_c02 = df_c02.drop(columns=["Unnamed: 4"])
    df_c02 = df_c02[["row", "0010"]] if "row" in df_c02.columns and "0010" in df_c02.columns else df_c02
    df_c02.reset_index(drop=True, inplace=True)

    # === BLOC INSTITUTIONNEL (C0700_0007_1) ===
    df_raw_bloc = pd.read_excel(corep_path, sheet_name="C0700_0007_1", header=12)
    df_bloc = df_raw_bloc.iloc[8:15].copy()
    colonnes_depart = df_raw_bloc.columns.get_loc("Unnamed: 2")
    df_bloc = df_bloc.iloc[:, colonnes_depart:]
    df_bloc.rename(columns={"Unnamed: 2": "row"}, inplace=True)
    df_bloc = df_bloc.drop(index=8).reset_index(drop=True)

    return bilan, df_c01, df_c02, df_bloc


def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(row.get(c, 0) for c in cols if pd.notna(row.get(c, 0)))


def recuperer_corep_bloc_institutionnel(resultats, annee: str):
    """
    Récupère uniquement le bloc institutionnel (C0700_0007_1) pour une année donnée.

    Args:
        resultats (dict): Résultats issus de simuler_solvabilite_pluriannuelle()
        annee (str): Année cible au format '2025', '2026', ...

    Returns:
        DataFrame: Le DataFrame du bloc institutionnel (C0700_0007_1)
    """
    if annee not in resultats:
        st.error(f"❌ Année {annee} non trouvée dans les résultats simulés.")
        return pd.DataFrame()

    data = resultats[annee]
    blocs = data.get("blocs_rwa", {})

    return blocs.get("C0700_0007_1", pd.DataFrame())

    return corep


def calculer_0220(row, ratios, debug=False):
    """Calcule la colonne 0220 (RWA) avec les ratios déjà calculés"""
    row_type = row.get("row")
    expo = row.get("0200", 0)
    
    # Si l'exposition est nulle ou NaN, on la met à 0
    if pd.isna(expo):
        expo = 0
    
    # Utilisation des ratios pré-calculés
    if row_type in [70.0, 80.0, 110.0]:
        ratio = ratios.get(row_type)  # Utiliser le ratio de transformation déjà calculé
        rwa = expo * ratio
        if debug:
            st.write(f"RWA calculé pour ligne {row_type}: {rwa}")
        return rwa
    
    # Pour les autres lignes, somme de 0215, 0216, 0217 si disponibles
    sum_cols = 0
    for k in ["0215", "0216", "0217"]:
        if k in row and not pd.isna(row.get(k)):
            sum_cols += row.get(k)
    
    if debug and row_type in [70.0, 80.0, 110.0]:
        st.write(f"RWA calculé pour ligne {row_type}: {sum_cols}")
    
    return sum_cols

def calculer_0040(row):
    return somme_sans_nan(row, ["0010", "0030"])

def calculer_0110(row):
    return somme_sans_nan(row, ["0040", "0050", "0060", "0070", "0080", "0090", "0100"])

def calculer_0150(row):
    return somme_sans_nan(row, ["0110", "0120", "0130"])


def calculer_rwa_depuis_exposition(expo, row_type, ratios, debug=False):
    """Calcule le RWA (0220) à partir de l'exposition (0200) et du ratio implicite"""
    if pd.isna(expo) or expo == 0:
        return 0
   
    ratio = ratios.get(row_type, 0.25)
    rwa = expo * ratio
   
    if debug:
        st.write(f"Calcul RWA pour ligne {row_type}:")
        st.write(f"  - Exposition: {expo}")
        st.write(f"  - Ratio: {ratio}")
        st.write(f"  - RWA calculé: {rwa}")
   
    return rwa

def calculer_0200(row, debug=False):
    """
    Calcule la colonne 0200 en fonction des pondérations et avec relation entre 0010 et 0190.
    Pour la ligne 070, 0200 est égal à 0150. Pour la ligne 80.0, le calcul basé sur 0170, 0180 et 0190 est appliqué.
    """
    if row.get("row") == 70.0:  # Pour la ligne 70.0, 0200 = 0150
        return row.get("0150", 0)

    if row.get("row") == 110.0:  # Pour la ligne 110.0, ne pas recalculer 0200
        return row.get("0200", 0)

    # Récupérer les valeurs de 0170, 0180, 0190 avec gestion des NaN
    v170 = row.get("0170", 0)
    v180 = row.get("0180", 0)
    v190 = row.get("0190", 0)
   
    v170 = 0 if pd.isna(v170) else v170
    v180 = 0 if pd.isna(v180) else v180
    v190 = 0 if pd.isna(v190) else v190

    v010 = row.get("0010", 0)
    v010 = 0 if pd.isna(v010) else v010
   
   

    # Calculer 0200 selon la pondération
    result = (0.2 * v170) + (0.5 * v180) + (1.0 * v190)

   

    return result


def calculer_ratios_transformation(df_ref, debug=False):
    """
    Calcule les ratios implicites (RWA/exposition) pour chaque type de ligne à partir des données de référence.
    Ces ratios seront utilisés pour les calculs futurs.
    """
    ratios = {}
    
    for row_type, name in [(70.0, "on_balance"), (80.0, "off_balance"), (110.0, "derivatives")]:
        ligne = df_ref[df_ref["row"] == row_type]
        
        if not ligne.empty:
            # Récupération de l'exposition (0200) et du RWA (0215 ou 0220)
            rwa_col = "0215" if "0215" in ligne.columns else "0220"
            
            rwa = ligne[rwa_col].values[0] if not pd.isna(ligne[rwa_col].values[0]) else 0
            expo = ligne["0200"].values[0] if "0200" in ligne.columns and not pd.isna(ligne["0200"].values[0]) else 0
            
            # Calcul du ratio RWA/exposition
            if expo != 0:
                ratio = round(rwa / expo, 4)
            else:
                ratio = 0.25  # Valeur par défaut si exposition = 0
                
            ratios[row_type] = ratio
            
            if debug:
                st.write(f"Ratio calculé pour ligne {row_type} ({name}): {ratio}")
                st.write(f"  - RWA: {rwa}, Exposition: {expo}")
        else:
            ratios[row_type] = 0.25  # Valeur par défaut si ligne non trouvée
            if debug:
                st.warning(f"Ligne {row_type} ({name}) non trouvée, utilisation ratio par défaut 0.25")
    
    return ratios
def calculer_0040(row):
    return somme_sans_nan(row, ["0010", "0030"])

def calculer_0110(row):
    return somme_sans_nan(row, ["0040", "0050", "0060", "0070", "0080", "0090", "0100"])

def calculer_0150(row):
    return somme_sans_nan(row, ["0110", "0120", "0130"])


def calculer_rwa_depuis_exposition(expo, row_type, ratios, debug=False):
    """Calcule le RWA (0220) à partir de l'exposition (0200) et du ratio implicite"""
    if pd.isna(expo) or expo == 0:
        return 0
   
    ratio = ratios.get(row_type, 0.25)
    rwa = expo * ratio
   
    if debug:
        st.write(f"Calcul RWA pour ligne {row_type}:")
        st.write(f"  - Exposition: {expo}")
        st.write(f"  - Ratio: {ratio}")
        st.write(f"  - RWA calculé: {rwa}")
   
    return rwa
def construire_df_c0700_recalcule(df_bloc, debug=False):
    """
    Recalcule toutes les colonnes du bloc C0700 après injection du capital planning
    avec propagation de 0010 vers 0190 et 0200
    """
    if debug:
        st.write("### RECALCUL DU BLOC C0700 AVEC PROPAGATION AMÉLIORÉE")
       
    df_simulee = df_bloc.copy()
   
    # S'assurer que toutes les colonnes nécessaires existent
    colonnes_requises = ["row", "0010", "0040", "0110", "0150", "0170", "0180", "0190", "0200", "0215", "0220"]
    for col in colonnes_requises:
        if col not in df_simulee.columns:
            df_simulee[col] = np.nan
            if debug:
                st.write(f"Colonne {col} ajoutée (manquante)")
   
    # Calculer les ratios une seule fois pour tout le bloc
    ratios = calculer_ratios_transformation(df_bloc, debug)
   
    if debug:
        st.write(f"Ratios de transformation calculés: {ratios}")
   
    # Recalculer ligne par ligne
    for idx, row in df_simulee.iterrows():
        row_copy = row.copy()
        row_type = row_copy["row"]
       
        if debug:
            st.write(f"\nRecalcul ligne {row_type}:")
       
        # Calcul des colonnes intermédiaires
        row_copy["0040"] = calculer_0040(row_copy)
        row_copy["0110"] = calculer_0110(row_copy)
        row_copy["0150"] = calculer_0150(row_copy)
       
        # Pour toutes les lignes, utiliser la nouvelle logique de calcul 0200
        old_0200 = row_copy.get("0200", 0)
        old_0200 = 0 if pd.isna(old_0200) else old_0200
       
        # Propager 0010 vers 0190 si nécessaire
        if row_type == 70.0:  # Pour les actifs du bilan (on-balance)
            v010 = row_copy.get("0010", 0)
            v010 = 0 if pd.isna(v010) else v010
           
            v190 = row_copy.get("0190", 0)
            v190 = 0 if pd.isna(v190) else v190
           
            # Si 0190 est vide ou 0 mais 0010 existe, mettre à jour 0190
            if (v190 == 0) and (v010 > 0):
                row_copy["0190"] = v010
                if debug:
                    st.write(f"  Mise à jour 0190 depuis 0010: {v010}")
       
        # Recalculer 0200 avec la nouvelle fonction
        row_copy["0200"] = calculer_0200(row_copy, debug)
       
        # Calculer 0220 (RWA) en dernier
        old_0220 = row_copy.get("0220", 0)
        old_0220 = 0 if pd.isna(old_0220) else old_0220
       
        row_copy["0220"] = calculer_0220(row_copy, ratios, debug)
       
        # Définir 0215 égal à 0220 (dans ce modèle)
        row_copy["0215"] = row_copy["0220"]
       
        if debug:
            st.write(f"  Résultats ligne {row_type}:")
            st.write(f"  - 0010: {row_copy.get('0010', 0)}")
            st.write(f"  - 0190: {row_copy.get('0190', 0)}")
            st.write(f"  - 0200: {old_0200} → {row_copy['0200']}")
            st.write(f"  - 0220: {old_0220} → {row_copy['0220']}")
       
        # Mettre à jour les valeurs dans le dataframe
        for col in colonnes_requises:
            if col in row_copy and not pd.isna(row_copy.get(col)):
                df_simulee.at[idx, col] = row_copy.get(col)
   
    return df_simulee
def appliquer_stress_montant_sur_bloc(df_bloc, montant_stress, debug=False):
    """
    Applique un stress (soustraction de montant) sur la ligne 70.0 du bloc C0700.
    Contrairement au capital planning, ce stress est négatif : on retire une valeur de 0010.
    La fonction recalcule ensuite toutes les colonnes via construire_df_c0700_recalcule().

    Args:
        df_bloc (DataFrame): Bloc C0700 à modifier (ex: C0700_0007_1)
        montant_stress (float): Montant à retirer de la ligne 70.0 (positif)
        debug (bool): Active l'affichage des étapes

    Returns:
        DataFrame: bloc recalculé après stress
    """
    
    df_new = df_bloc.copy()
    idx = df_new[df_new["row"] == 70.0].index

    if not idx.empty:
        ancienne_valeur = df_new.at[idx[0], "0010"]
        ancienne_valeur = 0 if pd.isna(ancienne_valeur) else ancienne_valeur

        nouvelle_valeur = max(0, ancienne_valeur - montant_stress)
        df_new.at[idx[0], "0010"] = nouvelle_valeur

        if debug:
            st.write(f"Ligne 70.0 : {ancienne_valeur:,.2f} - {montant_stress:,.2f} = {nouvelle_valeur:,.2f}")
    else:
        st.error("❌ Ligne 70.0 introuvable dans le bloc C0700")
        raise ValueError("Ligne 70.0 introuvable")

    # Recalcul complet du bloc après stress
    df_recalcule = construire_df_c0700_recalcule(df_new, debug)

    return df_recalcule

def executer_stress_event1_bloc_institutionnel_pluriannuel(
    resultats_proj: dict,
    annee_debut: str,
    montant_stress_total: float,
    horizon: int,
    debug: bool = False
) -> dict:
    """
    Applique le stress de type 'retrait massif des dépôts' sur plusieurs années
    en répartissant le montant total uniformément sur l’horizon défini.

    Returns:
        dict: Résultats par année : blocs stressés, RWA, ratio de solvabilité.
    """
    resultats_stress = {}
    montant_annuel = montant_stress_total / horizon

    for i in range(horizon):
        annee = str(int(annee_debut) + i)
        donnees = resultats_proj.get(annee, {})
        df_c01 = donnees.get("df_c01", pd.DataFrame())
        df_bloc = recuperer_corep_bloc_institutionnel(resultats_proj, annee).copy()

        rwa_total_projete = donnees.get("rwa", 0)

        if df_bloc.empty:
            st.warning(f"⚠️ Bloc C0700_0007_1 introuvable pour {annee}")
            continue

        if debug:
            st.write(f"\n🧪 Traitement de l'année {annee}")
            st.write(f"Montant annuel de stress: {montant_annuel:,.0f} DZD")

        # RWA initial
        rwa_initial = df_bloc["0220"].fillna(0).sum()

        # Appliquer le stress
        from backend.solvabilite.calcul_ratios_capital_stressé import appliquer_stress_montant_sur_bloc
        df_bloc_stresse = appliquer_stress_montant_sur_bloc(df_bloc, montant_annuel, debug=debug)

        # RWA après stress
        rwa_stresse = df_bloc_stresse["0220"].fillna(0).sum()
        delta_rwa = rwa_stresse - rwa_initial
        rwa_total_stresse = rwa_total_projete + delta_rwa

        # Fonds propres projetés (Tier 1)
        fonds_propres = 0
        if not df_c01.empty and "0100" in df_c01.columns:
            ligne_tier1 = df_c01[df_c01["row"] == 10.0]
            if not ligne_tier1.empty:
                fonds_propres = ligne_tier1["0100"].values[0]
                fonds_propres = 0 if pd.isna(fonds_propres) else fonds_propres

        # Ratio stressé
        ratio_solva_stresse = (fonds_propres / rwa_total_stresse) * 100 if rwa_total_stresse > 0 else 0

        resultats_stress[annee] = {
            "df_bloc_stresse": df_bloc_stresse,
            "rwa_total_stresse": rwa_total_stresse,
            "delta_rwa_total": delta_rwa,
            "ratio_solva_stresse": round(ratio_solva_stresse, 2),
            "fonds_propres": fonds_propres
        }

    return resultats_stress
