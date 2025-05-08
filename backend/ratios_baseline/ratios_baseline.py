import os
import pandas as pd
from backend.stress_test import event1 as bst
from backend.stress_test.event1 import get_mapping_df_row



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
    return 0



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



from backend.lcr.feuille_72 import calcul_HQLA
from backend.lcr.feuille_73 import calcul_outflow
from backend.lcr.feuille_74 import calcul_inflow
from backend.lcr.utils import Calcul_LCR

from backend.nsfr.feuille_80 import calcul_RSF
from backend.nsfr.feuille_81 import calcul_ASF
from backend.nsfr.utils import Calcul_NSFR



def calcul_ratios_projete(annee, bilan, df_72, df_73, df_74, df_80, df_81):
    posts = ["Caisse Banque Centrale / nostro","Créances banques autres","Créances clientèle (hors hypo)","Portefeuille","Immobilisations et Autres Actifs","Dettes envers les établissements de crédit (passif)","Depots clients (passif)","Autres passifs (passif)","Income Statement - Résultat de l'exercice"]
    for poste_bilan in posts:
        print("poste_bilan", poste_bilan)

        delta = get_capital_planning(bilan, poste_bilan, annee)
        print("delta", delta)

        # Propagation vers les feuilles LCR
        df_72, df_73, df_74 = bst.propager_delta_vers_COREP_LCR(poste_bilan, delta, df_72, df_73, df_74)

        # Propagation vers les feuilles NSFR
        df_80, df_81 = bst.propager_delta_vers_COREP_NSFR(poste_bilan, delta, df_80, df_81)

    # Calcul des ratios
    HQLA = calcul_HQLA(df_72)
    OUTFLOWS = calcul_outflow(df_73)
    INFLOWS = calcul_inflow(df_74)
    LCR = Calcul_LCR(INFLOWS, OUTFLOWS, HQLA)

    ASF = calcul_ASF(df_81)
    RSF = calcul_RSF(df_80)
    NSFR = Calcul_NSFR(ASF, RSF)

    return {
        "LCR": LCR,
        "NSFR": NSFR,
        "HQLA": HQLA,
        "OUTFLOWS": OUTFLOWS,
        "INFLOWS": INFLOWS,
        "ASF": ASF,
        "RSF": RSF,
        "df_72": df_72,
        "df_73": df_73,
        "df_74": df_74,
        "df_80": df_80,
        "df_81": df_81
    }
def calcul_ratios_sur_horizon(horizon, bilan, df_72, df_73, df_74, df_80, df_81):
    resultats = {}

    for annee in range(2024, 2024 + horizon + 1):
        # Cloner les feuilles pour ne pas propager les changements d'une année à l'autre
        df72_copy = df_72.copy()
        df73_copy = df_73.copy()
        df74_copy = df_74.copy()
        df80_copy = df_80.copy()
        df81_copy = df_81.copy()

        ratios = calcul_ratios_projete(
            annee=str(annee),
            bilan=bilan,
            df_72=df72_copy,
            df_73=df73_copy,
            df_74=df74_copy,
            df_80=df80_copy,
            df_81=df81_copy
        )

        resultats[annee] = ratios

    return resultats
