import pandas as pd
import numpy as np
import streamlit as st
import os
# Mappings globaux
mapping_feuilles_rwa = {
    "Caisse Banque Centrale / nostro": ["C0700_0002_1"],
    "Créances banques autres": ["C0700_0007_1"],
    "Créances sur la clientèle (total)": ["C0700_0008_1", "C0700_0009_1"],
    "Immobilisations et Autres Actifs": ["C0700_0017_1"]
}

mapping_c0700_to_c0200 = {
    "C0700_0002_1": "0070",
    "C0700_0007_1": "0120",
    "C0700_0008_1": "0130",
    "C0700_0009_1": "0140",
    "C0700_0017_1": "0211"
}

mapping_bilan_to_c4700 = {
    "Caisse Banque Centrale / nostro": 190,
    "Créances banques autres": 190,
    "Créances sur la clientèle (total)": 190,
    "Immobilisations et Autres Actifs": 190
}

"""
Calcul du Ratio de Solvabilité avec Capital Planning - Version debuggée
"""

# === Configuration des mappings ===
mapping_feuilles_rwa = {
    "Caisse Banque Centrale / nostro": ["C0700_0002_1"],
    "Créances banques autres": ["C0700_0007_1"],
    "Créances sur la clientèle (total)": ["C0700_0008_1", "C0700_0009_1"],
   
    "Immobilisations et Autres Actifs": ["C0700_0017_1"]
}

mapping_c0700_to_c0200 = {
    "C0700_0002_1": "0070",
    "C0700_0007_1": "0120",
    "C0700_0008_1": "0130",
    "C0700_0009_1": "0140",
    "C0700_0016": "0210",
    "C0700_0017_1": "0211"
}
def charger_c4700(levier_path="data/levier.xlsx"):
    """
    Charge les données C4700 pour le calcul du ratio de levier
    """
    try:
        df_c4700 = pd.read_excel(levier_path, sheet_name="C4700", header=9)
        df_c4700 = df_c4700.iloc[:, 2:]
        colonnes_utiles = [col for col in df_c4700.columns if not col.startswith('Unnamed: 4')]
        df_c4700 = df_c4700[colonnes_utiles]
        if 'Unnamed: 5' in df_c4700.columns:
            df_c4700 = df_c4700.drop(columns=['Unnamed: 5'])
        df_c4700 = df_c4700.rename(columns={'Unnamed: 2': 'Row', 'Unnamed: 3': '0010'})
        df_c4700['Row'] = pd.to_numeric(df_c4700['Row'], errors='coerce')
        df_c4700['0010'] = pd.to_numeric(df_c4700['0010'], errors='coerce')
        return df_c4700
    except Exception as e:
        st.error(f"Erreur lors du chargement de C4700: {e}")
        return pd.DataFrame(columns=['Row', '0010'])

def charger_tier1(corep_path="data/solvabilite.xlsx"):
    """
    Charge les données Tier1 (CET1 + AT1) depuis C0100
    """
    try:
        df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
        if "Unnamed: 2" in df_c01.columns:
            df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
        df_c01 = df_c01[["row", "0010"]] if "row" in df_c01.columns and "0010" in df_c01.columns else df_c01
        return df_c01.reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur lecture C0100 pour Tier1: {e}")
        return pd.DataFrame(columns=['row', '0010'])
def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(0 if pd.isna(row.get(c, 0)) else row.get(c, 0) for c in cols)

def charger_donnees(corep_path="data/solvabilite.xlsx", debug=False):
    """
    Charge toutes les données nécessaires : bilan, C0100, C0200 et blocs C0700
    """
    import os
    dossier = "data"
    bilan_path = os.path.join(dossier, "bilan.xlsx")

    # === BILAN ===
    if not os.path.exists(bilan_path):
        st.error(f"Fichier de bilan non trouvé : {bilan_path}")
        return None, None, None, None

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

    if debug:
        st.write("### DEBUG: Aperçu du bilan chargé")
        st.dataframe(bilan.head())

    # === C0100 ===
    try:
        df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
        if "Unnamed: 2" in df_c01.columns:
            df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
        df_c01 = df_c01[["row", "0010"]] if "row" in df_c01.columns and "0010" in df_c01.columns else df_c01
        df_c01 = df_c01.reset_index(drop=True)
        df_c01["row"] = pd.to_numeric(df_c01["row"], errors='coerce')
        df_c01["0010"] = pd.to_numeric(df_c01["0010"], errors='coerce')
        if debug:
            st.write("### DEBUG: Aperçu C0100")
            st.dataframe(df_c01.head(20))
    except Exception as e:
        st.error(f"Erreur lecture C0100 : {e}")
        df_c01 = pd.DataFrame(columns=["row", "0010"])

    # === C0200 ===
    try:
        df_c02 = pd.read_excel(corep_path, sheet_name="C0200", header=8)
        df_c02 = df_c02.drop(columns=["Unnamed: 0", "Unnamed: 1"], errors='ignore')
        if "Unnamed: 2" in df_c02.columns:
            df_c02 = df_c02.rename(columns={"Unnamed: 2": "row"})
        if "Unnamed: 4" in df_c02.columns:
            df_c02 = df_c02.drop(columns=["Unnamed: 4"])
        df_c02 = df_c02[["row", "0010"]] if "row" in df_c02.columns and "0010" in df_c02.columns else df_c02
        df_c02["row"] = pd.to_numeric(df_c02["row"], errors='coerce')
        df_c02["0010"] = pd.to_numeric(df_c02["0010"], errors='coerce')
        df_c02.reset_index(drop=True, inplace=True)
        if debug:
            st.write("### DEBUG: Aperçu C0200")
            st.dataframe(df_c02.head(20))
    except Exception as e:
        st.error(f"Erreur lecture C0200 : {e}")
        df_c02 = pd.DataFrame(columns=["row", "0010"])

    # === BLOCS C0700 ===
    blocs_c0700 = {}
    for feuille in sum(mapping_feuilles_rwa.values(), []):
        try:
            if debug:
                st.write(f"### DEBUG: Chargement bloc {feuille}")
            df_raw_bloc = pd.read_excel(corep_path, sheet_name=feuille, header=12)
            df_bloc = df_raw_bloc.iloc[8:15].copy()
            colonnes_depart = df_raw_bloc.columns.get_loc("Unnamed: 2")
            df_bloc = df_bloc.iloc[:, colonnes_depart:]
            df_bloc.rename(columns={df_bloc.columns[0]: "row"}, inplace=True)
            if 8 in df_bloc.index:
                df_bloc = df_bloc.drop(index=8)
            for col in df_bloc.columns:
                if col != "row" and not pd.api.types.is_numeric_dtype(df_bloc[col]):
                    df_bloc[col] = pd.to_numeric(df_bloc[col], errors='coerce')
            df_bloc["row"] = pd.to_numeric(df_bloc["row"], errors='coerce')
            df_bloc.reset_index(drop=True, inplace=True)
            colonnes_requises = ["row", "0010", "0200", "0215", "0220"]
            for col in colonnes_requises:
                if col not in df_bloc.columns:
                    df_bloc[col] = np.nan
            blocs_c0700[feuille] = df_bloc
            if debug:
                st.write(f"Bloc {feuille} chargé avec succès")
                st.dataframe(df_bloc)
        except Exception as e:
            st.warning(f"Erreur chargement bloc {feuille} : {e}")
            blocs_c0700[feuille] = pd.DataFrame(columns=["row", "0010", "0200", "0215", "0220"])

    return bilan, df_c01, df_c02, blocs_c0700


def calculer_ratios_transformation(df, debug=False):
    """
    Calcule les ratios implicites (RWA/exposition) pour chaque type de ligne
    avec meilleure gestion des erreurs
    """
    ratios = {}
    for row_type, name in [(70.0, "on_balance"), (80.0, "off_balance"), (110.0, "derivatives")]:
        ligne = df[df["row"] == row_type]
       
        if not ligne.empty:
            # S'assurer que les colonnes nécessaires existent
            rwa_col = "0215" if "0215" in ligne.columns else "0220"
           
            rwa = ligne[rwa_col].values[0] if not pd.isna(ligne[rwa_col].values[0]) else 0
            expo = ligne["0200"].values[0] if "0200" in ligne.columns and not pd.isna(ligne["0200"].values[0]) else 0
           
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

def calculer_0200(row, debug=False):
    """
    Calcule la colonne 0200 en fonction des pondérations et avec relation entre 0010 et 0190
    La logique est la suivante:
    - Si les colonnes 0170/0180/0190 existent, les utiliser pour calculer 0200
    - Sinon, utiliser 0010 comme valeur pour 0190 (pondération 100%)
    """
    if row.get("row") == 110.0:  # Pour les dérivés, ne pas recalculer
        return row.get("0200", 0)
   
    # Récupérer les valeurs de 0170, 0180, 0190 avec gestion des NaN
    v170 = row.get("0170", 0)
    v180 = row.get("0180", 0)
    v190 = row.get("0190", 0)
   
    # Remplacer les NaN par 0
    v170 = 0 if pd.isna(v170) else v170
    v180 = 0 if pd.isna(v180) else v180
    v190 = 0 if pd.isna(v190) else v190
   
    # Si 0190 est vide ou 0 mais 0010 existe, utiliser 0010 pour 0190 (pondération 100%)
    v010 = row.get("0010", 0)
    v010 = 0 if pd.isna(v010) else v010
   
    # Si 0190 est vide ou 0 mais 0010 existe, prendre la valeur de 0010
    if (v190 == 0) and (v010 > 0):
        v190 = v010
       
    # Calculer 0200 selon la pondération
    result = (0.2 * v170) + (0.5 * v180) + (1.0 * v190)
   
    # Si toutes les valeurs sont 0 ou NaN et que 0010 existe, utiliser 0010 comme base
    if v170 == 0 and v180 == 0 and v190 == 0 and v010 > 0:
        result = v010
   
    # Cas de secours si aucune valeur disponible mais 0200 existe déjà
    if result == 0 and not pd.isna(row.get("0200", 0)) and row.get("0200", 0) > 0:
        return row.get("0200", 0)
   
    if debug:
        st.write(f"Calcul 0200 pour ligne {row.get('row')}:")
        st.write(f"  - 0010: {v010}")
        st.write(f"  - 0170 (0.2): {v170}")
        st.write(f"  - 0180 (0.5): {v180}")
        st.write(f"  - 0190 (1.0): {v190}")
        st.write(f"  - Résultat 0200: {result}")
   
    return result

def calculer_0220(row, ratios, debug=False):
    """Calcule la colonne 0220 (RWA) selon le type de ligne avec meilleure gestion des erreurs"""
    row_type = row.get("row")
    expo = row.get("0200", 0)
   
    # Gestion des NaN
    if pd.isna(expo):
        expo = 0
       
    # Pour les lignes principales, utiliser le ratio
    if row_type in [70.0, 80.0, 110.0]:
        return calculer_rwa_depuis_exposition(expo, row_type, ratios, debug)
   
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
def injecter_capital_planning_dans_bloc(df_bloc, capital_planning_value, debug=False):
    """
    Injecte le capital planning dans le bloc C0700 et recalcule avec la nouvelle logique
    """
    if capital_planning_value is None or pd.isna(capital_planning_value) or capital_planning_value == 0:
        return construire_df_c0700_recalcule(df_bloc, debug)

    df_new = df_bloc.copy()
    idx = df_new[df_new["row"] == 70.0].index

    if not idx.empty:
        # Ancienne valeur peut être NaN, gérer ce cas
        ancienne_valeur = df_new.at[idx[0], "0010"]
        ancienne_valeur = 0 if pd.isna(ancienne_valeur) else ancienne_valeur
       
        df_new.at[idx[0], "0010"] = ancienne_valeur + capital_planning_value
       
        if debug:
            st.write(f"Capital planning injecté: {capital_planning_value}")
            st.write(f"Nouvelle valeur 0010: {df_new.at[idx[0], '0010']}")
    else:
        raise ValueError("Ligne 70.0 introuvable dans le bloc C0700")

    return construire_df_c0700_recalcule(df_new, debug)

def calculer_somme_rwa_bloc(df_bloc, debug=False):
    """
    Calcule la somme des RWA (0220) pour un bloc avec meilleure gestion des erreurs
    """
    if debug:
        st.write("### CALCUL SOMME RWA BLOC")
   
    # Vérifier si la colonne 0220 existe
    if "0220" not in df_bloc.columns:
        if debug:
            st.error("Colonne 0220 absente du bloc")
        return 0
       
    # Lignes à inclure dans le total RWA
    rwa_lignes = [70.0, 80.0, 110.0]
   
    # Filtrer le dataframe et calculer la somme
    df_filtered = df_bloc[df_bloc["row"].isin(rwa_lignes)]
   
    if df_filtered.empty:
        if debug:
            st.warning("Aucune des lignes RWA (70.0, 80.0, 110.0) n'est présente dans le bloc")
        return 0
   
    # Remplacer les NaN par 0 et calculer la somme
    somme_rwa = df_filtered["0220"].fillna(0).sum()
   
    if debug:
        st.write(f"Somme RWA calculée: {somme_rwa}")
        st.write("Détail par ligne:")
        for ligne in rwa_lignes:
            if ligne in df_filtered["row"].values:
                val = df_filtered[df_filtered["row"] == ligne]["0220"].fillna(0).values[0]
                st.write(f"  - Ligne {ligne}: {val}")
   
    return somme_rwa

def somme_si_dispo(df, lignes):
    """Somme les valeurs de la colonne 0010 pour les lignes spécifiées avec gestion des erreurs"""
    total = 0
    for l in lignes:
        ligne = df[df["row"] == l]
        if not ligne.empty and "0010" in ligne.columns:
            val = ligne["0010"].values[0]
            if not pd.isna(val):
                total += val
    return total

def recalculer_arborescence_c0200(df_c02):
    """
    Recalcule toutes les lignes du tableau C0200 selon la structure arborescente
    en sommant les dépendants pour chaque parent.
    """
    df = df_c02.copy()

    formules = {
        10: [40, 520, 590, 640],
        40: [50, 240, 250, 310],
        50: [60],
        60: [70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 211],
        240: [241, 242],
        250: [260, 270, 280, 290, 300],
        310: [320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 450],
        490: [500, 510],
        520: [530, 580],
        530: [540, 550, 555, 560, 570],
        590: [600, 610, 620],
        640: [650, 660, 670],
        690: [710, 720, 730, 740, 750, 760]
    }

    # Convertir 'row' en float si elle est string
    if df["row"].dtype == object:
        df["row"] = pd.to_numeric(df["row"], errors="coerce")

    for parent, enfants in formules.items():
        somme = 0
        for enfant in enfants:
            val = df.loc[df["row"] == enfant, "0010"]
            if not val.empty and not pd.isna(val.values[0]):
                somme += val.values[0]
        idx_parent = df[df["row"] == parent].index
        if not idx_parent.empty:
            df.at[idx_parent[0], "0010"] = somme

    return df


def calculer_fonds_propres_annee(df_c01_prec, bilan_df, annee):
    """
    Ajoute le capital planning au résultat (ligne 150) et recalcule les fonds propres
    """
    poste = "Income Statement - Résultat de l'exercice"
    cp_annee = get_capital_planning_below(bilan_df, poste, annee)

    df_c01_annee = df_c01_prec.copy()
    idx_150 = df_c01_annee[df_c01_annee["row"] == 150].index

    if not idx_150.empty and cp_annee is not None:
        ancienne_val = df_c01_annee.at[idx_150[0], "0010"] or 0
        df_c01_annee.at[idx_150[0], "0010"] = ancienne_val + cp_annee

    df_c01_annee = recalculer_c0100_arborescence(df_c01_annee)

    idx_20 = df_c01_annee[df_c01_annee["row"] == 20].index
    fonds_propres = df_c01_annee.at[idx_20[0], "0010"] if not idx_20.empty else None

    return df_c01_annee, fonds_propres

def recalculer_c0100_arborescence(df_c01):
    """
    Recalcule les blocs CET1, AT1 et Tier 2 du tableau C0100
    """
    df = df_c01.copy()

    formules_cet1 = {
        30: [40, 60, 70, 92],
        70: [80, 90, 91],
        130: [140, 150],
        150: [160, 170],
        250: [260, 270, 280, 285, 290],
        300: [310, 320, 330, 335],
        340: [350, 360, 365],
        390: [400, 410, 420],
        20: [30, 130, 180, 200, 210, 220, 240, 230, 250, 300, 340, 370, 380, 390,
             430, 440, 450, 460, 470, 471, 472, 480, 490, 500, 510, 511, 512,
             513, 514, 515, 520, 524, 529]
    }

    formules_at1 = {
        530: [540, 660, 670, 680, 690, 700, 710, 720, 730, 740, 744, 748],
        540: [551, 571, 580, 622],
        580: [590, 620, 621],
    }

    formules_tier2 = {
        750: [760, 880, 890, 900, 910, 920, 930, 940, 950, 955, 960, 970, 974, 978],
        760: [771, 791, 800, 842],
        800: [810, 840, 841],
    }

    for bloc in [formules_cet1, formules_at1, formules_tier2]:
        for ligne_parent, dependants in bloc.items():
            total = somme_si_dispo(df, dependants)
            idx = df[df["row"] == ligne_parent].index
            if not idx.empty:
                df.at[idx[0], "0010"] = total

    return df

def calculer_ratio_solvabilite(df_c01, df_c02):
    """
    Calcule le ratio de solvabilité = fonds propres réglementaires / total RWA
    """
    # Numérateur : ligne 20 dans C0100
    fp = df_c01.loc[df_c01["row"] == 20, "0010"]
    # Dénominateur : ligne 10 dans C0200
    rwa = df_c02.loc[df_c02["row"] == 10, "0010"]

    if fp.empty or rwa.empty or rwa.values[0] == 0:
        return None

    ratio = fp.values[0] / rwa.values[0] * 100
    return round(ratio, 2)
def traiter_poste_capital_planning(poste, feuille, bilan, annee, df_bloc_prec, df_c02):
    """
    Injecte le capital planning pour un poste donné et met à jour le C0200.
    Corrigée : conversion des index 'row' en string pour une bonne correspondance avec le mapping.
    """
    cp_value = get_capital_planning_below(bilan, poste, annee)
    if cp_value is None or pd.isna(cp_value):
        return df_bloc_prec.copy(), 0, df_c02

    # Injection et recalcul
    df_bloc_avec_cp = injecter_capital_planning_dans_bloc(df_bloc_prec, cp_value)
    df_bloc_recalcule = construire_df_c0700_recalcule(df_bloc_avec_cp)

    # Calcul du delta RWA
    rwa_ancien = calculer_somme_rwa_bloc(df_bloc_prec)
    rwa_nouveau = calculer_somme_rwa_bloc(df_bloc_recalcule)
    delta_rwa = rwa_nouveau - rwa_ancien

    # Mise à jour de la ligne cible dans C0200
    code_ligne = mapping_c0700_to_c0200.get(feuille)
    if code_ligne:
        df_c02_new = df_c02.copy()
        df_c02_new["row"] = df_c02_new["row"].astype(str)  # 🔁 Cast obligatoire

        idx = df_c02_new[df_c02_new["row"] == code_ligne].index
        if not idx.empty:
            ancienne_valeur = df_c02_new.at[idx[0], "0010"] or 0
            df_c02_new.at[idx[0], "0010"] = ancienne_valeur + delta_rwa

        return df_bloc_recalcule, delta_rwa, df_c02_new

    return df_bloc_recalcule, delta_rwa, df_c02

def traiter_tous_postes(bilan, annee, blocs_prec, df_c02_prec):
    """
    Traite tous les postes du mapping_feuilles_rwa et retourne :
    - blocs recalculés
    - C0200 mis à jour (ligne 10 mise à jour directement)
    - journal des deltas
    """
    blocs_recalcules = {}
    df_c02_new = df_c02_prec.copy()
    journal_deltas = []
    total_delta_rwa = 0  # 👈 Cumul global

    for poste, feuilles in mapping_feuilles_rwa.items():
        for feuille in feuilles:
            df_bloc_prec = blocs_prec.get(feuille, pd.DataFrame(columns=["row", "0010", "0200", "0215", "0220"]))
            bloc_new, delta_rwa, df_c02_new = traiter_poste_capital_planning(
                poste, feuille, bilan, annee, df_bloc_prec, df_c02_new
            )
            blocs_recalcules[feuille] = bloc_new
            journal_deltas.append((poste, feuille, delta_rwa))
            total_delta_rwa += delta_rwa  # 👈 Ajouter au total

    # Mise à jour directe de la ligne 10 (total RWA)
    idx_10 = df_c02_new[df_c02_new["row"] == 10].index
    if not idx_10.empty:
        ancienne_val = df_c02_new.at[idx_10[0], "0010"] or 0
        df_c02_new.at[idx_10[0], "0010"] = ancienne_val + total_delta_rwa
    else:
        # Si la ligne 10 n'existe pas, on peut l'ajouter
        nouvelle_ligne = pd.DataFrame([{"row": 10, "0010": total_delta_rwa}])
        df_c02_new = pd.concat([df_c02_new, nouvelle_ligne], ignore_index=True)

    return blocs_recalcules, df_c02_new, journal_deltas


def simuler_solvabilite_pluriannuelle(
    bilan, df_c01_2024, df_c02_2024, blocs_c0700_2024,
    annees=["2025", "2026", "2027"]
):
    """
    Version modifiée qui ne s'appuie plus sur C0200 mis à jour, mais reconstruit le RWA total
    à partir des deltas cumulés.
    """
    resultats = {
        "2024": {
            "ratio": calculer_ratio_solvabilite(df_c01_2024, df_c02_2024),
            "fonds_propres": df_c01_2024.loc[df_c01_2024["row"] == 20, "0010"].values[0],
            "rwa": df_c02_2024.loc[df_c02_2024["row"] == 10, "0010"].values[0],
            "df_c01": df_c01_2024.copy(),
            "df_c02": df_c02_2024.copy(),
            "blocs_rwa": {nom: df.copy() for nom, df in blocs_c0700_2024.items()},
            "rwa_cumule": df_c02_2024.loc[df_c02_2024["row"] == 10, "0010"].values[0]
        }
    }

    blocs_reference = {nom: df.copy() for nom, df in blocs_c0700_2024.items()}
    rwa_courant = resultats["2024"]["rwa_cumule"]

    for annee in annees:
        annee_prec = str(int(annee) - 1)

        blocs_annee, _, log_deltas = traiter_tous_postes(
            bilan, annee, blocs_reference, resultats[annee_prec]["df_c02"]
        )

        delta_total = sum(delta for _, _, delta in log_deltas)
        rwa_courant += delta_total

        df_c01_new, fonds_propres = calculer_fonds_propres_annee(
            resultats[annee_prec]["df_c01"],
            bilan, annee
        )
        ratio = round(fonds_propres / rwa_courant * 100, 2) if rwa_courant else None

        resultats[annee] = {
            "ratio": ratio,
            "fonds_propres": fonds_propres,
            "rwa": rwa_courant,
            "df_c01": df_c01_new,
            "df_c02": resultats[annee_prec]["df_c02"],  # figé
            "blocs_rwa": blocs_annee,
            "deltas": log_deltas,
            "rwa_cumule": rwa_courant
        }

    return resultats

def format_large_number(num):
    """Formate les grands nombres pour l'affichage"""
    if pd.isna(num) or num == 0:
        return "0"
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    else:
        return f"{num:,.2f}"

def afficher_ratios_solvabilite(resultats_solva):
    """Affiche les résultats des ratios de solvabilité dans Streamlit"""
    st.subheader("Ratio de Solvabilité")
    with st.expander("Ratio de Solvabilité", expanded=True):
        st.write("**Définition :** Le ratio de solvabilité mesure la capacité d'une banque à absorber les pertes par rapport à ses actifs pondérés par le risque.")
        st.latex(r"\\text{Solvabilité} = \\frac{\\text{Fonds propres réglementaires}}{\\text{RWA}}")
        st.write("**Interprétation :** Un ratio ≥ 8% indique une bonne couverture des risques.")

    for annee, result in resultats_solva.items():
        with st.expander(f"Détails pour {annee}", expanded=(annee == "2024")):
            st.markdown(f"### Année {annee}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ratio", f"{result['ratio']:.2f}%")
            with col2:
                st.metric("Fonds propres", format_large_number(result["fonds_propres"]))
            with col3:
                st.metric("RWA", format_large_number(result["rwa"]))

            # Tableau C0100 filtré (Fonds propres)
            st.markdown("**Fonds Propres (C0100)**")
            df_c01_filtre = result["df_c01"]
            lignes_fp = [20, 30, 150, 530, 750]
            df_fp = df_c01_filtre[df_c01_filtre["row"].isin(lignes_fp)]
            if not df_fp.empty:
                st.dataframe(df_fp, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour C0100.")

            # Tableau C0200 filtré (RWA)
            st.markdown("**Actifs Pondérés par le Risque (C0200)**")
            df_c02_filtre = result["df_c02"]
            lignes_rwa = [10, 40, 60, 120, 130, 140, 210, 211]
            df_rwa = df_c02_filtre[df_c02_filtre["row"].isin(lignes_rwa)]
            if not df_rwa.empty:
                st.dataframe(df_rwa, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour C0200.")

            # Détails des blocs C0700 si disponibles
            if "blocs_rwa" in result:
                for nom_bloc, bloc in result["blocs_rwa"].items():
                    st.markdown(f"**Bloc RWA - {nom_bloc} (C0700)**")
                    if not bloc.empty:
                        st.dataframe(bloc, use_container_width=True)
                    else:
                        st.info(f"Aucune donnée disponible pour {nom_bloc}.")

def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(row.get(c, 0) for c in cols if pd.notna(row.get(c, 0)))



def get_tier1_value(df_c01):
    """
    Récupère la valeur du Tier 1 (ligne 15) du tableau C0100
    """
    idx = df_c01[df_c01["row"] == 15].index
    if not idx.empty:
        return df_c01.loc[idx[0], "0010"]
    return None

# Mapping pour identifier les postes du bilan correspondant aux lignes dans C4700
# Ce mapping relie les postes du bilan aux catégories d'exposition dans le calcul du ratio de levier
mapping_bilan_to_c4700 = {
    "Caisse Banque Centrale / nostro": 190,  # Other assets
    "Créances banques autres": 190,  # Other assets
    "Créances sur la clientèle (total)": 190,  # Other assets
   # Other assets
    "Immobilisations et Autres Actifs": 190   # Other assets
}

def calcul_total_exposure(df_c4700, valeur_stressee_0190=None):
    """
    Calcule l'exposition totale pour le ratio de levier
    """
    rows_a_inclure = [
        10, 20, 30, 40, 50, 61, 65, 71, 81, 91, 92, 93,
        101, 102, 103, 104, 110, 120, 130, 140, 150, 160, 170, 180,
        181, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 196,
        197, 198, 200, 210, 220, 230, 235, 240, 250, 251, 252, 253,
        254, 255, 256, 257, 260, 261, 262, 263, 264, 265, 266, 267, 270
    ]
   
    df_temp = df_c4700.copy()
   
    if valeur_stressee_0190 is not None:
        idx = df_temp[df_temp['Row'] == 190].index
        if not idx.empty:
            df_temp.loc[idx[0], '0010'] += valeur_stressee_0190
        else:
            # Si ligne 190 absente, on l'ajoute
            new_row = pd.DataFrame([{"Row": 190, "0010": valeur_stressee_0190}])
            df_temp = pd.concat([df_temp, new_row], ignore_index=True)
   
    total_exposure = (
        df_temp[df_temp['Row'].isin(rows_a_inclure)]
        .apply(lambda row: somme_sans_nan(row, ['0010']), axis=1)
        .sum()
    )
   
    return total_exposure, df_temp

def calculer_ratio_levier(tier1_value, total_exposure):
    """
    Calcule le ratio de levier = Tier 1 / Total Exposure
    """
    if pd.isna(tier1_value) or pd.isna(total_exposure) or total_exposure == 0:
        return None
   
    ratio = (tier1_value / total_exposure) * 100
    return round(ratio, 2)


    # === Récupération du capital planning ===
def get_capital_planning_below(bilan_df, poste_bilan, annee="2025"):
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index
    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                return valeur
    return None



def calculer_fonds_propres_tier1_annee(df_c01_prec, bilan_df, annee):
    """
    Ajoute le capital planning au résultat (ligne 150) et recalcule les fonds propres Tier 1
    """
    poste = "Income Statement - Résultat de l'exercice"
    cp_annee = get_capital_planning_below(bilan_df, poste, annee)

    df_c01_annee = df_c01_prec.copy()
    idx_150 = df_c01_annee[df_c01_annee["row"] == 150].index

    if not idx_150.empty and cp_annee is not None:
        ancienne_val = df_c01_annee.at[idx_150[0], "0010"] or 0
        df_c01_annee.at[idx_150[0], "0010"] = ancienne_val + cp_annee

    df_c01_annee = recalculer_c0100_arborescence(df_c01_annee)

    idx_15 = df_c01_annee[df_c01_annee["row"] == 15].index
    tier1 = df_c01_annee.at[idx_15[0], "0010"] if not idx_15.empty else None

    return df_c01_annee, tier1

def recalculer_c0100_arborescence(df_c01):
    """
    Recalcule les blocs CET1, AT1 et Tier 2 du tableau C0100
    """
    df = df_c01.copy()

    formules_cet1 = {
        30: [40, 60, 70, 92],
        70: [80, 90, 91],
        130: [140, 150],
        150: [160, 170],
        250: [260, 270, 280, 285, 290],
        300: [310, 320, 330, 335],
        340: [350, 360, 365],
        390: [400, 410, 420],
        20: [30, 130, 180, 200, 210, 220, 240, 230, 250, 300, 340, 370, 380, 390,
             430, 440, 450, 460, 470, 471, 472, 480, 490, 500, 510, 511, 512,
             513, 514, 515, 520, 524, 529]
    }

    formules_at1 = {
        530: [540, 660, 670, 680, 690, 700, 710, 720, 730, 740, 744, 748],
        540: [551, 571, 580, 622],
        580: [590, 620, 621],
    }

    # Ajout de la formule pour Tier1 = CET1 + AT1
    formules_tier1 = {
        15: [20, 530]  # Tier1 = CET1 + AT1
    }

    for bloc in [formules_cet1, formules_at1, formules_tier1]:
        for ligne_parent, dependants in bloc.items():
            idx = df[df["row"] == ligne_parent].index
            if not idx.empty:
                total = sum(
                    df.loc[df["row"] == l, "0010"].values[0]
                    for l in dependants
                    if l in df["row"].values and not df.loc[df["row"] == l, "0010"].isna().all()
                )
                df.at[idx[0], "0010"] = total

    return df

def simuler_levier_pluriannuel(
    bilan, df_c01_2024, df_c4700_2024,
    annees=["2025", "2026", "2027"]):
    """
    Simule la projection des ratios de levier pour plusieurs années
    """
    # Obtenir Tier1 initial
    tier1_2024 = get_tier1_value(df_c01_2024)
    # Calcul de l'exposition totale initiale
    total_exposure_2024, _ = calcul_total_exposure(df_c4700_2024)
   
    resultats = {
        "2024": {
            "ratio": calculer_ratio_levier(tier1_2024, total_exposure_2024),
            "tier1": tier1_2024,
            "total_exposure": total_exposure_2024,
            "df_c01": df_c01_2024.copy(),
            "df_c4700": df_c4700_2024.copy()
        }
    }
   
    # Utiliser pour simuler les années suivantes
    dict_df_c01 = {"2024": df_c01_2024.copy()}
    dict_df_c4700 = {"2024": df_c4700_2024.copy()}
   
    for annee in annees:
        print(f"\n🔁 Traitement de l'année {annee} pour levier")
        annee_prec = str(int(annee) - 1)
       
        # ÉTAPE 1: Recalcul de Tier1 avec le capital planning
        df_c01_new, tier1_value = calculer_fonds_propres_tier1_annee(
            dict_df_c01[annee_prec],
            bilan, annee
        )
       
        # ÉTAPE 2: Mise à jour de l'exposition pour le ratio de levier
        df_c4700_prec = dict_df_c4700[annee_prec].copy()
       
        # Calculer la somme des modifications de capital planning à intégrer dans "Other assets"
        somme_capital_planning = 0
        for poste, row_c4700 in mapping_bilan_to_c4700.items():
            cp_value = get_capital_planning_below(bilan, poste, annee)
            if cp_value is not None:
                somme_capital_planning += cp_value
       
        # Recalculer l'exposition totale avec la somme des capital planning
        total_exposure, df_c4700_new = calcul_total_exposure(df_c4700_prec, somme_capital_planning)
       
        # Calcul du ratio de levier final
        ratio = calculer_ratio_levier(tier1_value, total_exposure)
       
        # Sauvegarde des résultats
        resultats[annee] = {
            "ratio": ratio,
            "tier1": tier1_value,
            "total_exposure": total_exposure,
            "df_c01": df_c01_new,
            "df_c4700": df_c4700_new
        }
       
        # Stockage pour la prochaine itération
        dict_df_c01[annee] = df_c01_new
        dict_df_c4700[annee] = df_c4700_new

    return resultats

def format_large_number(num):
    """Formate les grands nombres pour l'affichage"""
    if pd.isna(num) or num == 0:
        return "0"
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    else:
        return f"{num:,.2f}"

def afficher_ratios_levier(resultats_levier):
    """Affiche les résultats des ratios de levier dans Streamlit"""
    st.subheader("Ratio de Levier")
    with st.expander("Ratio de Levier", expanded=True):
        st.write("**Définition :** Le ratio de levier mesure la capacité d'une banque à faire face à ses engagements, indépendamment de la pondération des risques.")
        st.latex(r"\\text{Levier} = \\frac{\\text{Tier 1}}{\\text{Exposition Totale}}")
        st.write("**Interprétation :** Un ratio ≥ 3% est généralement requis par la réglementation bancaire européenne.")

    for annee, result in resultats_levier.items():
        with st.expander(f"Détails pour {annee}", expanded=(annee == "2024")):
            st.markdown(f"### Année {annee}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ratio", f"{result['ratio']:.2f}%")
            with col2:
                st.metric("Tier 1 (C0100)", format_large_number(result['tier1']))
            with col3:
                st.metric("Exposition Totale (C4700)", format_large_number(result['total_exposure']))

            st.markdown("**Tier 1 (extrait de C0100)**")
            st.dataframe(result["df_c01"][result["df_c01"]["row"].isin([15, 20, 530])], use_container_width=True)

            st.markdown("**C4700 (exposition totale)**")
            key_rows = [10, 61, 91, 130, 150, 160, 170, 180, 190, 270]  # Lignes principales pour C4700
            st.dataframe(result["df_c4700"][result["df_c4700"]["Row"].isin(key_rows)], use_container_width=True)
