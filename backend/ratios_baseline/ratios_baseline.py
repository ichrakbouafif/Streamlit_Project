import os
import pandas as pd
import streamlit as st
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

# Supprime les lignes où Poste du Bilan est vide ET 2025 = 0
    mask = (bilan["Poste du Bilan"].notna()) | (bilan["2025"] != 0)
    bilan = bilan[mask].reset_index(drop=True)
    #bilan = bilan.dropna(how="all").reset_index(drop=True)
    
    return bilan

#Récupérer la valeur de capital planning
""" def get_capital_planning(bilan_df, poste_bilan, annee="2025"):
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index

    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                return valeur
    return 0
 """

# Récupérer la valeur de capital planning avec ajustement conditionnel
def get_capital_planning(bilan_df, poste_bilan, annee="2025"):
    bilan_df = bilan_df.reset_index(drop=True)
    poste_bilan_lower = poste_bilan.strip().lower()
    index_poste = bilan_df["Poste du Bilan"].astype(str).str.strip().str.lower() == poste_bilan_lower
    index_poste = bilan_df[index_poste].index

    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                if poste_bilan_lower == "créances clientèle":
                    return 1 * valeur
                elif poste_bilan_lower == "créances banques autres":
                    return 0.28 * valeur
                elif poste_bilan_lower == "depots clients (passif)":
                    #return 0.71 * valeur
                    return valeur
                elif poste_bilan_lower == "dettes envers les établissements de crédit (passif)":
                    return 0.09 * valeur
                else:
                    return valeur
    return 0


def get_mapping_df_row_CP(post_bilan):
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
        if feuille in ["df_72","df_73","df_74","df_80","df_81"]: 
            df_name = feuille
        else:
            continue  # feuille non reconnue

        result.append((row_number, df_name))

    return result

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

mapping_bilan_LCR_NSFR = {
    "Caisse Banque Centrale / nostro": [
        ("row_0050", "df_72"),  # LB: Withdrawable central bank reserves
    ],
    "Créances banques autres": [
        ("row_0160", "df_74"),  # Inflow: Monies due from financial customers
    ],
    "Créances hypothécaires": [
        ("row_X", "df_80"),  # RSF from loans to finantial customers
        
    ],
    "Créances clientèle": [
        ("row_0050", "df_74"),  # Inflow – Monies from retail customers
        ("row_0820", "df_80"), # RSF from loans to non finantial customers 
    ],
    "Portefeuille": [
        ("row_0580", "df_80"),  # RSF from securities other than liquid assets non hqla
    ],
    "Participations": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
    ],
    "Immobilisations et Autres Actifs": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Dettes envers les établissements de crédit (passif)": [
        ("row_0230", "df_73"), # outflow non operational deposits by finantial customers
        ("row_0300", "df_81"), # ASF from finantial cus and central banks - liabilities provided by finantial customers
    ],
    "Depots clients (passif)": [
        ("row_0030", "df_73"), ## outflow not covered by DGS
        ("row_0090", "df_81"), #ASF from retail deposits
        ("row_0110", "df_81"), #ASF from other non finantial customers
        ("row_0130", "df_81"), #ASF from other non finantial customers

    ],
    "Autres passifs (passif)": [
        ("row_X", "df_81"), #ASF from other liabilities
    ],
    "Comptes de régularisation (passif)": [
        #("row_0890", "df_73"), ## outflow other liabilities
        ("row_X", "df_81"), #ASF from other liabilities
    ],
    "Provisions (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Capital souscrit (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Primes émission (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Réserves (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Report à nouveau (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Income Statement - Résultat de l'exercice": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
}

from backend.lcr.feuille_72 import calcul_HQLA
from backend.lcr.feuille_73 import calcul_outflow
from backend.lcr.feuille_74 import calcul_inflow
from backend.lcr.utils import Calcul_LCR

from backend.nsfr.feuille_80 import calcul_RSF
from backend.nsfr.feuille_81 import calcul_ASF
from backend.nsfr.utils import Calcul_NSFR


def propager_CP_vers_COREP_LCR(poste_bilan, delta, df_72, df_73, df_74, ponderations=None):
    lignes = get_mapping_df_row_CP(poste_bilan)
    print("lignes = ", lignes)

    lignes_72 = [l for l in lignes if l[1] == "df_72"]
    lignes_73 = [l for l in lignes if l[1] == "df_73"]
    lignes_74 = [l for l in lignes if l[1] == "df_74"]
    n, m, p = len(lignes_72), len(lignes_73), len(lignes_74)

    print("n (df_72) = ", n)
    print("m (df_73) = ", m)
    print("p (df_74) = ", p)

    if n + m + p == 0:
        return df_72, df_73, df_74

    df_72 = df_72.copy()
    df_73 = df_73.copy()
    df_74 = df_74.copy()

    if ponderations is None:
        ponderations_72 = [1 / n] * n if n > 0 else []
        ponderations_73 = [1 / m] * m if m > 0 else []
        ponderations_74 = [1 / p] * p if p > 0 else []
    else:
        ponderations_72 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_72"]
        ponderations_73 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_73"]
        ponderations_74 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_74"]

    for (row_num, _), poids in zip(lignes_72, ponderations_72):
        part_delta = delta * poids
        print("part delta in df_72 = ", part_delta)
        mask = df_72["row"] == row_num
        df_72.loc[mask, "0010"] = df_72.loc[mask, "0010"] + part_delta

    for (row_num, _), poids in zip(lignes_73, ponderations_73):
        part_delta = delta * poids
        print("part delta in df_73 = ", part_delta)
        mask = df_73["row"] == row_num
        df_73.loc[mask, "0010"] = df_73.loc[mask, "0010"] + part_delta

    for (row_num, _), poids in zip(lignes_74, ponderations_74):
        part_delta = delta * poids
        print("part delta in df_74 = ", part_delta)
        mask = df_74["row"] == row_num
        df_74.loc[mask, "0010"] = df_74.loc[mask, "0010"] + part_delta

    return df_72, df_73, df_74

def calcul_ratios_projete(annee, bilan, df_72, df_73, df_74, df_80, df_81):
    posts = ["Caisse Banque Centrale / nostro","Créances banques autres","Créances clientèle","Portefeuille","Immobilisations et Autres Actifs","Dettes envers les établissements de crédit (passif)","Depots clients (passif)","Autres passifs (passif)","Income Statement - Résultat de l'exercice"]
    for poste_bilan in posts:
        print("poste_bilan", poste_bilan)

        delta = get_capital_planning(bilan, poste_bilan, annee)
        print("delta", delta)

        # Propagation vers les feuilles LCR
        df_72, df_73, df_74 = propager_CP_vers_COREP_LCR(poste_bilan, delta, df_72, df_73, df_74)

        # Propagation vers les feuilles NSFR
        df_80, df_81 = propager_CP_vers_COREP_NSFR(poste_bilan, delta, df_80, df_81)

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
    
    # Initialize with the original data
    current_df72 = df_72.copy()
    current_df73 = df_73.copy()
    current_df74 = df_74.copy()
    current_df80 = df_80.copy()
    current_df81 = df_81.copy()

    for annee in range(2024, 2024 + horizon + 1):
        ratios = calcul_ratios_projete(
            annee=str(annee),
            bilan=bilan,
            df_72=current_df72,
            df_73=current_df73,
            df_74=current_df74,
            df_80=current_df80,
            df_81=current_df81
        )

        resultats[annee] = ratios
        
        # Update the current dataframes with the modified ones for the next iteration
        current_df72 = ratios["df_72"].copy()
        current_df73 = ratios["df_73"].copy()
        current_df74 = ratios["df_74"].copy()
        current_df80 = ratios["df_80"].copy()
        current_df81 = ratios["df_81"].copy()

    return resultats

def extract_rsf_data(user_selections=None):
    # Default data
    data = {
        "Row": ["580", "820"],
        "Rubrique": [
            "non-HQLA securities and exchange traded equities (unencumbered or encumbered < 1 year)",
            "other loans to non-financial customers (unencumbered or encumbered < 1 year)"
        ],
        "Included_in_calculation": ["Yes", "Yes"],
        "Amount_less_than_6M": [76456830, 1398399253],
        "Amount_6M_to_1Y": [30122816, 57733609],
        "Amount_greater_than_1Y": [136894455, 1359266078],
        "RSF_factor_less_than_6M": [0.50, 0.50],
        "RSF_factor_6M_to_1Y": [0.50, 0.50],
        "RSF_factor_greater_than_1Y": [0.85, 0.85],
        "Required_stable_funding": [169650110, 1883442598]
    }
    
    # Update with user selections if provided
    if user_selections:
        for row, selection in user_selections.items():
            if row in data["Row"]:
                idx = data["Row"].index(row)
                data["Included_in_calculation"][idx] = "Yes" if selection else "No"
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate only for included rows
    included_mask = df["Included_in_calculation"] == "Yes"
    
    # Calculate totals only for included rows
    df["Total_amount"] = 0
    df.loc[included_mask, "Total_amount"] = (
        df.loc[included_mask, "Amount_less_than_6M"] + 
        df.loc[included_mask, "Amount_6M_to_1Y"] + 
        df.loc[included_mask, "Amount_greater_than_1Y"]
    )
    
    # Calculate weights only for included rows
    df["Weight_less_than_6M"] = 0
    df["Weight_6M_to_1Y"] = 0
    df["Weight_greater_than_1Y"] = 0
    
    df.loc[included_mask, "Weight_less_than_6M"] = (
        df.loc[included_mask, "Amount_less_than_6M"] / 
        df.loc[included_mask, "Total_amount"]
    )
    df.loc[included_mask, "Weight_6M_to_1Y"] = (
        df.loc[included_mask, "Amount_6M_to_1Y"] / 
        df.loc[included_mask, "Total_amount"]
    )
    df.loc[included_mask, "Weight_greater_than_1Y"] = (
        df.loc[included_mask, "Amount_greater_than_1Y"] / 
        df.loc[included_mask, "Total_amount"]
    )
    
    # Format percentages
    for col in ["Weight_less_than_6M", "Weight_6M_to_1Y", "Weight_greater_than_1Y"]:
        df[col] = df[col].apply(lambda x: f"{x:.2%}" if x != 0 else "0.00%")
    
    # Format large numbers
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", 
                "Total_amount", "Required_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{x:,.0f}")
    
    return df


def create_summary_table_rsf(user_selections=None):
    df = extract_rsf_data(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Titres non-HQLA et actions échangées en bourse (non grevés ou grevés < 1 an)",
            "Autres prêts aux clients non financiers (non grevés ou grevés < 1 an)"
        ],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M (€)": df["Amount_less_than_6M"],
        "Montant 6M-1A (€)": df["Amount_6M_to_1Y"],
        "Montant > 1A (€)": df["Amount_greater_than_1Y"],
        "Montant total (€)": df["Total_amount"],
        "Poids < 6M": df["Weight_less_than_6M"],
        "Poids 6M-1A": df["Weight_6M_to_1Y"],
        "Poids > 1A": df["Weight_greater_than_1Y"],
        "Financement stable requis (€)": df["Required_stable_funding"]
    })
    
    return summary_table

def show_rsf_tab():
        st.markdown("##### Détail du calcul du ratio NSFR")
        st.markdown("###### Les rubriques COREP impactées par le capital planning dans RSF")

        # Create checkboxes for each row
        rsf_rows = ["580", "820"]
        rsf_selections = {}

        cols = st.columns(len(rsf_rows))
        for i, row in enumerate(rsf_rows):
            with cols[i]:
                rsf_selections[row] = st.checkbox(
                    f"Inclure ligne {row}", 
                    value=True,  # Default to checked
                    key=f"rsf_{row}"
                )

        # Get table with user selections
        table_rsf = create_summary_table_rsf(rsf_selections)
        styled_rsf = style_table(table_rsf, highlight_columns=["Poids < 6M", "Poids 6M-1A", "Poids > 1A"])
        st.markdown(styled_rsf.to_html(), unsafe_allow_html=True)
    

def extract_asf_data(user_selections=None):
    data = {
        "Row": ["90", "110", "130", "Total"],
        "Rubrique": [
            "Stable retail deposits",
            "Other retail deposits",
            "ASF from other non-financial customers",
            "TOTAL SELECTED ITEMS"
        ],
        "Included_in_calculation": ["Yes", "Yes", "Yes", "Yes"],
        "Amount_less_than_6M": [70461721, 2687188132, 1854112318, 0],
        "Amount_6M_to_1Y": [263249, 156025150, 96897231, 0],
        "Amount_greater_than_1Y": [0, 90419066, 48761102, 0],
        "Available_stable_funding": [67188721, 2649311020, 1024265877, 0]
    }

    # Update with user selections if provided
    if user_selections:
        for row, selection in user_selections.items():
            if row in data["Row"]:
                idx = data["Row"].index(row)
                data["Included_in_calculation"][idx] = "Yes" if selection else "No"
    
    df = pd.DataFrame(data)
    
    # Calculate only for included rows
    included_mask = df["Included_in_calculation"] == "Yes"
    
    # Calculate totals for included rows only
    df.loc[df["Row"] == "Total", "Amount_less_than_6M"] = (
        df[included_mask & (df["Row"] != "Total")]["Amount_less_than_6M"].sum()
    )
    df.loc[df["Row"] == "Total", "Amount_6M_to_1Y"] = (
        df[included_mask & (df["Row"] != "Total")]["Amount_6M_to_1Y"].sum()
    )
    df.loc[df["Row"] == "Total", "Amount_greater_than_1Y"] = (
        df[included_mask & (df["Row"] != "Total")]["Amount_greater_than_1Y"].sum()
    )
    df.loc[df["Row"] == "Total", "Available_stable_funding"] = (
        df[included_mask & (df["Row"] != "Total")]["Available_stable_funding"].sum()
    )
    
    # Total per row
    df["Total_amount"] = (
        df["Amount_less_than_6M"] + 
        df["Amount_6M_to_1Y"] + 
        df["Amount_greater_than_1Y"]
    )
    
    # Calculate weights only for included rows
    total_selected = df[df["Row"] == "Total"]["Total_amount"].values[0]
    
    df["Poids_%_par_type"] = 0
    df.loc[included_mask, "Poids_%_par_type"] = (
        df.loc[included_mask, "Total_amount"] / total_selected
    )
    
    df["Poids < 6M"] = 0
    df["Poids 6M-1Y"] = 0
    df["Poids > 1Y"] = 0
    
    df.loc[included_mask, "Poids < 6M"] = (
        df.loc[included_mask, "Amount_less_than_6M"] / 
        df.loc[included_mask, "Total_amount"]
    )
    df.loc[included_mask, "Poids 6M-1Y"] = (
        df.loc[included_mask, "Amount_6M_to_1Y"] / 
        df.loc[included_mask, "Total_amount"]
    )
    df.loc[included_mask, "Poids > 1Y"] = (
        df.loc[included_mask, "Amount_greater_than_1Y"] / 
        df.loc[included_mask, "Total_amount"]
    )
    
    # Format numbers
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", 
                "Total_amount", "Available_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{float(x):,.0f}" if x != "" else "")
    
    # Format percentages
    for col in ["Poids_%_par_type", "Poids < 6M", "Poids 6M-1Y", "Poids > 1Y"]:
        df[col] = df[col].apply(lambda x: f"{float(x):.2%}" if x != 0 else "0.00%")
    
    return df

def create_summary_table_asf(user_selections=None):
    df = extract_asf_data(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Dépôts stables de détail",
            "Autres dépôts de détail",
            "ASF provenant d'autres clients non financiers",
            "TOTAL DES ÉLÉMENTS SÉLECTIONNÉS"
        ],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M (€)": df["Amount_less_than_6M"],
        "Montant 6M-1A (€)": df["Amount_6M_to_1Y"],
        "Montant > 1A (€)": df["Amount_greater_than_1Y"],
        "Montant total (€)": df["Total_amount"],
        "Poids % par type": df["Poids_%_par_type"],
        "Poids < 6M": df["Poids < 6M"],
        "Poids 6M-1A": df["Poids 6M-1Y"],
        "Poids > 1A": df["Poids > 1Y"],
        "Financement stable disponible (€)": df["Available_stable_funding"]
    })
    
    return summary_table

def show_asf_tab():
        st.markdown("###### Les rubriques COREP impactées par le capital planning dans ASF")

        # Create checkboxes for ASF rows
        asf_rows = ["90", "110", "130"]
        asf_selections = {}

        cols = st.columns(len(asf_rows))
        for i, row in enumerate(asf_rows):
            with cols[i]:
                asf_selections[row] = st.checkbox(
                    f"Inclure ligne {row}", 
                    value=True,
                    key=f"asf_{row}"
                )

        # Get ASF table with user selections
        table_asf = create_summary_table_asf(asf_selections)
        styled_asf = style_table(table_asf, highlight_columns=["Poids % par type", "Poids < 6M", "Poids 6M-1A", "Poids > 1A"])
        st.markdown(styled_asf.to_html(), unsafe_allow_html=True)

def extract_other_liabilities_data(user_selections=None):
    # Data from the pasted line for "Other liabilities"
    data = {
        "Row": ["0300", "Total"],
        "Rubrique": [
            "Other liabilities",
            "TOTAL SELECTED ITEMS"
        ],
        "Included_in_calculation": ["Yes", "Yes"],
        "Amount_less_than_6M": [466211782, 0],
        "Amount_6M_to_1Y": [108096124, 0],
        "Amount_greater_than_1Y": [1435000000, 0],
        "Available_stable_funding": [1489048062, 0]
    }

    # Update with user selections if provided
    if user_selections:
        for row, selection in user_selections.items():
            if row in data["Row"]:
                idx = data["Row"].index(row)
                data["Included_in_calculation"][idx] = "Yes" if selection else "No"
    
    df = pd.DataFrame(data)
    
    # Calculate only for included rows
    included_mask = df["Included_in_calculation"] == "Yes"
    
    # Calculate totals for included rows only
    df.loc[df["Row"] == "Total", "Amount_less_than_6M"] = (
        df[included_mask & (df["Row"] != "Total")]["Amount_less_than_6M"].sum()
    )
    df.loc[df["Row"] == "Total", "Amount_6M_to_1Y"] = (
        df[included_mask & (df["Row"] != "Total")]["Amount_6M_to_1Y"].sum()
    )
    df.loc[df["Row"] == "Total", "Amount_greater_than_1Y"] = (
        df[included_mask & (df["Row"] != "Total")]["Amount_greater_than_1Y"].sum()
    )
    df.loc[df["Row"] == "Total", "Available_stable_funding"] = (
        df[included_mask & (df["Row"] != "Total")]["Available_stable_funding"].sum()
    )
    
    # Total per row
    df["Total_amount"] = (
        df["Amount_less_than_6M"] + 
        df["Amount_6M_to_1Y"] + 
        df["Amount_greater_than_1Y"]
    )
    
    # Calculate weights for time buckets for included rows
    df["Poids < 6M"] = 0
    df["Poids 6M-1Y"] = 0
    df["Poids > 1Y"] = 0
    
    for idx in df.index:
        if df.loc[idx, "Included_in_calculation"] == "Yes" and df.loc[idx, "Total_amount"] > 0:
            df.loc[idx, "Poids < 6M"] = (
                df.loc[idx, "Amount_less_than_6M"] / 
                df.loc[idx, "Total_amount"]
            )
            df.loc[idx, "Poids 6M-1Y"] = (
                df.loc[idx, "Amount_6M_to_1Y"] / 
                df.loc[idx, "Total_amount"]
            )
            df.loc[idx, "Poids > 1Y"] = (
                df.loc[idx, "Amount_greater_than_1Y"] / 
                df.loc[idx, "Total_amount"]
            )
    
    # Format numbers
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", 
                "Total_amount", "Available_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{float(x):,.0f}" if x != "" else "")
    
    # Format percentages
    for col in ["Poids < 6M", "Poids 6M-1Y", "Poids > 1Y"]:
        df[col] = df[col].apply(lambda x: f"{float(x):.2%}" if x != 0 else "0.00%")
    
    return df

def create_summary_table_other_liabilities(user_selections=None):
    df = extract_other_liabilities_data(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Other liabilities",
            "TOTAL "
        ],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M (€)": df["Amount_less_than_6M"],
        "Montant 6M-1A (€)": df["Amount_6M_to_1Y"],
        "Montant > 1A (€)": df["Amount_greater_than_1Y"],
        "Montant total (€)": df["Total_amount"],
        "Poids < 6M": df["Poids < 6M"],
        "Poids 6M-1A": df["Poids 6M-1Y"],
        "Poids > 1A": df["Poids > 1Y"],
        "Financement stable disponible (€)": df["Available_stable_funding"]
    })
    
    return summary_table

def show_other_liabilities_tab():
    st.markdown("###### Les rubriques COREP impactées par le capital planning dans Other Liabilities")

    # Create checkbox for Other Liabilities row
    other_liab_rows = ["0300"]
    other_liab_selections = {}

    cols = st.columns(len(other_liab_rows))
    for i, row in enumerate(other_liab_rows):
        with cols[i]:
            other_liab_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=True,
                key=f"other_liab_{row}"
            )

    # Get Other Liabilities table with user selections
    table_other_liab = create_summary_table_other_liabilities(other_liab_selections)
    styled_other_liab = style_table(table_other_liab, highlight_columns=["Poids < 6M", "Poids 6M-1A", "Poids > 1A"])
    st.markdown(styled_other_liab.to_html(), unsafe_allow_html=True)

def style_table(df, highlight_columns=None):
    """
    Stylise un tableau avec les couleurs PwC
    """
    # Couleurs PwC
    pwc_orange = "#d04a02"
    pwc_dark_blue = "#FFCDA8"
    pwc_light_gray = "#f5f0e6"
    
    # Style de base du tableau
    table_styles = [
        # Style de l'en-tête
        {"selector": "thead th", 
         "props": f"background-color: {pwc_dark_blue}; color: black; font-weight: bold; text-align: center; padding: 8px;"},
        # Style des cellules du corps
        {"selector": "tbody td", 
         "props": "padding: 6px; text-align: right;"},
        # Style des lignes alternées
        {"selector": "tbody tr:nth-child(odd) td", 
         "props": f"background-color: {pwc_light_gray};"},
        # Style de la première colonne
        {"selector": "tbody td:first-child", 
         "props": "text-align: center; font-weight: bold;"},
        # Style de la deuxième colonne (Description)
        {"selector": "tbody td:nth-child(2)", 
         "props": "text-align: left;"},
        # Style du tableau entier
        {"selector": "table", 
         "props": "width: 100%; border-collapse: collapse; font-size: 14px;"},
        # Bordure du tableau
        {"selector": "th, td", 
         "props": "border: 1px solid #ddd;"}
    ]
    
    # Convertir toutes les colonnes en type objet pour s'assurer que le formatage reste intact
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    # Appliquer le style
    styled_df = df.style.set_table_styles(table_styles)
    
    # Mettre en évidence les colonnes de pourcentage si spécifiées
    if highlight_columns:
        for col in highlight_columns:
            if col in df.columns:
                styled_df = styled_df.set_properties(**{
                    'font-weight': 'bold',
                    'color': pwc_orange
                }, subset=[col])
    
    return styled_df

def show_outflow_tab():
    st.markdown("##### Détail du calcul du ratio LCR")
    st.markdown("###### Les rubriques COREP impactées par le capital planning dans les outflows LCR")

    # Create checkboxes for each row
    lcr_rows = ["0035", "0060", "0070", "0080", "0110", "0250", "0260"]
    lcr_selections = {}

    # Default values for checkboxes
    default_values = {
        "0035": True, "0060": True, "0070": True,
        "0080": False, "0110": False, "0250": False, "0260": True
    }

    # Create checkboxes in 2 rows (4 in first row, 3 in second)
    cols1 = st.columns(4)
    cols2 = st.columns(3)
    
    all_cols = cols1 + cols2
    
    for i, row in enumerate(lcr_rows):
        with all_cols[i]:
            lcr_selections[row] = st.checkbox(
                f"Inclure ligne {row}", 
                value=default_values.get(row, True),  # Default to checked based on default_values
                key=f"lcr_{row}"
            )

    # Get table with user selections
    table_lcr = create_summary_table_lcr_outflow(lcr_selections)
    styled_lcr = style_table(table_lcr, highlight_columns=["Poids (% du total)", "Poids (% lignes integrées)"])
    st.markdown(styled_lcr.to_html(), unsafe_allow_html=True)

def extract_lcr_outflow_data(user_selections=None):
    """
    Extrait les données de sorties LCR (Liquidity Coverage Ratio) des lignes spécifiées.
    """
    # Données des lignes demandées (35, 60, 70, 80, 110, 250, 260)
    data = {
        "Row": ["0035", "0060", "0070", "0080", "0110", "0250", "0260"],
        "Rubrique": [
            "deposits exempted from the calculation of outflows",
            "deposits subject to higher outflows category 1",
            "deposits subject to higher outflows category 2",
            "stable deposits",
            "other retail deposits",
            "Non-operational deposits covered by DGS",
            "Non-operational deposits not covered by DGS"
        ],
        "Amount": [
            1153420704,
            129868556,
            1654960060,
            67414342,
            36822874,
            25816211,
            1323881264
        ]
    }
    
    # Création du DataFrame
    df = pd.DataFrame(data)
    
    # Update with user selections if provided
    if user_selections:
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if user_selections.get(x, False) else "Non"
        )
    else:
        # Default values if no selections provided
        default_values = {
            "0035": True, "0060": True, "0070": True,
            "0080": False, "0110": False, "0250": False, "0260": True
        }
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if default_values.get(x, False) else "Non"
        )
    
    # Calculer le total des lignes incluses dans le calcul
    included_mask = df["Included_in_calculation"] == "Oui"
    total_included = df[included_mask]["Amount"].sum()
    
    # Calculer les poids (proportion par rapport au total des lignes incluses)
    df["Weight_proportion"] = pd.NA
    for idx, row in df.iterrows():
        if row["Included_in_calculation"] == "Oui" and total_included > 0:
            df.at[idx, "Weight_proportion"] = row["Amount"] / total_included
    
    # Calculer les poids par rapport au total des dépôts de détail (si nécessaire)
    retail_deposit_rows = ["0035", "0060", "0070", "0080", "0110"]
    retail_deposits_included = df[df["Row"].isin(retail_deposit_rows) & included_mask]
    retail_deposits_total = retail_deposits_included["Amount"].sum()
    
    df["Weight_included"] = pd.NA
    for idx, row in df.iterrows():
        if row["Row"] in retail_deposit_rows and row["Included_in_calculation"] == "Oui" and retail_deposits_total > 0:
            df.at[idx, "Weight_included"] = row["Amount"] / retail_deposits_total
    
    return df

def create_summary_table_lcr_outflow(user_selections=None):
    """
    Crée un tableau récapitulatif à partir des données LCR outflow.
    """
    df = extract_lcr_outflow_data(user_selections)
    
    # Formatage des pourcentages et des montants
    df_formatted = df.copy()
    df_formatted["Weight_proportion"] = df["Weight_proportion"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")
    df_formatted["Weight_included"] = df["Weight_included"].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")
    df_formatted["Amount"] = df["Amount"].apply(lambda x: f"{int(x):,}".replace(",", " "))
    
    # Création d'une version plus lisible du tableau en conservant les rubriques en anglais
    summary_table = pd.DataFrame({
        "Row": df_formatted["Row"],
        "Rubrique": df_formatted["Rubrique"],
        "Inclus dans le calcul": df_formatted["Included_in_calculation"],
        "Montant (2024)": df_formatted["Amount"],
        "Poids (% du total)": df_formatted["Weight_proportion"],
        "Poids (% lignes integrées)": df_formatted["Weight_included"]
    })
    
    # Ajouter une ligne de total pour les lignes incluses
    included_rows = df[df["Included_in_calculation"] == "Oui"]
    total_included = included_rows["Amount"].sum()
    
    total_row = pd.DataFrame({
        "Row": ["Total"],
        "Rubrique": ["TOTAL OUTFLOWS"],
        "Inclus dans le calcul": [""],
        "Montant (2024)": [f"{int(total_included):,}".replace(",", " ")],
        "Poids (% du total)": ["100.00%"],
        "Poids (% lignes integrées)": [""]
    })
    
    # Concaténer avec le tableau principal
    summary_table = pd.concat([summary_table, total_row], ignore_index=True)
    
    return summary_table


def apply_capital_planning_to_df80(df_80, capital_planning_value, rsf_data_row, target_row):

    # Extract weights from the RSF data row
    weight_less_6m = float(rsf_data_row['Poids < 6M'].strip('%')) / 100
    weight_6m_1y = float(rsf_data_row['Poids 6M-1A'].strip('%')) / 100
    weight_greater_1y = float(rsf_data_row['Poids > 1A'].strip('%')) / 100
    
    # Calculate amounts to add to each maturity bucket
    amount_less_6m = capital_planning_value * weight_less_6m
    amount_6m_1y = capital_planning_value * weight_6m_1y
    amount_greater_1y = capital_planning_value * weight_greater_1y
    
    # Apply to the appropriate row in df_80
    row_index = df_80[df_80['row'] == target_row].index
    
    if len(row_index) > 0:
        idx = row_index[0]
        
        # Add amounts to each maturity bucket
        df_80.at[idx, '0010'] = (df_80.at[idx, '0010'] if pd.notnull(df_80.at[idx, '0010']) else 0) + amount_less_6m
        df_80.at[idx, '0020'] = (df_80.at[idx, '0020'] if pd.notnull(df_80.at[idx, '0020']) else 0) + amount_6m_1y
        df_80.at[idx, '0030'] = (df_80.at[idx, '0030'] if pd.notnull(df_80.at[idx, '0030']) else 0) + amount_greater_1y
    
    return df_80

def apply_capital_planning_to_df81(df_81, capital_planning_value, asf_data):
    """
    Apply capital planning impact to df_81 based on ASF weights from the provided table.
    Distributes the value to rows 90, 110, and 130 according to their weights.
    
    Args:
        df_81 (pd.DataFrame): The df_81 DataFrame to modify
        capital_planning_value (float): The capital planning value to distribute
        asf_data (pd.DataFrame): The ASF data table containing weights
        
    Returns:
        pd.DataFrame: Modified df_81 with capital planning impacts applied
    """
    # Filter only the relevant rows (90, 110, 130)
    asf_rows = asf_data[asf_data['Row'].isin(['90', '110', '130'])]
    
    # Calculate total weight for normalization
    total_weight = asf_rows['Poids % par type'].str.rstrip('%').astype(float).sum() / 100
    
    for _, asf_row in asf_rows.iterrows():
        # Extract weights
        weight_type = float(asf_row['Poids % par type'].strip('%')) / 100
        weight_less_6m = float(asf_row['Poids < 6M'].strip('%')) / 100
        weight_6m_1y = float(asf_row['Poids 6M-1A'].strip('%')) / 100
        weight_greater_1y = float(asf_row['Poids > 1A'].strip('%')) / 100
        
        # Calculate the portion for this row (normalized by total weight)
        portion = capital_planning_value * (weight_type / total_weight)
        
        # Calculate amounts to add to each maturity bucket
        amount_less_6m = portion * weight_less_6m
        amount_6m_1y = portion * weight_6m_1y
        amount_greater_1y = portion * weight_greater_1y
        
        # Find the target row in df_81
        target_row = int(asf_row['Row'])
        row_index = df_81[df_81['row'] == target_row].index
        
        if len(row_index) > 0:
            idx = row_index[0]
            
            # Add amounts to each maturity bucket
            df_81.at[idx, '0010'] = (df_81.at[idx, '0010'] if pd.notnull(df_81.at[idx, '0010']) else 0) + amount_less_6m
            df_81.at[idx, '0020'] = (df_81.at[idx, '0020'] if pd.notnull(df_81.at[idx, '0020']) else 0) + amount_6m_1y
            df_81.at[idx, '0030'] = (df_81.at[idx, '0030'] if pd.notnull(df_81.at[idx, '0030']) else 0) + amount_greater_1y
    
    return df_81

def apply_capital_planning_to_df81_liabilities(df_81, capital_planning_value, liabilities_data_row):
    """
    Apply capital planning impact to df_81 row 300 (Other liabilities) based on weights.
    
    Args:
        df_81 (pd.DataFrame): The df_81 DataFrame to modify
        capital_planning_value (float): The capital planning value to distribute
        liabilities_data_row (pd.Series): The row from liabilities data table containing weights
        
    Returns:
        pd.DataFrame: Modified df_81 with capital planning impacts applied
    """
    # Extract weights from the liabilities data row
    weight_less_6m = float(liabilities_data_row['Poids < 6M'].strip('%')) / 100
    weight_6m_1y = float(liabilities_data_row['Poids 6M-1A'].strip('%')) / 100
    weight_greater_1y = float(liabilities_data_row['Poids > 1A'].strip('%')) / 100
    
    # Calculate amounts to add to each maturity bucket
    amount_less_6m = capital_planning_value * weight_less_6m
    amount_6m_1y = capital_planning_value * weight_6m_1y
    amount_greater_1y = capital_planning_value * weight_greater_1y
    
    # Apply to row 300 in df_81
    row_300_index = df_81[df_81['row'] == 300].index
    
    if len(row_300_index) > 0:
        idx = row_300_index[0]
        
        # Add amounts to each maturity bucket
        df_81.at[idx, '0010'] = (df_81.at[idx, '0010'] if pd.notnull(df_81.at[idx, '0010']) else 0) + amount_less_6m
        df_81.at[idx, '0020'] = (df_81.at[idx, '0020'] if pd.notnull(df_81.at[idx, '0020']) else 0) + amount_6m_1y
        df_81.at[idx, '0030'] = (df_81.at[idx, '0030'] if pd.notnull(df_81.at[idx, '0030']) else 0) + amount_greater_1y
    
    return df_81

def extract_liabilities_data():
    """
    Create a DataFrame with the liabilities data for row 300.
    """
    data = {
        "Row": ["0300", "Total"],
        "Rubrique": ["Other liabilities", "TOTAL"],
        "Inclus dans le calcul": ["Oui", "Oui"],
        "Montant < 6M (€)": ["466,211,782", "466,211,782"],
        "Montant 6M-1A (€)": ["108,096,124", "108,096,124"],
        "Montant > 1A (€)": ["1,435,000,000", "1,435,000,000"],
        "Montant total (€)": ["2,009,307,906", "2,009,307,906"],
        "Poids < 6M": ["23.20%", "23.20%"],
        "Poids 6M-1A": ["5.38%", "5.38%"],
        "Poids > 1A": ["71.42%", "71.42%"],
        "Financement stable disponible (€)": ["1,489,048,062", "1,489,048,062"]
    }
    
    df = pd.DataFrame(data)
    
    # Clean numeric columns
    numeric_cols = ["Montant < 6M (€)", "Montant 6M-1A (€)", "Montant > 1A (€)", 
                   "Montant total (€)", "Financement stable disponible (€)"]
    for col in numeric_cols:
        df[col] = df[col].str.replace(",", "").str.replace(" ", "").astype(float)
    
    return df


def propager_CP_vers_COREP_NSFR(poste_bilan, delta, df_80, df_81, ponderations=None):
    lignes = get_mapping_df_row_CP(poste_bilan)
    print("lignes nsfr = ", lignes)

    lignes_80 = [l for l in lignes if l[1] == "df_80"]
    lignes_81 = [l for l in lignes if l[1] == "df_81"]
    n = len(lignes_80)
    m = len(lignes_81)

    print("n (df_80) = ", n)
    print("m (df_81) = ", m)

    if n + m == 0:
        return df_80, df_81

    df_80 = df_80.copy()
    df_81 = df_81.copy()

    if ponderations is None:
        ponderations_80 = [1 / n] * n if n > 0 else []
        ponderations_81 = [1 / m] * m if m > 0 else []
    else:
        ponderations_80 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_80"]
        ponderations_81 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_81"]

    # Get all data tables
    rsf_data = create_summary_table_rsf()
    asf_data = create_summary_table_asf()
    liabilities_data = extract_liabilities_data()

    # Special handling for specific posts
    if poste_bilan == "Portefeuille":
        rsf_row = rsf_data[rsf_data['Row'] == '580'].iloc[0]
        df_80 = apply_capital_planning_to_df80(df_80, delta, rsf_row, 580)
    elif poste_bilan == "Créances clientèle":
        rsf_row = rsf_data[rsf_data['Row'] == '820'].iloc[0]
        df_80 = apply_capital_planning_to_df80(df_80, delta, rsf_row, 820)
    elif poste_bilan == "Depots clients (passif)":
        df_81 = apply_capital_planning_to_df81(df_81, delta, asf_data)
    elif poste_bilan == "Dettes envers les établissements de crédit (passif)":
        liabilities_row = liabilities_data[liabilities_data['Row'] == '0300'].iloc[0]
        df_81 = apply_capital_planning_to_df81_liabilities(df_81, delta, liabilities_row)
    else:
        # Normal processing for other posts
        for (row_num, _), poids in zip(lignes_80, ponderations_80):
            part_delta = delta * poids
            print("part delta in df_80 = ", part_delta)
            mask = df_80["row"] == row_num
            df_80.loc[mask, "0010"] = df_80.loc[mask, "0010"] + part_delta

        for (row_num, _), poids in zip(lignes_81, ponderations_81):
            part_delta = delta * poids
            print("part delta in df_81 = ", part_delta)
            mask = df_81["row"] == row_num
            df_81.loc[mask, "0010"] = df_81.loc[mask, "0010"] + part_delta

    return df_80, df_81