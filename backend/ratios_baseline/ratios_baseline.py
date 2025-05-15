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
                if poste_bilan_lower == "créances clientèle (hors hypo)":
                    return 0.01 * valeur
                elif poste_bilan_lower == "créances banques autres":
                    return 0.28 * valeur
                elif poste_bilan_lower == "depots clients (passif)":
                    return 0.71 * valeur
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
        # Optional: use weights if provided (must match the length)
        ponderations_80 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_80"]
        ponderations_81 = [p for (row, df), p in zip(lignes, ponderations) if df == "df_81"]

    # Apply delta to df_80
    for (row_num, _), poids in zip(lignes_80, ponderations_80):
        part_delta = delta * poids
        print("part delta in df_80 = ", part_delta)
        mask = df_80["row"] == row_num
        df_80.loc[mask, "0010"] = df_80.loc[mask, "0010"] + part_delta

    # Apply delta to df_81
    for (row_num, _), poids in zip(lignes_81, ponderations_81):
        part_delta = delta * poids
        print("part delta in df_81 = ", part_delta)
        mask = df_81["row"] == row_num
        df_81.loc[mask, "0010"] = df_81.loc[mask, "0010"] + part_delta

    return df_80, df_81





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

def extract_rsf_data():
    # Données des lignes 580 et 820
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
    
    # Création du DataFrame
    df = pd.DataFrame(data)
    
    # Calcul des montants totaux pour chaque ligne
    df["Total_amount"] = df["Amount_less_than_6M"] + df["Amount_6M_to_1Y"] + df["Amount_greater_than_1Y"]
    
    # Calcul des poids (proportion de chaque tranche de maturité)
    df["Weight_less_than_6M"] = df["Amount_less_than_6M"] / df["Total_amount"]
    df["Weight_6M_to_1Y"] = df["Amount_6M_to_1Y"] / df["Total_amount"]
    df["Weight_greater_than_1Y"] = df["Amount_greater_than_1Y"] / df["Total_amount"]
    
    # Formatage des pourcentages
    for col in ["Weight_less_than_6M", "Weight_6M_to_1Y", "Weight_greater_than_1Y"]:
        df[col] = df[col].apply(lambda x: f"{x:.2%}")
    
    # Formatage des grands nombres avec séparateur de milliers
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", 
                "Total_amount", "Required_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{x:,.0f}")
    
    return df

def create_summary_table_rsf():
    """
    Crée un tableau récapitulatif à partir des données NSFR.
    """
    df = extract_rsf_data()
    
    # Création d'une version plus lisible du tableau avec traduction en français
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Titres non-HQLA et actions échangées en bourse (non grevés ou grevés < 1 an)",
            "Autres prêts aux clients non financiers (non grevés ou grevés < 1 an)"
        ],
        "Inclus dans le calcul": ["Oui", "Oui"],
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

def extract_asf_data():
    data = {
        "Row": ["90", "110", "130", "Total"],
        "Rubrique": [
            "Stable retail deposits",
            "Other retail deposits",
            "ASF from other non-financial customers",
            "TOTAL SELECTED ITEMS"
        ],
        "Included_in_calculation": ["Yes", "Yes", "Yes", "Yes"],
        "Amount_less_than_6M": [70461721, 2687188132, 1854112318, 70461721 + 2687188132 + 1854112318],
        "Amount_6M_to_1Y": [263249, 156025150, 96897231, 263249 + 156025150 + 96897231],
        "Amount_greater_than_1Y": [0, 90419066, 48761102, 0 + 90419066 + 48761102],
        "Available_stable_funding": [67188721, 2649311020, 1024265877, 67188721 + 2649311020 + 1024265877]
    }

    df = pd.DataFrame(data)

    # Total par ligne
    df["Total_amount"] = df["Amount_less_than_6M"] + df["Amount_6M_to_1Y"] + df["Amount_greater_than_1Y"]

    # Total global
    total_selected_items = df[df["Row"] == "Total"]["Total_amount"].values[0]

    # Poids % par type
    df["Poids_%_par_type"] = df["Total_amount"] / total_selected_items

    # Poids par tranche de maturité relative à la ligne
    df["Poids < 6M"] = df["Amount_less_than_6M"] / df["Total_amount"]
    df["Poids 6M-1Y"] = df["Amount_6M_to_1Y"] / df["Total_amount"]
    df["Poids > 1Y"] = df["Amount_greater_than_1Y"] / df["Total_amount"]

    # Formatage des montants
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", "Total_amount", "Available_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{x:,.0f}")

    # Formatage des pourcentages
    for col in ["Poids_%_par_type", "Poids < 6M", "Poids 6M-1Y", "Poids > 1Y"]:
        df[col] = df[col].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "")

    return df

def create_summary_table_asf():
    df = extract_asf_data()

    # Création d'une version traduite du tableau
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Dépôts stables de détail",
            "Autres dépôts de détail",
            "ASF provenant d'autres clients non financiers",
            "TOTAL DES ÉLÉMENTS SÉLECTIONNÉS"
        ],
        "Inclus dans le calcul": ["Oui", "Oui", "Oui", "Oui"],
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

def style_table(df, highlight_columns=None):
    """
    Stylise un tableau avec les couleurs PwC
    """
    # Couleurs PwC
    pwc_orange = "#f47721"
    pwc_dark_gray = "#3d3d3d"
    #pwc_light_beige = "#f5f0e6"
    pwc_brown = "#6e4c1e"
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