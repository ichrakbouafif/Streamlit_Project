import os
import pandas as pd
import shutil
from backend.stress_test.event1 import ajuster_annees_suivantes,get_valeur_poste_bilan


def part_loans_mb_outflow(df_73, bilan, annee="2024"):
    try:
        valeur_outflow_mb = df_73.loc[df_73['row'] == 230]['0010'].values[0]
        print("valeur_outflow_mb = ", valeur_outflow_mb)
        dette_etab_credit = get_valeur_poste_bilan(bilan, "Dettes envers les établissements de crédit (passif)", annee)
        print("dette_etab_credit = ", dette_etab_credit)
        return round((valeur_outflow_mb / dette_etab_credit) * 100, 2) if dette_etab_credit else 0.0
    except Exception as e:
        print(f"[Erreur part_loans_mb_outflow] : {e}")
        return 0.0

def part_credit_clientele_inflow(df_74, bilan, annee="2024"):
    try:
        valeur_inflow_credit = df_74.loc[df_74['row'] == 50]['0010'].values[0]
        print("valeur_inflow_credit = ", valeur_inflow_credit)
        creance_clientele = get_valeur_poste_bilan(bilan, "Créances clientèle", annee)
        print("creance_clientele = ", creance_clientele)
        return round((valeur_inflow_credit / creance_clientele) * 100, 2) if creance_clientele else 0.0
    except Exception as e:
        print(f"[Erreur part_credit_clientele_inflow] : {e}")
        return 0.0

def part_depots_mb_inflow(df_74, bilan, annee="2024"):
    try:
        valeur_inflow_mb = df_74.loc[df_74['row'] == 160]['0010'].values[0]
        print("valeur_inflow_mb = ", valeur_inflow_mb)
        creance_banques = get_valeur_poste_bilan(bilan, "Créances banques autres", annee)
        print("creance_banques = ", creance_banques)
        return round((valeur_inflow_mb / creance_banques) * 100, 2) if creance_banques else 0.0
    except Exception as e:
        print(f"[Erreur part_depots_mb_inflow] : {e}")
        return 0.0


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


def propager_impact_vers_df74(df_74, bilan_df, annee="2024", pourcentage=0.1, horizon=3):
    """
    Propage l'impact du tirage PNU vers df_74 pour les lignes :
    - row 160 : + Part Dépôts MB (Inflow) * capital planning créances banques autres
    - row 50  : + Part Crédits Clientèle (Inflow) * capital planning créances clientèle + tirage_total
    """
    df_74 = df_74.copy()
    
    # Étape 1 : calcul des parts (toujours sur l’année 2024)
    part_mb = part_depots_mb_inflow(df_74, bilan_df, "2024")
    print(f"Part Dépôts MB (Inflow) : {part_mb}")
    part_credit = part_credit_clientele_inflow(df_74, bilan_df, "2024")
    print(f"Part Crédits Clientèle (Inflow) : {part_credit}")

    # Étape 2 : tirage total
    poste_engagements = "Engagements de garantie donnés"
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, annee)
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_engagements}' introuvable pour {annee}")

    tirage_total = (valeur_initiale * pourcentage) / horizon
    print(f"Tirage total = {tirage_total}")

    # Étape 3 : capital plannings
    capital_creances = get_capital_planning(bilan_df, "Créances clientèle", annee="2025")
    capital_banques = get_capital_planning(bilan_df, "Créances banques autres", annee="2025")
    print(f"Capital créances : {capital_creances}")
    print(f"Capital banques : {capital_banques}")

    # Étape 4 : application de l’impact pour chaque année cible
    

    impact_160 = (part_mb / 100) * capital_banques
    impact_50 = (part_credit / 100) * (capital_creances + tirage_total)

        # Appliquer impact ligne 160
    mask_160 = df_74["row"] == 160
    df_74.loc[mask_160, "0010"] = df_74.loc[mask_160, "0010"] + impact_160

        # Appliquer impact ligne 50
    mask_50 = df_74["row"] == 50
    df_74.loc[mask_50, "0010"] = df_74.loc[mask_50, "0010"] + impact_50

    return df_74


def propager_impact_vers_df73(df_73, bilan_df, pourcentage=0.1, horizon=3, annee="2024",
                               poids_dettes=0.85, poids_portefeuille=0.15):
    df_73 = df_73.copy()

    # Constantes
    poste_engagements = "Engagements de garantie donnés"
    poste_dettes = "Dettes envers les établissements de crédit (passif)"
    poste_retail = "Dont Retail"
    poste_hypo = "Dont Hypothécaires"
    poste_corpo = "Dont Corpo"

    # Valeurs fixes
    part_loans_mb = part_loans_mb_outflow(df_73, bilan_df, annee="2024") / 100
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, annee)
    tirage_total = (valeur_initiale * pourcentage) / horizon

    # Pour rows 480 et 499
    retail = get_valeur_poste_bilan(bilan_df, poste_retail, annee)
    hypo = get_valeur_poste_bilan(bilan_df, poste_hypo, annee)
    corpo = get_valeur_poste_bilan(bilan_df, poste_corpo, annee)

    # Impact dettes annuel
    impact_annuel_dettes = tirage_total * poids_dettes
    capital_dette = get_capital_planning(bilan_df, poste_dettes, annee="2025")

    impact_230 = part_loans_mb * (impact_annuel_dettes + capital_dette)
    impact_480 = - (pourcentage * retail) / horizon
    impact_499 = - ((pourcentage * hypo) + (pourcentage * corpo)) / horizon
    print(f"Impact 499 : {impact_499}")


    df_73.loc[df_73["row"] == 230, "0010"] += impact_230
    df_73.loc[df_73["row"] == 480, "0010"] += impact_480
    df_73.loc[df_73["row"] == 490, "0010"] += impact_499

    return df_73
