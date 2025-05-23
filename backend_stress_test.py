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
    bilan[["2024", "2025", "2026", "2027"]] = bilan[["2024", "2025", "2026", "2027"]].apply(pd.to_numeric, errors='coerce')
    return bilan


def charger_lcr():
    """
    Charge le fichier LCR situé dans le dossier 'data/'.
    """
    from backend.lcr.feuille_72 import charger_feuille_72
    from backend.lcr.feuille_73 import charger_feuille_73
    from backend.lcr.feuille_74 import charger_feuille_74
    
    lcr_path = os.path.join("data", "LCR.csv")
    
    if not os.path.exists(lcr_path):
        raise FileNotFoundError(f"Le fichier {lcr_path} est introuvable.")
    
    df_72 = charger_feuille_72(lcr_path)
    df_73 = charger_feuille_73(lcr_path)
    df_74 = charger_feuille_74(lcr_path)

    
    return df_72, df_73, df_74

def charger_nsfr():
    """
    Charge le fichier NSFR situé dans le dossier 'data/'.
    """
    from backend.nsfr.feuille_80 import charger_feuille_80
    from backend.nsfr.feuille_81 import charger_feuille_81
    
    nsfr_path = os.path.join("data", "NSFR.csv")
    
    if not os.path.exists(nsfr_path):
        raise FileNotFoundError(f"Le fichier {nsfr_path} est introuvable.")
    
    df_80 = charger_feuille_80(nsfr_path)
    df_81 = charger_feuille_81(nsfr_path)

    return df_80, df_81


def get_valeur_poste_bilan(bilan_df, poste_bilan, annee="2024"):
    """
    Récupère la valeur d’un poste du bilan pour une année donnée, en tenant compte que
    les lignes impaires contiennent les valeurs des lignes de titre situées juste avant.
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
    Ajuste la valeur d’un poste pour toutes les années > annee_depart en appliquant la variation.
    """
    bilan_df = bilan_df.copy()
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste].index
    if index_poste.empty:
        return bilan_df  # Poste non trouvé

    idx = index_poste[0]
    annees = [col for col in bilan_df.columns if col.isdigit()]
    annees_suivantes = [a for a in annees if int(a) > int(annee_depart)]

    for an in annees_suivantes:
        bilan_df.loc[idx, an] -= variation

    return bilan_df


def appliquer_stress_retrait_depots(bilan_df, pourcentage, horizon=1, annee="2025",
                                    poids_portefeuille=0.5, poids_creances=0.5):
    bilan_df = bilan_df.copy()

    poste_depots = "Depots clients (passif)"
    poste_portefeuille = "Portefeuille"
    poste_creances = "Créances banques autres"

    valeur_depots = get_valeur_poste_bilan(bilan_df, poste_depots, annee)
    if valeur_depots is None:
        raise ValueError(f"Poste '{poste_depots}' non trouvé ou valeur manquante pour {annee}.")

    choc_total = valeur_depots *pourcentage
    choc_annuel = choc_total / horizon 

    for i in range(horizon):
        target_annee = str(int(annee) + i)

        # Dépôts clients → baisse
        idx_dep = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_depots].index[0]
        bilan_df.loc[idx_dep, target_annee] -= choc_annuel
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_depots, target_annee, choc_annuel)

        # Portefeuille → baisse
        reduction_portefeuille = choc_annuel * poids_portefeuille
        idx_port = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_portefeuille].index[0]
        bilan_df.loc[idx_port, target_annee] -= reduction_portefeuille
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_portefeuille, target_annee, reduction_portefeuille)

        # Créances banques autres → baisse
        reduction_creances = choc_annuel * poids_creances
        idx_cre = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_creances].index[0]
        bilan_df.loc[idx_cre, target_annee] -= reduction_creances
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_creances, target_annee, reduction_creances)

    return bilan_df

mapping_bilan_LCR_NSFR = {
    "Caisse Banque Centrale / nostro": [
        ("row_0040", "df_72"),  # LB: Coins and banknotes
        ("row_0050", "df_72"),  # LB: Withdrawable central bank reserves
        ("row_0150", "df_72"),  # Inflow: Monies due from central banks
        ("row_0030", "df_74"),  # NSFR: Central bank assets
    ],
    "Créances banques autres": [
        ("row_0060", "df_72"),  # LB: Central bank assets
        ("row_0160", "df_74"),  # Inflow: Monies due from financial customers
        ("row_0100", "df_74"),  # Inflow: Monies due from CB + financial customers
        ("row_0730", "df_80"),  # NSFR: RSF from loans to financial customers
    ],
    "Créances hypothécaires": [
        ("row_0030", "df_72"),  # Inflow – à ajuster selon contrepartie
        ("row_0800", "df_74"),  # NSFR
        ("row_0810", "df_74"),
    ],
    "Créances clientèle (hors hypo)": [
        ("row_0030", "df_72"),
        ("row_0060", "df_72"),
        ("row_0070", "df_72"),
        ("row_0080", "df_72"),
        ("row_0090", "df_72"),
    ],
    "Portefeuille": [
        ("row_0070", "df_72"),  ## central government assets
        ("row_0100", "df_72"),  ## recognised central government assets
        ("row_0190", "df_72"),  ## extremely high-quality covered bonds
        ("row_0200", "df_72"),  ## high-quality covered bonds
        ("row_0260", "df_72"),  ## high-quality covered bonds (CQS2)
        ("row_0270", "df_72"),  ## high-quality covered bonds (CQS1)
    ],
    "Participations": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_0600", "df_74"),  # NSFR
    ],
    "Immobilisations et Autres Actifs": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_1030", "df_74"),
    ],
    "Dettes envers les établissements de crédit": [
        ("row_0230", "df_73"),
        ("row_1350", "df_73"),
        ("row_0270", "df_74"),
    ],
    "Depots clients (passif)": [
        ("row_0035", "df_73"),("row_0060", "df_73"),("row_0070", "df_73"),   ## retail deposits
        ("row_0120", "df_73"),  ## Operational deposits
        ("row_0203", "df_73"),  ## Excess operational deposits
        ("row_0210", "df_73"),  ## Non-operational deposits
        ("row_0070", "df_74"),
        ("row_0130", "df_74"),
        ("row_0200", "df_74"),
    ],
    "Autres passifs": [
        ("row_0885", "df_73"),
        ("row_0918", "df_73"),
        ("row_0390", "df_74"),
    ],
    "Comptes de régularisation": [
        ("row_0890", "df_73"),
        ("row_0390", "df_74"),
        ("row_0430", "df_74"),
    ],
    "Provisions": [
        ("row_X", "df_73"),
        ("row_0430", "df_74"),
    ],
    "Capital souscrit": [
        ("row_0030", "df_74"),
    ],
    "Primes émission": [
        ("row_0030", "df_74"),
    ],
    "Réserves": [
        ("row_0030", "df_74"),
    ],
    "Report à nouveau": [
        ("row_0030", "df_74"),
    ],
    "Résultat de l'exercice": [
        ("row_0030", "df_74"),
    ],
}


def afficher_postes_concernes(bilan_df, postes, annees=["2024", "2025", "2026", "2027"]):
    """
    Affiche uniquement les lignes associées aux postes concernés pour les années spécifiées.
    """
    resultats = []

    for poste in postes:
        idx = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste].index
        if not idx.empty:
            ligne_valeurs = bilan_df.loc[idx[0], ["Poste du Bilan"] + annees]
            resultats.append(ligne_valeurs)

    return pd.DataFrame(resultats).set_index("Poste du Bilan")


def get_delta_bilan(original_df, stressed_df, poste_bilan, annee):
    """
    Calcule le delta (différence) entre la valeur originale et stressée pour un poste donné.

    Args:
        original_df (DataFrame): Le bilan original.
        stressed_df (DataFrame): Le bilan stressé.
        poste_bilan (str): Nom du poste.
        annee (str): Année considérée.

    Returns:
        float: La différence (delta > 0 si diminution).
    """
    val_orig = original_df.loc[original_df["Poste du Bilan"] == poste_bilan, annee].values[0]
    val_stressed = stressed_df.loc[stressed_df["Poste du Bilan"] == poste_bilan, annee].values[0]
    return val_orig - val_stressed

def get_mapping_df_row(post_bilan):
    """
    À partir d’un poste du bilan, retourne les lignes correspondantes et les DataFrames associées.

    Args:
        post_bilan (str): Le nom du poste du bilan (clé du dictionnaire `mapping_bilan_LCR_NSFR`).

    Returns:
        List[Tuple[int, str]]: Liste des tuples (row_number, df_name) où df_name ∈ {'df_72', 'df_73', 'df_74'}.
    """
    result = []
    if post_bilan not in mapping_bilan_LCR_NSFR:
        raise ValueError(f"Poste '{post_bilan}' non trouvé dans le mapping.")

    for row_str, feuille in mapping_bilan_LCR_NSFR[post_bilan]:
        if row_str == "row_X":
            continue  # ignorer les lignes non mappées
        try:
            row_number = int(row_str.replace("row_", ""))
        except ValueError:
            continue  # ignorer les erreurs de conversion de ligne

        # Utilisation de noms de DataFrame au lieu des codes de feuille
        if feuille in ["df_72","df_73","df_74"] :
            df_name = feuille
        else:
            continue  # feuille non reconnue

        result.append((row_number, df_name))

    return result



def propager_delta_vers_COREP_LCR(poste_bilan, delta, df_72, df_73, df_74, ponderations=None):
    lignes = get_mapping_df_row(poste_bilan)
    n = len(lignes)
    
    if n == 0:
        return df_72, df_73, df_74

    if ponderations is None:
        ponderations = [1 / n] * n  # Equal weighting by default

    for (row_num, df_name), poids in zip(lignes, ponderations):
        part_delta = delta * poids
        if df_name == "df_72":
            mask = df_72["row"] == row_num
            df_72.loc[mask, "0010"] = df_72.loc[mask, "0010"] - part_delta
        elif df_name == "df_73":
            mask = df_73["row"] == row_num
            df_73.loc[mask, "0010"] = df_73.loc[mask, "0010"] - part_delta
        elif df_name == "df_74":
            mask = df_74["row"] == row_num
            df_74.loc[mask, "0010"] = df_74.loc[mask, "0010"] - part_delta

    return df_72, df_73, df_74

def propager_delta_vers_COREP_NSFR(poste_bilan, delta, df_80, df_81, ponderations=None):
    lignes = get_mapping_df_row(poste_bilan)
    n = len(lignes)
    
    if n == 0:
        return df_80, df_81

    if ponderations is None:
        ponderations = [1 / n] * n  # Equal weighting by default

    for (row_num, df_name), poids in zip(lignes, ponderations):
        part_delta = delta * poids
        if df_name == "df_80":
            mask = df_80["row"] == row_num
            df_80.loc[mask, "0010"] = df_80.loc[mask, "0010"] - part_delta
        elif df_name == "df_81":
            mask = df_81["row"] == row_num
            df_81.loc[mask, "0010"] = df_81.loc[mask, "0010"] - part_delta
        

    return df_80, df_81

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


