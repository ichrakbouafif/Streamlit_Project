import pandas as pd

def extraire_lignes_non_vides(df, colonne_montant='0010'):
    if colonne_montant in df.columns:
        return df[df[colonne_montant].fillna(0) != 0]
    return pd.DataFrame()

def affiche_LB_lcr(df):
    df = df.copy()
    # Renommer les colonnes
    df.columns = [
        "Item",                     # Deuxième colonne (Unnamed: 1)
        "row",                      # Troisième colonne (Unnamed: 2)
        "Montant (0010)",           # Quatrième colonne
        "Standard weight (0020)",   # Cinquième colonne
        "Applicable weight (0030)", # Sixième colonne
        "Valeur (0040)"             # Septième colonne
    ]

    df['row'] = df['row'].apply(lambda x: f"{int(x):04d}" if pd.notna(x) else "")
    # Appliquer le format 100% au lieu de 1.0 dans "Applicable weight (0030)"
    df["Applicable weight (0030)"] = df["Applicable weight (0030)"].apply(
        lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
    )

    # Convertir la colonne "Valeur (0040)" en float (en supprimant les virgules et caractères non numériques)
    df["Valeur (0040)"] = pd.to_numeric(df["Valeur (0040)"].astype(str).str.replace(",", " "), errors="coerce")
    
    # Formater les nombres avec séparateur de milliers et 2 décimales
    df["Valeur (0040)"] = df["Valeur (0040)"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )
    df["Montant (0010)"] = df["Montant (0010)"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )

    # Ne garder que les lignes où "Valeur (0040)" est différente de 0
    df = df[df["Valeur (0040)"].fillna(0) != 0]

    # Supprimer la colonne "Standard weight (0020)"
    df = df.drop(columns=["Standard weight (0020)"])
    #df = df.set_index("row")
    return df

def affiche_outflow_lcr(df):
    import pandas as pd
    df = df.copy()

    # Ne garder que les 6 premières colonnes
    df = df.iloc[:, :6]

    # Renommer les colonnes
    df.columns = [
        "Item",                     # 1ère colonne
        "row",                      # 2ème colonne
        "Montant (0010)",           # 3ème colonne
        "Standard weight (0040)",   # 4ème colonne
        "Applicable weight (0050)", # 5ème colonne
        "Outflow (0060)"            # 6ème colonne
    ]
    df['row'] = df['row'].apply(lambda x: f"{int(x):04d}" if pd.notna(x) else "")

    # Appliquer le format 100% au lieu de 1.0 dans "Applicable weight (0050)"
    df["Applicable weight (0050)"] = df["Applicable weight (0050)"].apply(
        lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
    )

    # Convertir "Outflow (0060)" en float
    df["Outflow (0060)"] = pd.to_numeric(
        df["Outflow (0060)"].astype(str).str.replace(",", " "), errors="coerce"
    )
    
    # Formater les nombres avec séparateur de milliers et 2 décimales
    df["Montant (0010)"] = df["Montant (0010)"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )
    df["Outflow (0060)"] = df["Outflow (0060)"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )

    # Filtrer les lignes où Outflow != 0
    df = df[df["Outflow (0060)"].fillna(0) != 0]

    # Supprimer la colonne inutile
    df = df.drop(columns=["Standard weight (0040)"])
    #df = df.set_index("row")
    return df


def affiche_inflow_lcr(df):
    df = df.copy()
    # Renommer les colonnes
    df.columns = [
        "Item",                     #  colonne (Unnamed: 1)
        "row",                      #  colonne (Unnamed: 2)
        "Montant (0010)",           #  colonne
        "Standard weight (0070)",   # Cinquième colonne
        "Applicable weight (0080)", # Sixième colonne
        "Inflow (0140)"             # Septième colonne
    ]
    df['row'] = df['row'].apply(lambda x: f"{int(x):04d}" if pd.notna(x) else "")

    # Appliquer le format 100% au lieu de 1.0 dans "Applicable weight (0030)"
    df["Applicable weight (0080)"] = df["Applicable weight (0080)"].apply(
        lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
    )

    # Convertir la colonne "Inflow (0140)" en float (en supprimant les virgules et caractères non numériques)
    df["Inflow (0140)"] = pd.to_numeric(df["Inflow (0140)"].astype(str).str.replace(",", " "), errors="coerce")
    
    # Formater les nombres avec séparateur de milliers et 2 décimales
    df["Inflow (0140)"] = df["Inflow (0140)"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )
    df["Montant (0010)"] = df["Montant (0010)"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )


    # Ne garder que les lignes où "Inflow (0140)" est différente de 0
    df = df[df["Inflow (0140)"].fillna(0) != 0]

    # Supprimer la colonne "Standard weight (0070)"
    df = df.drop(columns=["Standard weight (0070)"])
    #df = df.set_index("row")

    return df

import os
import pandas as pd

from backend.lcr.feuille_72 import charger_feuille_72
from backend.lcr.feuille_73 import charger_feuille_73
from backend.lcr.feuille_74 import charger_feuille_74

path = os.path.join("data", "LCR.csv")
df_72 = charger_feuille_72(path)
df_73 = charger_feuille_73(path)
df_74 = charger_feuille_74(path)


def Calcul_LCR(inflow,OUTFLOWS,HQLA):

    # Limiter les inflows à 75% des outflows
    inflow_limit = min(inflow, 0.75 * OUTFLOWS)

    # Sorties nettes ajustées
    net_outflows = OUTFLOWS - inflow_limit

    # Calcul du LCR
    if net_outflows == 0:
        return float('inf') if HQLA > 0 else 0.0  # éviter division par zéro

    lcr = (HQLA / net_outflows)
    #print("LCR=",lcr,"%")
    return lcr

