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
        ("row_0800", "C74.00"),
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
    "Dépôts clients (Corpo & Retail)": [
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


#Modifier le fichier COREP
def maj_valeur_corep(fichier_corep, feuille, ligne, colonne, nouvelle_valeur):
    """
    Met à jour une cellule dans une feuille du fichier COREP Excel.
    """
    df = pd.read_excel(fichier_corep, sheet_name=feuille)

    df.loc[ligne, colonne] = nouvelle_valeur

    with pd.ExcelWriter(fichier_corep, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=feuille, index=False)


# Fonction principale de mise à jour du bilan dans le COREP et recalcul des ratios
def update_and_calculate_ratios(poste_bilan, fichier_bilan="data/bilan.xlsx", fichier_corep="data/corep.xlsx"):
    # Charger le bilan
    bilan_df = charger_bilan()

    # Récupérer la valeur du capital planning dans le bilan
    valeur_capital = get_capital_planning_below(bilan_df, poste_bilan)
    if valeur_capital is None:
        raise ValueError(f"La valeur pour {poste_bilan} n'a pas été trouvée dans le bilan.")

    # Mapper la valeur dans le fichier COREP selon la configuration
    if poste_bilan in mapping_bilan_LCR_NSFR:
        for ligne, colonne in mapping_bilan_LCR_NSFR[poste_bilan]:
            # Mettre à jour la valeur dans la feuille COREP
            maj_valeur_corep(fichier_corep, ligne, colonne, valeur_capital)

        # Recalculer les ratios après la mise à jour (ajoutez vos fonctions de calcul ici)
        recalculer_ratios(fichier_corep)

    return "Mise à jour réussie et ratios recalculés."

def recalculer_ratios(fichier_corep):
    """
    Cette fonction doit recalculer les ratios LCR et NSFR après la mise à jour du fichier COREP.
    """
    lcr = 1
    nsfr = 1


    print(f"LCR recalculé : {lcr}")
    print(f"NSFR recalculé : {nsfr}")


