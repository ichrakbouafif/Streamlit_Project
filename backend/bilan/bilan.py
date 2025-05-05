import os
import pandas as pd

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


# fichier: mapping_bilan_corep.py
mapping_bilan_LCR_NSFR = {
    "Caisse Banque Centrale / nostro": [
        ("row_0040", "C72.00"),  # LB: Coins and banknotes
        ("row_0050", "C72.00"),  # LB: Withdrawable central bank reserves
        ("row_0150", "C72.00"),  # Inflow: Monies due from central banks
        ("row_0030", "C74.00"),  # NSFR: Central bank assets
    ],
    "Créances banques autres": [
        ("row_0060", "C72.00"),  # LB: Central bank assets
        ("row_0160", "C72.00"),  # Inflow: Monies due from financial customers
        ("row_0100", "C72.00"),  # Inflow: Monies due from CB + financial customers
        ("row_0730", "C74.00"),  # NSFR: RSF from loans to financial customers
    ],
    "Créances hypothécaires": [
        ("row_0030", "C72.00"),  # Inflow – à ajuster selon contrepartie
        ("row_0800", "C74.00"),  # NSFR
        ("row_0810", "C74.00"),
    ],
    "Créances clientèle (hors hypo)": [
        ("row_0030", "C72.00"),
        ("row_0060", "C72.00"),
        ("row_0070", "C72.00"),
        ("row_0080", "C72.00"),
        ("row_0090", "C72.00"),
    ],
    "Portefeuille (titres)": [
        ("row_0190", "C72.00"),
        ("row_0260", "C72.00"),
        ("row_0280", "C72.00"),
        ("row_0310", "C72.00"),
        ("row_0470", "C72.00"),
        ("row_0560", "C74.00"),
        ("row_0570", "C74.00"),
    ],
    "Participations": [
        ("row_X", "C72.00"),  # Non considéré LCR
        ("row_0600", "C74.00"),  # NSFR
    ],
    "Immobilisations et Autres Actifs": [
        ("row_X", "C72.00"),  # Non considéré LCR
        ("row_1030", "C74.00"),
    ],
    "Dettes envers les établissements de crédit": [
        ("row_0230", "C73.00"),
        ("row_1350", "C73.00"),
        ("row_0270", "C74.00"),
    ],
    "Depots clients (passif)": [
        ("row_0030", "C73.00"),
        ("row_0110", "C73.00"),
        ("row_0240", "C73.00"),
        ("row_0250", "C73.00"),
        ("row_0260", "C73.00"),
        ("row_0070", "C74.00"),
        ("row_0130", "C74.00"),
        ("row_0200", "C74.00"),
    ],
    "Autres passifs": [
        ("row_0885", "C73.00"),
        ("row_0918", "C73.00"),
        ("row_0390", "C74.00"),
    ],
    "Comptes de régularisation": [
        ("row_0890", "C73.00"),
        ("row_0390", "C74.00"),
        ("row_0430", "C74.00"),
    ],
    "Provisions": [
        ("row_X", "C73.00"),
        ("row_0430", "C74.00"),
    ],
    "Capital souscrit": [
        ("row_0030", "C74.00"),
    ],
    "Primes émission": [
        ("row_0030", "C74.00"),
    ],
    "Réserves": [
        ("row_0030", "C74.00"),
    ],
    "Report à nouveau": [
        ("row_0030", "C74.00"),
    ],
    "Résultat de l'exercice": [
        ("row_0030", "C74.00"),
    ],
}

""" def add_capital_planning_df(df, row_number, value_to_add):

    # Si row_number est une chaîne, essayer de l'interpréter comme un index de ligne.
    if isinstance(row_number, str):
        # Vérifier si la chaîne correspond à un format comme "row_150" et extraire le numéro.
        if row_number.startswith("row_"):
            row_number = int(row_number.replace("row_", ""))
        else:
            raise ValueError(f"Format de row_number invalide: {row_number}")

    # Vérification que la colonne '0010' existe
    if '0010' not in df.columns:
        raise ValueError("La colonne '0010' n'existe pas dans le DataFrame.")
    
    # Vérifier que row_number ne dépasse pas la taille du DataFrame
    if row_number < 0 or row_number >= len(df):
        print(f"Avertissement: row_number {row_number} hors des limites du DataFrame. Taille actuelle: {len(df)}")
        return df  # Ne rien ajouter et renvoyer le DataFrame inchangé.
    
    # Ajouter la valeur à la ligne spécifiée
    current_value = df.at[row_number, '0010']
    current_value = current_value if pd.notnull(current_value) else 0
    df.at[row_number, '0010'] = current_value + value_to_add

    return df """

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
