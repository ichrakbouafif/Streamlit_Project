import os
import pandas as pd
import shutil
from backend.stress_test.event1 import ajuster_annees_suivantes,get_valeur_poste_bilan

def get_capital_planning(bilan_df, poste_bilan, annee="2025"):
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index

    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                return valeur
    return 0

def appliquer_tirage_pnu(bilan_df, pourcentage, horizon=3, annee="2024",
                         poids_portefeuille=0.15, poids_dettes=0.85):
    """
    Applique l'impact du tirage PNU sur les postes bilantiels :
    - diminue les engagements de garanties données
    - augmente les dettes envers établissements de crédit
    - diminue le portefeuille
    """

    bilan_df = bilan_df.copy()
    
    poste_engagements = "Engagements de garantie donnés"
    poste_portefeuille = "Portefeuille"
    poste_dettes = "Dettes envers les établissements de crédit (passif)"
    poste_creances = "Créances clientèle"


    # Étape 1 : récupérer la valeur initiale du poste engagements
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, annee)
    print(f"Valeur initiale pour {poste_engagements} en {annee} : {valeur_initiale}")
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_engagements}' introuvable ou sans valeur pour {annee}.")

    tirage_total = (valeur_initiale * pourcentage) / horizon
    print(f"Tirage total : {tirage_total}")

    for i in range(horizon):
        annee_cible = str(int(annee) + i+1)

        # Augmentation des créances clientèle (nouveau)
        impact_creances = tirage_total 
        idx_creances = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_creances].index[0]
        bilan_df.loc[idx_creances, annee_cible] += impact_creances
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_creances, annee_cible, -impact_creances)

        # Réduction des engagements de garanties données
        idx_eng = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_engagements].index[0]
        bilan_df.loc[idx_eng, annee_cible] -= tirage_total
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_engagements, annee_cible, tirage_total)

        # Diminution du portefeuille
        impact_portefeuille = tirage_total * poids_portefeuille
        idx_port = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_portefeuille].index[0]
        bilan_df.loc[idx_port, annee_cible] -= impact_portefeuille
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_portefeuille, annee_cible, impact_portefeuille)

        # Augmentation des dettes envers établissements de crédit
        impact_dettes = tirage_total * poids_dettes
        idx_dettes = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_dettes].index[0]
        bilan_df.loc[idx_dettes, annee_cible] += impact_dettes
        bilan_df = ajuster_annees_suivantes(bilan_df, poste_dettes, annee_cible, -impact_dettes) 

    return bilan_df


mapping_bilan_LCR_NSFR_E2 = {
    "Créances clientèle": [
        ("row_0050", "df_74"),  # Inflow – Monies from retail customers
    ],
    "Portefeuille": [
        ("row_0070", "df_72"),  
        ("row_0820", "df_80"), 
        ("row_1060", "df_80"), 
    ],
    "Dettes envers les établissements de crédit (passif)": [
        ("row_0230", "df_73"), # outflow 
        ("row_0250", "df_73"), # outflow 
        ("row_0260", "df_73"), # outflow 
        ("row_0480", "df_73"), # outflow 
        ("row_0490", "df_73"), # outflow 
        ("row_0300", "df_81"), # ASF from finantial cus and central banks - liabilities provided by finantial customers
    ],
}

def propager_impact_portefeuille_vers_df72(df_72, bilan_df, annee="2024", pourcentage=0.1, horizon=3, poids_portefeuille=0.15):
    """
    Propagation de l'impact du portefeuille vers la ligne row_0070 de df_72 suite au tirage PNU.
    On applique : row_0070 = row_0070 - impact_portefeuille
    """
    df_72 = df_72.copy()
    
    poste_engagements = "Engagements de garantie donnés"

    # Récupérer la valeur initiale du poste engagements
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, annee)
    print(f"Valeur initiale pour {poste_engagements} en {annee} : {valeur_initiale}")
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_engagements}' introuvable ou sans valeur pour {annee}.")

    tirage_total = (valeur_initiale * pourcentage) / horizon
    print(f"Tirage total : {tirage_total}")

    impact_portefeuille = tirage_total * poids_portefeuille

        # Mettre à jour la ligne 'row_0070' dans df_72
    mask = df_72["row"] == 70
    df_72.loc[mask, "0010"] = df_72.loc[mask, "0010"] - impact_portefeuille

    return df_72
