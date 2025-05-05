import os
import pandas as pd
import numpy as np
import shutil
from openpyxl import load_workbook

def charger_bilan():
    """
    Charge le fichier de bilan bancaire situé dans le dossier 'data/'.
    Nettoie et structure le fichier pour utilisation dans le stress test.
    """
    bilan_path = os.path.join("data", "bilan.xlsx")
    
    if not os.path.exists(bilan_path):
        raise FileNotFoundError(f"Le fichier {bilan_path} est introuvable.")
    
    bilan = pd.read_excel(bilan_path)
    bilan = bilan.iloc[2:].reset_index(drop=True)

    if "Unnamed: 1" in bilan.columns:
        bilan = bilan.drop(columns=["Unnamed: 1"])

    colonnes = list(bilan.columns)
    for i, col in enumerate(colonnes):
        if str(col).startswith("Unnamed: 6"):
            bilan = bilan.iloc[:, :i]
            break

    bilan.columns.values[0] = "Poste du Bilan"
    bilan.columns.values[1] = "2024"
    bilan.columns.values[2] = "2025"
    bilan.columns.values[3] = "2026"
    bilan.columns.values[4] = "2027"

    bilan = bilan.dropna(how="all").reset_index(drop=True)
    return bilan


def charger_lcr():
    """
    Charge le fichier LCR situé dans le dossier 'data/'.
    """
    lcr_path = os.path.join("data", "LCR.csv")
    
    if not os.path.exists(lcr_path):
        raise FileNotFoundError(f"Le fichier {lcr_path} est introuvable.")
    
    df_72 = pd.read_excel(lcr_path, sheet_name="C7200_TOTAL")
    df_73 = pd.read_excel(lcr_path, sheet_name="C7300_TOTAL")
    df_74 = pd.read_excel(lcr_path, sheet_name="C7400_TOTAL")
    
    return df_72, df_73, df_74


def get_valeur_poste_bilan(bilan_df, poste_bilan, annee="2024"):
    """
    Récupère la valeur d'un poste du bilan pour une année donnée.
    """
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index

    if not index_poste.empty:
        i = index_poste[0] 
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                return valeur
    return None


def ajuster_annees_suivantes(bilan_df, poste, annee_depart, variation):
    """
    Ajuste la valeur d'un poste pour toutes les années > annee_depart en appliquant la variation.
    """
    bilan_df = bilan_df.copy()
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste].index
    if index_poste.empty:
        return bilan_df  # Poste non trouvé

    idx = index_poste[0]
    annees = [col for col in bilan_df.columns if str(col).isdigit()]
    annees_suivantes = [a for a in annees if int(a) > int(annee_depart)]

    for an in annees_suivantes:
        bilan_df.loc[idx, an] -= variation

    return bilan_df


def appliquer_stress_retrait_depots(bilan_df, p1, p2=1, p3='equitable', annee="2025",
                                   poids_portefeuille=0.5, poids_creances=0.5):
    """
    Applique un stress de retrait massif des dépôts sur le bilan.
    
    Args:
        bilan_df: DataFrame du bilan
        p1: Pourcentage de diminution des dépôts (entre 0 et 1)
        p2: Horizon d'absorption du choc en années (par défaut: 1)
        p3: Mode d'écoulement ('equitable' ou 'premiere_annee')
        annee: Année de départ du stress (par défaut: 2025)
        poids_portefeuille: Proportion de l'effet sur le portefeuille (entre 0 et 1)
        poids_creances: Proportion de l'effet sur les créances bancaires (entre 0 et 1)
        
    Returns:
        DataFrame du bilan stressé
    """
    bilan_df = bilan_df.copy()

    poste_depots = "Depots clients (passif)"
    poste_portefeuille = "Portefeuille"
    poste_creances = "Créances banques autres"

    valeur_depots = get_valeur_poste_bilan(bilan_df, poste_depots, annee)
    if valeur_depots is None:
        raise ValueError(f"Poste '{poste_depots}' non trouvé ou valeur manquante pour {annee}.")

    # Calcul du choc total et annuel
    choc_total = valeur_depots * p1
    
    if p3 == 'equitable' and p2 > 1:
        choc_annuel = choc_total / p2  # Répartition équitable sur p2 années
    else:  # 'premiere_annee'
        choc_annuel = choc_total  # Tout le choc sur la première année

    for i in range(p2):
        target_annee = str(int(annee) + i)
        
        # Si mode première année, on n'applique le choc que la première année
        if p3 == 'premiere_annee' and i > 0:
            break
            
        # Dépôts clients → baisse
        idx_dep = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_depots].index[0]
        if i == 0 or p3 == 'equitable':
            bilan_df.loc[idx_dep, target_annee] -= choc_annuel
            bilan_df = ajuster_annees_suivantes(bilan_df, poste_depots, target_annee, choc_annuel)

        # Portefeuille → baisse
        reduction_portefeuille = choc_annuel * poids_portefeuille
        idx_port = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_portefeuille].index[0]
        if i == 0 or p3 == 'equitable':
            bilan_df.loc[idx_port, target_annee] -= reduction_portefeuille
            bilan_df = ajuster_annees_suivantes(bilan_df, poste_portefeuille, target_annee, reduction_portefeuille)

        # Créances banques autres → baisse
        reduction_creances = choc_annuel * poids_creances
        idx_cre = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_creances].index[0]
        if i == 0 or p3 == 'equitable':
            bilan_df.loc[idx_cre, target_annee] -= reduction_creances
            bilan_df = ajuster_annees_suivantes(bilan_df, poste_creances, target_annee, reduction_creances)

    return bilan_df


def get_delta_bilan(original_df, stressed_df, poste_bilan, annee):
    """
    Calcule la différence entre la valeur originale et stressée pour un poste donné.
    """
    val_orig = original_df.loc[original_df["Poste du Bilan"] == poste_bilan, annee].values[0]
    val_stressed = stressed_df.loc[stressed_df["Poste du Bilan"] == poste_bilan, annee].values[0]
    return val_orig - val_stressed


def propager_delta_vers_corep(poste_bilan, delta, df_72, df_73, df_74):
    """
    Répartit un delta sur les lignes COREP liées à un poste du bilan.
    """
    # Mapping entre postes du bilan et lignes COREP
    mapping_bilan_LCR_NSFR = {
        "Caisse Banque Centrale / nostro": [
            ("row_0040", "df_72"),  # LB: Coins and banknotes
            ("row_0050", "df_72"),  # LB: Withdrawable central bank reserves
        ],
        "Créances banques autres": [
            ("row_0060", "df_72"),  # LB: Central bank assets
            ("row_0160", "df_74"),  # Inflow: Monies due from financial customers
        ],
        "Portefeuille": [
            ("row_0070", "df_72"),  # central government assets
            ("row_0100", "df_72"),  # recognised central government assets
        ],
        "Depots clients (passif)": [
            ("row_0030", "df_73"),  # retail deposits
            ("row_0120", "df_73"),  # Operational deposits
            ("row_0210", "df_73"),  # Non-operational deposits
        ],
    }
    
    if poste_bilan not in mapping_bilan_LCR_NSFR:
        return df_72, df_73, df_74  # Poste non mappé, rien à faire
    
    # Récupérer les lignes COREP associées
    lignes = mapping_bilan_LCR_NSFR[poste_bilan]
    n = len(lignes)
    
    if n == 0:
        return df_72, df_73, df_74  # Aucune ligne à modifier
    
    # Répartition équitable du delta
    poids = 1.0 / n
    
    for row_str, df_name in lignes:
        row_num = int(row_str.replace("row_", ""))
        delta_par_ligne = delta * poids
        
        if df_name == "df_72":
            if row_num in df_72["row"].values:
                idx = df_72[df_72["row"] == row_num].index[0]
                df_72.loc[idx, "0010"] = df_72.loc[idx, "0010"] - delta_par_ligne
        elif df_name == "df_73":
            if row_num in df_73["row"].values:
                idx = df_73[df_73["row"] == row_num].index[0]
                df_73.loc[idx, "0010"] = df_73.loc[idx, "0010"] - delta_par_ligne
        elif df_name == "df_74":
            if row_num in df_74["row"].values:
                idx = df_74[df_74["row"] == row_num].index[0]
                df_74.loc[idx, "0010"] = df_74.loc[idx, "0010"] - delta_par_ligne
    
    return df_72, df_73, df_74


def calculer_ratio_lcr(df_72, df_73, df_74):
    """
    Calcule le ratio LCR à partir des feuilles COREP.
    
    La formule simplifiée du LCR est:
    LCR = HQLA / Sorties nettes de trésorerie sur 30 jours
    """
    from backend.lcr.feuille_72 import calcul_HQLA
    from backend.lcr.feuille_73 import calcul_outflow
    from backend.lcr.feuille_74 import calcul_inflow
    from backend.lcr.utils import Calcul_LCR
    
    
    HQLA = calcul_HQLA(df_72)
    OUTFLOWS = calcul_outflow(df_73)
    inflow = calcul_inflow(df_74)
    LCR = Calcul_LCR(inflow,OUTFLOWS,HQLA)
    return LCR


def afficher_postes_concernes(bilan_df, postes, annees=["2024", "2025", "2026", "2027"]):
    """
    Extrait les postes concernés du bilan pour les années spécifiées.
    """
    resultats = []

    for poste in postes:
        idx = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste].index
        if not idx.empty:
            ligne_valeurs = bilan_df.loc[idx[0], ["Poste du Bilan"] + annees]
            resultats.append(ligne_valeurs)

    return pd.DataFrame(resultats).set_index("Poste du Bilan")


def sauvegarder_bilan_stresse(bilan_stresse, output_filename="bilan_stresse.xlsx", output_dir="data"):
    """
    Sauvegarde le bilan stressé dans un fichier Excel.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    bilan_stresse.to_excel(output_path, index=False)
    return output_path


def sauvegarder_corep_modifie(original_path, df_72, df_73, df_74, output_filename="LCR_stresse.xlsx", output_dir="data"):
    """
    Crée une copie du fichier COREP original et remplace les feuilles.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)
    
    shutil.copyfile(original_path, output_path)
    
    with pd.ExcelWriter(output_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_72.to_excel(writer, sheet_name="C7200_TOTAL", index=False)
        df_73.to_excel(writer, sheet_name="C7300_TOTAL", index=False)
        df_74.to_excel(writer, sheet_name="C7400_TOTAL", index=False)
    
    return output_path


def executer_stress_test_retrait_depots(p1, p2=1, p3='equitable', annee_depart="2025", 
                                       poids_portefeuille=0.5, poids_creances=0.5):
    """
    Exécute le stress test complet pour le scénario de retrait massif des dépôts.
    
    Args:
        p1: Pourcentage de diminution des dépôts (entre 0 et 1)
        p2: Horizon d'absorption du choc en années
        p3: Mode d'écoulement ('equitable' ou 'premiere_annee')
        annee_depart: Année de départ du stress
        poids_portefeuille: Proportion de l'effet sur le portefeuille
        poids_creances: Proportion de l'effet sur les créances bancaires
        
    Returns:
        Un dictionnaire contenant les résultats du stress test
    """
    try:
        # 1. Charger les données
        bilan_original = charger_bilan()
        df_72, df_73, df_74 = charger_lcr()
        lcr_path = os.path.join("data", "LCR.csv")
        
        # 2. Appliquer le stress sur le bilan
        bilan_stresse = appliquer_stress_retrait_depots(
            bilan_original, p1, p2, p3, annee_depart, 
            poids_portefeuille, poids_creances
        )
        
        # 3. Extraire les postes impactés pour affichage
        postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
        bilan_impacte = afficher_postes_concernes(bilan_stresse, postes_concernes)
        bilan_original_impacte = afficher_postes_concernes(bilan_original, postes_concernes)
        
        # 4. Calculer les deltas pour chaque poste et année
        deltas = {}
        annees = [str(int(annee_depart) + i) for i in range(p2)]
        
        for poste in postes_concernes:
            for annee in annees:
                delta = get_delta_bilan(bilan_original, bilan_stresse, poste, annee)
                deltas[(poste, annee)] = delta
                
                # 5. Propager les deltas vers COREP
                df_72, df_73, df_74 = propager_delta_vers_corep(poste, delta, df_72, df_73, df_74)
        
        # 6. Calculer le ratio LCR original et stressé
        lcr_original = calculer_ratio_lcr(*charger_lcr())
        lcr_stresse = calculer_ratio_lcr(df_72, df_73, df_74)
        
        # 7. Sauvegarder les fichiers
        chemin_bilan_stresse = sauvegarder_bilan_stresse(bilan_stresse)
        chemin_lcr_stresse = sauvegarder_corep_modifie(lcr_path, df_72, df_73, df_74)
        
        # 8. Préparer les résultats
        resultats = {
            "bilan_original": bilan_original,
            "bilan_stresse": bilan_stresse,
            "bilan_impacte": bilan_impacte,
            "bilan_original_impacte": bilan_original_impacte,
            "lcr_original": lcr_original,
            "lcr_stresse": lcr_stresse,
            "delta_lcr": lcr_original - lcr_stresse if lcr_original and lcr_stresse else None,
            "deltas": deltas,
            "chemin_bilan_stresse": chemin_bilan_stresse,
            "chemin_lcr_stresse": chemin_lcr_stresse,
            "parametres": {
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "annee_depart": annee_depart,
                "poids_portefeuille": poids_portefeuille,
                "poids_creances": poids_creances
            }
        }
        
        return resultats
    
    except Exception as e:
        return {"erreur nom de l'error ": str(e)}