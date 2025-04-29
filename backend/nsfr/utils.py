import pandas as pd

def extraire_lignes_non_vides(df, colonne_montant='0010'):
    if colonne_montant in df.columns:
        return df[df[colonne_montant].fillna(0) != 0]
    return pd.DataFrame()

import pandas as pd

def affiche_RSF(df):
    # Renommer les colonnes
    df.columns = [
        "Item",                     # colonne (Unnamed: 1)
        "Row",                      # colonne (Unnamed: 2)
        "Montant < 6 mois (0010)",  
        "Montant >= 6 mois < 1an (0020)",  
        "Montant > 1an (0030)",  
        "HQLA (0040)",  
        "Applicable RSF factor < 6 mois (0090)",   
        "Applicable RSF factor >= 6 mois < 1an (0100)",
        "Applicable RSF factor > 1an (0110)",   
        "Applicable RSF factor HQLA (0120)",
        "RSF (0130)"
    ]

    # Ne garder que les lignes où "RSF (0130)" est différente de 0
    df = df[df["RSF (0130)"].fillna(0) != 0]

    # Appliquer le format pourcentage sur les colonnes des "Applicable RSF factor"
    cols_rsf_factors = [
        "Applicable RSF factor < 6 mois (0090)",
        "Applicable RSF factor >= 6 mois < 1an (0100)",
        "Applicable RSF factor > 1an (0110)",
        "Applicable RSF factor HQLA (0120)"
    ]
    
    for col in cols_rsf_factors:
        df[col] = df[col].apply(
            lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
        )

    return df

def affiche_ASF(df):
    # Renommer les colonnes (sans HQLA)
    df.columns = [
        "Item",                     
        "Row",                      
        "Montant < 6 mois (0010)",  
        "Montant >= 6 mois < 1an (0020)",  
        "Montant > 1an (0030)",  
        "Applicable ASF factor < 6 mois (0070)",   
        "Applicable ASF factor >= 6 mois < 1an (0080)",
        "Applicable ASF factor > 1an (0090)",   
        "ASF (0100)"
    ]
    # Ne garder que les lignes où "ASF (0100)" est différente de 0
    df = df[df["ASF (0100)"].fillna(0) != 0]
    # Appliquer le format pourcentage sur les colonnes des "Applicable ASF factor"
    cols_asf_factors = [
        "Applicable ASF factor < 6 mois (0070)",
        "Applicable ASF factor >= 6 mois < 1an (0080)",
        "Applicable ASF factor > 1an (0090)"
    ]
    
    for col in cols_asf_factors:
        df[col] = df[col].apply(
            lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
        )

    return df
