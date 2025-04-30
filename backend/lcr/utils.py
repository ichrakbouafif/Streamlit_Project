import pandas as pd

def extraire_lignes_non_vides(df, colonne_montant='0010'):
    if colonne_montant in df.columns:
        return df[df[colonne_montant].fillna(0) != 0]
    return pd.DataFrame()

def affiche_LB_lcr(df):

    # Renommer les colonnes
    df.columns = [
        "Item",                     # Deuxième colonne (Unnamed: 1)
        "Row",                      # Troisième colonne (Unnamed: 2)
        "Montant (0010)",           # Quatrième colonne
        "Standard weight (0020)",   # Cinquième colonne
        "Applicable weight (0030)", # Sixième colonne
        "Valeur (0040)"             # Septième colonne
    ]

    # Appliquer le format 100% au lieu de 1.0 dans "Applicable weight (0030)"
    df["Applicable weight (0030)"] = df["Applicable weight (0030)"].apply(
        lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
    )

    # Convertir la colonne "Valeur (0040)" en float (en supprimant les virgules et caractères non numériques)
    df["Valeur (0040)"] = pd.to_numeric(df["Valeur (0040)"].astype(str).str.replace(",", ""), errors="coerce")

    # Ne garder que les lignes où "Valeur (0040)" est différente de 0
    df = df[df["Valeur (0040)"].fillna(0) != 0]

    # Supprimer la colonne "Standard weight (0020)"
    df.drop(columns=["Standard weight (0020)"], inplace=True)

    return df

def affiche_outflow_lcr(df):

    # Renommer les colonnes
    df.columns = [
        "Item",                     # colonne (Unnamed: 1)
        "Row",                      # colonne (Unnamed: 2)
        "Montant (0010)",           # colonne montant
        "Standard weight (0040)",   # Cinquième colonne
        "Applicable weight (0050)", # Sixième colonne
        "Outflow (0060)"             # Septième colonne
    ]

    # Appliquer le format 100% au lieu de 1.0 dans "Applicable weight (0030)"
    df["Applicable weight (0050)"] = df["Applicable weight (0050)"].apply(
        lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
    )

    # Convertir la colonne "Outflow (0060)" en float (en supprimant les virgules et caractères non numériques)
    df["Outflow (0060)"] = pd.to_numeric(df["Outflow (0060)"].astype(str).str.replace(",", ""), errors="coerce")

    # Ne garder que les lignes où "Outflow (0060)" est différente de 0
    df = df[df["Outflow (0060)"].fillna(0) != 0]

    # Supprimer la colonne "Standard weight (0040)"
    df.drop(columns=["Standard weight (0040)"], inplace=True)

    return df

def affiche_inflow_lcr(df):

    # Renommer les colonnes
    df.columns = [
        "Item",                     #  colonne (Unnamed: 1)
        "Row",                      #  colonne (Unnamed: 2)
        "Montant (0010)",           #  colonne
        "Standard weight (0070)",   # Cinquième colonne
        "Applicable weight (0080)", # Sixième colonne
        "Inflow (0140)"             # Septième colonne
    ]

    # Appliquer le format 100% au lieu de 1.0 dans "Applicable weight (0030)"
    df["Applicable weight (0080)"] = df["Applicable weight (0080)"].apply(
        lambda x: f"{int(float(x)*100)}%" if pd.notnull(x) and x != 'None' else ""
    )

    # Convertir la colonne "Inflow (0140)" en float (en supprimant les virgules et caractères non numériques)
    df["Inflow (0140)"] = pd.to_numeric(df["Inflow (0140)"].astype(str).str.replace(",", ""), errors="coerce")

    # Ne garder que les lignes où "Inflow (0140)" est différente de 0
    df = df[df["Inflow (0140)"].fillna(0) != 0]

    # Supprimer la colonne "Standard weight (0070)"
    df.drop(columns=["Standard weight (0070)"], inplace=True)

    return df
import os
import pandas as pd
from backend.lcr.feuille_72 import calcul_HQLA
from backend.lcr.feuille_73 import calcul_outflow
from backend.lcr.feuille_74 import calcul_inflow
from backend.lcr.feuille_72 import charger_feuille_72
from backend.lcr.feuille_73 import charger_feuille_73
from backend.lcr.feuille_74 import charger_feuille_74

path = os.path.join("data", "LCR.csv")
df_72 = charger_feuille_72(path)
df_73 = charger_feuille_73(path)
df_74 = charger_feuille_74(path)

HQLA = calcul_HQLA(df_72)
OUTFLOWS = calcul_outflow(df_73)
inflows = calcul_inflow(df_74)

def Calcul_LCR(inflow,OUTFLOWS,HQLA):

    # Limiter les inflows à 75% des outflows
    inflow_limit = min(inflow, 0.75 * OUTFLOWS)

    # Sorties nettes ajustées
    net_outflows = OUTFLOWS - inflow_limit

    # Calcul du LCR
    if net_outflows == 0:
        return float('inf') if HQLA > 0 else 0.0  # éviter division par zéro

    lcr = (HQLA / net_outflows)*100
    print("LCR=",lcr,"%")
    return lcr

