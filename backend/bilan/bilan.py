import os
import pandas as pd
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

#Récupérer la valeur de capital planning
def get_capital_planning(bilan_df, poste_bilan, annee="2025"):
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index

    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                return valeur
    return None

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
        ("row_0030", "df_73"),  ## retail deposits
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


def add_capital_planning_df(df, row_number, value_to_add):
    if 'row' not in df.columns:
        print("⚠️ Colonne 'row' introuvable dans le DataFrame.")
        return df

    row_index = df[df['row'] == row_number].index
    if row_index.empty:
        print(f"⚠️ Ligne avec 'row' == {row_number} non trouvée.")
        return df
    
    idx = row_index[0]
    current_value = df.at[idx, '0010']
    df.at[idx, '0010'] = (current_value if pd.notnull(current_value) else 0) + value_to_add
    return df


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

        if feuille == "C72.00":
            df_name = "df_72"
        elif feuille == "C73.00":
            df_name = "df_73"
        elif feuille == "C74.00":
            df_name = "df_74"
        else:
            continue  # feuille non reconnue

        result.append((row_number, df_name))

    return result



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


def appliquer_stress_retrait_depots(bilan_df, p1, p2=1, p3='equitable', annee="2025",
                                    poids_portefeuille=0.5, poids_creances=0.5):
    bilan_df = bilan_df.copy()

    poste_depots = "Depots clients (passif)"
    poste_portefeuille = "Portefeuille"
    poste_creances = "Créances banques autres"

    valeur_depots = get_valeur_poste_bilan(bilan_df, poste_depots, annee)
    if valeur_depots is None:
        raise ValueError(f"Poste '{poste_depots}' non trouvé ou valeur manquante pour {annee}.")

    choc_total = valeur_depots * p1
    choc_annuel = choc_total / p2 if p3 == 'equitable' and p2 > 1 else choc_total

    for i in range(p2):
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

# Utilisation :
#postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
#bilan_filtré = afficher_postes_concernes(bilan_stresse, postes_concernes)

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

def propager_delta_vers_COREP(poste_bilan, delta, df_72, df_73, df_74, ponderations=None):
    """
    Répartit un delta sur les lignes COREP liées à un poste du bilan.

    Args:
        poste_bilan (str): Nom du poste du bilan.
        delta (float): Montant total à répartir.
        df_72, df_73, df_74 (DataFrame): Feuilles COREP.
        ponderations (List[float], optional): Liste des poids associés à chaque ligne COREP.
                                               Si None, la répartition est équitable.

    Returns:
        Tuple des DataFrames mis à jour : (df_72, df_73, df_74).
    """
    lignes = get_mapping_df_row(poste_bilan)
    n = len(lignes)
    ponderations = [0]*n
    if n == 0:
        return df_72, df_73, df_74  # Rien à faire

    if ponderations is None:
        ponderations = [1 / n] * n
    elif len(ponderations) != n:
        raise ValueError("Le nombre de pondérations doit correspondre au nombre de lignes COREP. n= ",n)

    for (row_num, df_name), poids in zip(lignes, ponderations):
        part_delta = delta * poids
        if df_name == "df_72":
            df_72.loc[df_72["row"] == row_num, "0010"] -= part_delta
        elif df_name == "df_73":
            df_73.loc[df_73["row"] == row_num, "0010"] -= part_delta
        elif df_name == "df_74":
            df_74.loc[df_74["row"] == row_num, "0010"] -= part_delta

    return df_72, df_73, df_74


def sauvegarder_bilan_stresse(bilan_stresse, output_filename="bilan_stresse.xlsx", output_dir="data"):
    """
    Sauvegarde le bilan stressé dans un fichier Excel.

    Args:
        bilan_stresse (DataFrame): Le DataFrame contenant le bilan stressé.
        output_filename (str): Nom du fichier de sortie (par défaut "bilan_stresse.xlsx").
        output_dir (str): Dossier où enregistrer le fichier (par défaut "data").
    """
    # Créer le dossier s’il n’existe pas
    os.makedirs(output_dir, exist_ok=True)

    # Chemin de sauvegarde
    output_path = os.path.join(output_dir, output_filename)

    # Sauvegarde Excel
    bilan_stresse.to_excel(output_path, index=False)

    print(f"✅ Bilan stressé sauvegardé dans : {output_path}")



def sauvegarder_corep_modifie(original_path, df_72, df_73, df_74, output_filename="LCR_stresse.xlsx", output_dir="data"):
    """
    Crée une copie du fichier COREP original et remplace les feuilles C72.00, C73.00 et C74.00 par les DataFrames modifiés.

    Args:
        original_path (str): Chemin du fichier Excel original (ex. "LCR.xlsx").
        df_72, df_73, df_74 (DataFrame): Données modifiées.
        output_filename (str): Nom du fichier de sortie (par défaut "LCR_stresse.xlsx").
        output_dir (str): Dossier où enregistrer le fichier (par défaut "data").
    """
    # Créer le dossier s’il n’existe pas
    os.makedirs(output_dir, exist_ok=True)

    # Chemin du nouveau fichier
    output_path = os.path.join(output_dir, output_filename)

    # Copier le fichier original vers le nouveau chemin
    shutil.copyfile(original_path, output_path)

    # Charger le fichier copié
    with pd.ExcelWriter(output_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_72.to_excel(writer, sheet_name="C7200_TOTAL", index=False)
        df_73.to_excel(writer, sheet_name="C7300_TOTAL", index=False)
        df_74.to_excel(writer, sheet_name="C7400_TOTAL", index=False)

    print(f"✅ Nouveau fichier COREP sauvegardé dans : {output_path}")

#sauvegarder_corep_modifie(file_path, df_72, df_73, df_74, output_filename="LCR_stresse.xlsx", output_dir="data")
#sauvegarder_bilan_stresse(bilan_stresse, output_filename="bilan_stresse.xlsx", output_dir="data")