import os
import pandas as pd
import streamlit as st
from config import style_table



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
    bilan[["2024", "2025", "2026", "2027"]] = bilan[["2024", "2025", "2026", "2027"]].apply(pd.to_numeric, errors='coerce')
    return bilan


def charger_lcr():
    """
    Charge le fichier LCR situé dans le dossier 'data/'.
    """
    from backend.lcr.feuille_72 import charger_feuille_72
    from backend.lcr.feuille_73 import charger_feuille_73
    from backend.lcr.feuille_74 import charger_feuille_74
    
    lcr_path = os.path.join("data", "LCR.csv")
    
    if not os.path.exists(lcr_path):
        raise FileNotFoundError(f"Le fichier {lcr_path} est introuvable.")
    
    df_72 = charger_feuille_72(lcr_path)
    df_73 = charger_feuille_73(lcr_path)
    df_74 = charger_feuille_74(lcr_path)

    
    return df_72, df_73, df_74

def charger_nsfr():
    """
    Charge le fichier NSFR situé dans le dossier 'data/'.
    """
    from backend.nsfr.feuille_80 import charger_feuille_80
    from backend.nsfr.feuille_81 import charger_feuille_81
    
    nsfr_path = os.path.join("data", "NSFR.csv")
    
    if not os.path.exists(nsfr_path):
        raise FileNotFoundError(f"Le fichier {nsfr_path} est introuvable.")
    
    df_80 = charger_feuille_80(nsfr_path)
    df_81 = charger_feuille_81(nsfr_path)

    return df_80, df_81

#####################################  IMPACT PNU SUR BILAN  ##########################################



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


def ajuster_annees_suivantes(bilan_df, poste, annee_depart, variation):
    """
    Ajuste la valeur d’un poste pour toutes les années > annee_depart en appliquant la variation.
    """
    bilan_df = bilan_df.copy()
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste].index
    if index_poste.empty:
        return bilan_df  # Poste non trouvé

    idx = index_poste[0]
    annees = [col for col in bilan_df.columns if col.isdigit()]
    annees_suivantes = [a for a in annees if int(a) > int(annee_depart)]

    for an in annees_suivantes:
        bilan_df.loc[idx, an] -= variation

    return bilan_df

def afficher_postes_concernes(bilan_df, postes, horizon=1):
    """
    Affiche les lignes associées aux postes concernés pour les années de 2024 à 2024 + horizon,
    avec formatage des montants en '123 456 789.12'.
    """
    # Générer dynamiquement la liste des années en fonction de l'horizon
    annees_base = [str(2024 + i) for i in range(horizon + 1)]

    resultats = []

    for poste in postes:
        idx = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste].index
        if not idx.empty:
            ligne_valeurs = bilan_df.loc[idx[0], ["Poste du Bilan"] + annees_base]
            resultats.append(ligne_valeurs)

    df_resultats = pd.DataFrame(resultats).set_index("Poste du Bilan")

    # Format personnalisé
    def format_custom(x):
        if pd.isna(x):
            return ""
        return f"{x:,.2f}".replace(",", " ")

    return df_resultats.applymap(format_custom)


def appliquer_stress_retrait_depots(bilan_df, pourcentage, horizon=1, annee="2025",
                                    poids_portefeuille=0.5, poids_creances=0.5):
    bilan_df = bilan_df.copy()

    poste_depots = "Depots clients (passif)"
    poste_portefeuille = "Portefeuille"
    poste_creances = "Créances banques autres"

    annee_precedente = str(int(annee) - 1)

    # Valeur de référence pour le choc : dépôts 2024
    valeur_depots_2024 = get_valeur_poste_bilan(bilan_df, poste_depots, annee_precedente)
    if valeur_depots_2024 is None:
        raise ValueError(f"Poste '{poste_depots}' non trouvé ou valeur manquante pour {annee_precedente}.")

    # Calcul du choc total basé sur les dépôts 2024
    choc_total = valeur_depots_2024 * pourcentage
    choc_portefeuille = choc_total * poids_portefeuille
    choc_creances = choc_total * poids_creances

    # Appliquer le choc à chaque année de l'horizon
    for i in range(horizon):
        target_annee = str(int(annee) + i)
        annee_ref = str(int(target_annee) - 1)

        # Dépôts clients
        idx_dep = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_depots].index[0]
        val_ref_dep = bilan_df.loc[idx_dep, annee_ref]
        cap_planning_dep = bilan_df.loc[idx_dep, target_annee] - val_ref_dep
        bilan_df.loc[idx_dep, target_annee] = val_ref_dep + cap_planning_dep - choc_total

        # Portefeuille
        idx_port = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_portefeuille].index[0]
        val_ref_port = bilan_df.loc[idx_port, annee_ref]
        cap_planning_port = bilan_df.loc[idx_port, target_annee] - val_ref_port
        bilan_df.loc[idx_port, target_annee] = val_ref_port + cap_planning_port - choc_portefeuille

        # Créances banques autres
        idx_cre = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_creances].index[0]
        val_ref_cre = bilan_df.loc[idx_cre, annee_ref]
        cap_planning_cre = bilan_df.loc[idx_cre, target_annee] - val_ref_cre
        bilan_df.loc[idx_cre, target_annee] = val_ref_cre + cap_planning_cre - choc_creances

    return bilan_df

########################################      LCR      ########################################
def show_hqla_tab():
    st.markdown("##### ")
    st.markdown("###### Les rubriques COREP HQLA impactées par l'événement retrait de dépôts")

    # Create checkboxes for each row
    hqla_rows = ["0040", "0050", "0070"]
    hqla_selections = {}

    # Default values for checkboxes (all checked)
    default_values =     default_values = {
        "0040": False, "0050": False, "0070": True
    }

    # Create checkboxes in columns
    cols = st.columns(len(hqla_rows))
    
    for i, row in enumerate(hqla_rows):
        with cols[i]:
            hqla_selections[row] = st.checkbox(
                f"Inclure ligne {row}", 
                value=default_values.get(row, True),
                key=f"hqla_{row}"
            )

    # Get table with user selections
    table_hqla = create_summary_table_hqla(hqla_selections)
    styled_hqla = style_table(table_hqla, highlight_columns=["Poids (% du total)"])
    st.markdown(styled_hqla.to_html(), unsafe_allow_html=True)

def extract_hqla_data(user_selections=None):
    data = {
        "Row": ["0040", "0050", "0070"],
        "Rubrique": [
            "Coins and banknotes",
            "Withdrawable central bank reserves",
            "Central government assets"
        ],
        "Amount": [3620790, 100941682, 573180647]
    }
    
    df = pd.DataFrame(data)
    
    if user_selections:
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if user_selections.get(x, False) else "Non"
        )
    else:
        df["Included_in_calculation"] = "Oui"
    
    included_mask = df["Included_in_calculation"] == "Oui"
    total_included = df[included_mask]["Amount"].sum()
    
    df["Weight"] = 0
    for idx, row in df.iterrows():
        if row["Included_in_calculation"] == "Oui" and total_included > 0:
            df.at[idx, "Weight"] = row["Amount"] / total_included
    
    return df

def create_summary_table_hqla(user_selections=None):
    df = extract_hqla_data(user_selections)
    
    df_formatted = df.copy()
    df_formatted["Weight"] = df["Weight"].apply(lambda x: f"{x:.2%}" if x > 0 else "")
    df_formatted["Amount"] = df["Amount"].apply(lambda x: f"{int(x):,}".replace(",", " "))
    
    summary_table = pd.DataFrame({
        "Row": df_formatted["Row"],
        "Rubrique": df_formatted["Rubrique"],
        "Intégré dans le calcul": df_formatted["Included_in_calculation"],
        "Montant 2024": df_formatted["Amount"],
        "Poids (% du total)": df_formatted["Weight"]
    })
    
    included_rows = df[df["Included_in_calculation"] == "Oui"]
    total_included = included_rows["Amount"].sum()
    
    total_row = pd.DataFrame({
        "Row": ["Total"],
        "Rubrique": ["TOTAL HQLA"],
        "Intégré dans le calcul": [""],
        "Montant 2024": [f"{int(total_included):,}".replace(",", " ")], 
        "Poids (% du total)": ["100.00%"]
    })
    
    return pd.concat([summary_table, total_row], ignore_index=True)

def show_outflow_tab_retrait_depots():
    st.markdown("##### ")
    st.markdown("###### Les rubriques COREP Outflow impactées par l'événement retrait de dépôts")

    outflow_rows = ["0035", "0060", "0070", "0080", "0110", "0250", "0260"]
    outflow_selections = {}

    default_values = {
        "0035": True, "0060": True, "0070": True,
        "0080": False, "0110": False, "0250": False, "0260": True
    }

    cols1 = st.columns(4)
    cols2 = st.columns(3)
    all_cols = cols1 + cols2
    
    for i, row in enumerate(outflow_rows):
        with all_cols[i]:
            outflow_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=default_values.get(row, True),
                key=f"outflow_retrait_{row}"
            )

    table_outflow = create_summary_table_outflow_retrait(outflow_selections)
    styled_outflow = style_table(table_outflow, highlight_columns=["Poids (% du total)"])
    st.markdown(styled_outflow.to_html(), unsafe_allow_html=True)

def extract_outflow_retrait_data(user_selections=None):
    data = {
        "Row": ["0035", "0060", "0070", "0080", "0110", "0250", "0260"],
        "Rubrique": [
            "deposits exempted from the calculation of outflows",
            "category 1",
            "category 2",
            "stable deposits",
            "other retail deposits",
            "covered by DGS",
            "not covered by DGS"
        ],
        "Amount": [1153420704, 129868556, 1654960060, 67414342, 36822874, 25816211, 1323881264]
    }
    
    df = pd.DataFrame(data)
    default_values = {
        "0035": True, "0060": True, "0070": True,
        "0080": False, "0110": False, "0250": False, "0260": True
    }
    
    if user_selections:
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if user_selections.get(x, False) else "Non"
        )
    else:
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if default_values.get(x, False) else "Non"
        )
    
    included_mask = df["Included_in_calculation"] == "Oui"
    total_included = df[included_mask]["Amount"].sum()
    
    df["Weight"] = 0
    df["Impacted_amount"] = 0
    for idx, row in df.iterrows():
        if row["Included_in_calculation"] == "Oui" and total_included > 0:
            df.at[idx, "Weight"] = row["Amount"] / total_included
    
    return df

def create_summary_table_outflow_retrait(user_selections=None):
    df = extract_outflow_retrait_data(user_selections)
    
    df_formatted = df.copy()
    df_formatted["Weight"] = df["Weight"].apply(lambda x: f"{x:.2%}" if x > 0 else "")
    df_formatted["Amount"] = df["Amount"].apply(lambda x: f"{int(x):,}".replace(",", " "))
    df_formatted["Impacted_amount"] = df["Impacted_amount"].apply(lambda x: f"{int(x):,}".replace(",", " ") if x > 0 else "0")
    
    summary_table = pd.DataFrame({
        "Row": df_formatted["Row"],
        "Rubrique": df_formatted["Rubrique"],
        "Intégré dans le calcul": df_formatted["Included_in_calculation"],
        "Montant 2024": df_formatted["Amount"],
        "Poids (% du total)": df_formatted["Weight"]
    })
    
    included_rows = df[df["Included_in_calculation"] == "Oui"]
    total_included = included_rows["Amount"].sum()
    
    total_row = pd.DataFrame({
        "Row": ["Total"],
        "Rubrique": ["TOTAL OUTFLOWS"],
        "Intégré dans le calcul": [""],
        "Montant 2024": [f"{int(total_included):,}".replace(",", " ")], 
        "Poids (% du total)": ["100.00%"]
    })
    
    return pd.concat([summary_table, total_row], ignore_index=True)

def show_inflow_tab_retrait_depots():
    st.markdown("##### ")
    st.markdown("###### Les rubriques COREP Inflow impactées par l'événement retrait de dépôts")

    inflow_rows = ["0040", "0060", "0070", "0090", "0160", "0201", "0240", "0260"]
    inflow_selections = {}

    default_values = {
        "0040": False, "0060": False, "0070": False, "0090": False, "0160":True,
        "0201": False, "0240": False, "0260": False

    }

    cols1 = st.columns(4)
    cols2 = st.columns(4)
    all_cols = cols1 + cols2
    
    for i, row in enumerate(inflow_rows):
        with all_cols[i]:
            inflow_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=default_values.get(row, True),
                key=f"inflow_retrait_{row}"
            )

    table_inflow = create_summary_table_inflow_retrait(inflow_selections)
    styled_inflow = style_table(table_inflow, highlight_columns=["Poids (% du total)", "Taux d'entrée", "Montant impacté"])
    st.markdown(styled_inflow.to_html(), unsafe_allow_html=True)

def extract_inflow_retrait_data(user_selections=None):
    data = {
        "Row": ["0040", "0060", "0070", "0090", "0160", "0201", "0240", "0260"],
        "Rubrique": [
            "monies due from non-financial customers (not principal repayment)",
            "monies due from retail customers",
            "monies due from non-financial corporates",
            "monies due from other legal entities",
            "monies due from central banks and financial customers",
            "loans with an undefined contractual end date",
            "inflows from derivatives",
            "other inflows"
        ],
        "Amount": [6071608, 17398647, 12122323, 157576, 1170789830, 1467363, 19425, 2073651],
    }
    
    df = pd.DataFrame(data)
    
    if user_selections:
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if user_selections.get(x, False) else "Non"
        )
    else:
        default_included = {"0160"}
        df["Included_in_calculation"] = df["Row"].apply(
            lambda x: "Oui" if x in default_included else "Non"
        )
    
    included_mask = df["Included_in_calculation"] == "Oui"
    total_included = df[included_mask]["Amount"].sum()
    
    df["Weight"] = 0
    for idx, row in df.iterrows():
        if row["Included_in_calculation"] == "Oui" and total_included > 0:
            df.at[idx, "Weight"] = row["Amount"] / total_included
    
    return df


def create_summary_table_inflow_retrait(user_selections=None):
    df = extract_inflow_retrait_data(user_selections)
    
    df_formatted = df.copy()
    df_formatted["Weight"] = df["Weight"].apply(lambda x: f"{x:.2%}" if x > 0 else "")
    df_formatted["Amount"] = df["Amount"].apply(lambda x: f"{int(x):,}".replace(",", " "))    
    summary_table = pd.DataFrame({
        "Row": df_formatted["Row"],
        "Rubrique": df_formatted["Rubrique"],
        "Intégré dans le calcul": df_formatted["Included_in_calculation"],
        "Montant 2024": df_formatted["Amount"],
        "Poids (% du total)": df_formatted["Weight"]
    })
    
    included_rows = df[df["Included_in_calculation"] == "Oui"]
    total_included = included_rows["Amount"].sum()
    
    total_row = pd.DataFrame({
        "Row": ["Total"],
        "Rubrique": ["TOTAL INFLOWS"],
        "Intégré dans le calcul": [""],
        "Montant 2024": [f"{int(total_included):,}".replace(",", " ")], 
        "Poids (% du total)": ["100.00%"]
    })
    
    return pd.concat([summary_table, total_row], ignore_index=True)




def propager_retrait_depots_vers_df72(df_72, bilan_df, annee="2024", pourcentage=0.15, horizon=1, poids_portefeuille=0.15):
    """
    Propage l'impact du retrait massif des dépôts vers les lignes HQLA du df_72
    selon leur poids dans le total des actifs HQLA.
    
    Nouvelle logique:
    Pour chaque ligne HQLA dans df_72:
    adjustment = Poids (% du total) * poids_portefeuille * (-valeur_dépôts_2024 * pourcentage_retrait)
    """
    df_72 = df_72.copy()

    # 1. Récupérer les données HQLA avec leurs poids
    hqla_data = extract_hqla_data()  # Utilise la fonction existante
    hqla_data = hqla_data[hqla_data["Included_in_calculation"] == "Oui"]  # Seulement les lignes incluses
    
    # 2. Récupérer la valeur des dépôts clients 2024
    poste_depots = "Depots clients (passif)"
    valeur_depots_2024 = get_valeur_poste_bilan(bilan_df, poste_depots, "2024")
    if valeur_depots_2024 is None:
        raise ValueError(f"Poste '{poste_depots}' introuvable ou sans valeur pour 2024.")

    # 3. Calculer le choc total (négatif car c'est un retrait)
    choc_total = -valeur_depots_2024 * pourcentage
    
    # 4. Appliquer l'impact à chaque ligne HQLA dans df_72
    for _, row in hqla_data.iterrows():
        row_id = int(row["Row"])  # Convertir "0040" -> 40
        
        # Trouver la ligne correspondante dans df_72
        mask = df_72["row"] == row_id
        if not mask.any():
            print(f"Avertissement: Ligne HQLA {row_id} non trouvée dans df_72")
            continue
            
        # Calculer l'ajustement pour cette ligne
        poids = float(row["Weight"])
        adjustment = poids * poids_portefeuille * choc_total
        
        # Appliquer l'ajustement (négatif car retrait)
        df_72.loc[mask, "0010"] = df_72.loc[mask, "0010"] + adjustment
        
        #print(f"Applied adjustment to row {row_id}: {adjustment:,.2f} (weight: {poids:.2%})")

    return df_72

def propager_retrait_depots_vers_df73(df_73, bilan_df, annee="2024", pourcentage=0.15, horizon=1):
    """
    Propage l’impact du retrait massif des dépôts vers les lignes d’outflows dans df_73,
    selon leur poids dans le total des rubriques sélectionnées.

    Formule :
    adjustment = Poids (% du total) * (-valeur_dépôts_2024 * pourcentage_retrait)

    Seules les lignes où 'Inclure dans calcul' == 'Oui' sont ajustées.
    """
    df_73 = df_73.copy()

    # 1. Extraire la table d’outflows avec les poids selon les sélections utilisateur
    outflow_data = extract_outflow_retrait_data()
    outflow_data = outflow_data[outflow_data["Included_in_calculation"] == "Oui"]

    # 2. Récupérer la valeur des dépôts clients
    poste_depots = "Depots clients (passif)"
    valeur_depots_2024 = get_valeur_poste_bilan(bilan_df, poste_depots, "2024")
    if valeur_depots_2024 is None:
        raise ValueError(f"Poste '{poste_depots}' introuvable ou sans valeur pour 2024")

    # 3. Calculer le choc total
    choc_total = -valeur_depots_2024 * pourcentage / horizon

    # 4. Appliquer l'ajustement à chaque ligne sélectionnée
    for _, row in outflow_data.iterrows():
        row_id = int(row["Row"])  # Ex: "0060" -> 60
        poids = float(row["Weight"])
        adjustment = poids * choc_total

        mask = df_73["row"] == row_id
        if not mask.any():
            print(f"Avertissement: ligne {row_id} non trouvée dans df_73.")
            continue

        df_73.loc[mask, "0010"] = df_73.loc[mask, "0010"] + adjustment
        #print(f"Ajouté à la ligne {row_id} : {adjustment:,.2f} (poids: {poids:.2%})")

    return df_73
def propager_retrait_depots_vers_df74(df_74, bilan_df, annee="2024", pourcentage=0.15, horizon=1, poids_portefeuille=0.15, impact_creances=0.85, inflow_selections=None):
    """
    Propage l’impact du retrait des dépôts sur les lignes inflow de df_74, selon les pondérations.
    """
    df_74 = df_74.copy()

    poste_depots = "Depots clients (passif)"
    poste_creances = "Créances banques autres"

    val_depots = get_valeur_poste_bilan(bilan_df, poste_depots,"2024")
    val_creances = get_valeur_poste_bilan(bilan_df, poste_creances, "2024")

    if val_depots is None or val_creances is None:
        raise ValueError("Valeurs bilan manquantes pour calcul (dépôts ou créances).")

    retrait_total = -val_depots * pourcentage

    inflow_df = extract_inflow_retrait_data(inflow_selections)
    inflow_df = inflow_df[inflow_df["Included_in_calculation"] == "Oui"]

    for _, row in inflow_df.iterrows():
        row_code = int(row["Row"]) 
        montant = row["Amount"]
        part_dans_inflow = montant / val_creances if val_creances > 0 else 0

        ajustement = impact_creances * retrait_total * poids_portefeuille * part_dans_inflow

        mask = df_74["row"] ==row_code
        df_74.loc[mask, "0010"] = df_74.loc[mask, "0010"] + ajustement 

    return df_74



########################################      NSFR      ########################################

def extract_asf_data_v2(user_selections=None):
    data = {
        "Row": ["0090", "0110", "0130", "Total"],
        "Rubrique": [
            "Stable retail deposits",
            "Other retail deposits",
            "ASF from other non-financial customers (except central banks)",
            "TOTAL "
        ],
        "Included_in_calculation": ["No", "Yes", "Yes", "Yes"],
        "Amount_less_than_6M": [70461721, 2687188132, 1854112318, 0],
        "Amount_6M_to_1Y": [263249, 156025150, 96897231, 0],
        "Amount_greater_than_1Y": [0, 90419066, 48761102, 0],
        "Available_stable_funding": [67188721, 2649311020, 1024265877, 0]
    }

    if user_selections:
        for row, selection in user_selections.items():
            if row in data["Row"]:
                idx = data["Row"].index(row)
                data["Included_in_calculation"][idx] = "Yes" if selection else "No"

    df = pd.DataFrame(data)

    included_mask = df["Included_in_calculation"] == "Yes"
    
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", "Available_stable_funding"]:
        df[col] = df[col].astype(float)

    df.loc[df["Row"] == "Total", "Amount_less_than_6M"] = df[included_mask & (df["Row"] != "Total")]["Amount_less_than_6M"].sum()
    df.loc[df["Row"] == "Total", "Amount_6M_to_1Y"] = df[included_mask & (df["Row"] != "Total")]["Amount_6M_to_1Y"].sum()
    df.loc[df["Row"] == "Total", "Amount_greater_than_1Y"] = df[included_mask & (df["Row"] != "Total")]["Amount_greater_than_1Y"].sum()
    df.loc[df["Row"] == "Total", "Available_stable_funding"] = df[included_mask & (df["Row"] != "Total")]["Available_stable_funding"].sum()

    df["Total_amount"] = df["Amount_less_than_6M"] + df["Amount_6M_to_1Y"] + df["Amount_greater_than_1Y"]

    total_selected = df[df["Row"] == "Total"]["Total_amount"].values[0]

    df["Poids_%_par_type"] = 0
    df.loc[included_mask, "Poids_%_par_type"] = df.loc[included_mask, "Total_amount"] / total_selected

    df["Poids < 6M"] = 0
    df["Poids 6M-1Y"] = 0
    df["Poids > 1Y"] = 0

    df.loc[included_mask, "Poids < 6M"] = df.loc[included_mask, "Amount_less_than_6M"] / df.loc[included_mask, "Total_amount"]
    df.loc[included_mask, "Poids 6M-1Y"] = df.loc[included_mask, "Amount_6M_to_1Y"] / df.loc[included_mask, "Total_amount"]
    df.loc[included_mask, "Poids > 1Y"] = df.loc[included_mask, "Amount_greater_than_1Y"] / df.loc[included_mask, "Total_amount"]

    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", "Total_amount", "Available_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{float(x):,.0f}".replace(",", " ") if x != "" else "")

    for col in ["Poids_%_par_type", "Poids < 6M", "Poids 6M-1Y", "Poids > 1Y"]:
        df[col] = df[col].apply(lambda x: f"{float(x):.2%}" if x != 0 else "0.00%")

    return df

def create_summary_table_asf_v2(user_selections=None):
    df = extract_asf_data_v2(user_selections)

    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": df["Rubrique"],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M": df["Amount_less_than_6M"],
        "Montant 6M-1A": df["Amount_6M_to_1Y"],
        "Montant > 1A": df["Amount_greater_than_1Y"],
        "Montant total": df["Total_amount"],
        "Poids % par type": df["Poids_%_par_type"],
        "Poids < 6M": df["Poids < 6M"],
        "Poids 6M-1A": df["Poids 6M-1Y"],
        "Poids > 1A": df["Poids > 1Y"],
        "Financement stable disponible": df["Available_stable_funding"]
    })

    return summary_table

def show_asf_tab_v2():
    st.markdown("###### Les nouvelles rubriques ASF avec montants mis à jour")

    asf_rows = ["0090", "0110", "0130"]
    asf_selections = {}

    cols = st.columns(len(asf_rows))
    for i, row in enumerate(asf_rows):
        with cols[i]:
            asf_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=(row != "0090"),
                key=f"asf_v2_{row}"
            )

    table_asf = create_summary_table_asf_v2(asf_selections)
    styled_asf = style_table(
        table_asf,
        highlight_columns=["Poids % par type", "Poids < 6M", "Poids 6M-1A", "Poids > 1A"]
    )
    st.markdown(styled_asf.to_html(), unsafe_allow_html=True)


import pandas as pd
import streamlit as st

def extract_rsf_data_financial_customers(user_selections=None):
    data = {
        "Row": ["730", "Total"],
        "Rubrique": [
            "Other loans and advances to financial customers",
            "TOTAL SELECTED ITEMS"
        ],
        "Included_in_calculation": ["Yes", "Yes"],
        "Amount_less_than_6M": [3035906378, 0],
        "Amount_6M_to_1Y": [264969774, 0],
        "Amount_greater_than_1Y": [662511893, 0],
        "Available_stable_funding": [1098587418, 0]
    }

    if user_selections:
        for row, selection in user_selections.items():
            if row in data["Row"]:
                idx = data["Row"].index(row)
                data["Included_in_calculation"][idx] = "Yes" if selection else "No"

    df = pd.DataFrame(data)

    included_mask = df["Included_in_calculation"] == "Yes"

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

    df["Total_amount"] = (
        df["Amount_less_than_6M"] + 
        df["Amount_6M_to_1Y"] + 
        df["Amount_greater_than_1Y"]
    )

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
        df[col] = df[col].apply(lambda x: f"{float(x):,.0f}".replace(",", " ") if x != "" else "")

    # Format percentages
    for col in ["Poids_%_par_type", "Poids < 6M", "Poids 6M-1Y", "Poids > 1Y"]:
        df[col] = df[col].apply(lambda x: f"{float(x):.2%}" if x != 0 else "0.00%")

    return df

def create_summary_table_rsf_financial_customers(user_selections=None):
    df = extract_rsf_data_financial_customers(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Other loans and advances to financial customers",
            "TOTAL"
        ],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M": df["Amount_less_than_6M"],
        "Montant 6M-1A": df["Amount_6M_to_1Y"],
        "Montant > 1A": df["Amount_greater_than_1Y"],
        "Montant total": df["Total_amount"],
        "Poids % par type": df["Poids_%_par_type"],
        "Poids < 6M": df["Poids < 6M"],
        "Poids 6M-1A": df["Poids 6M-1Y"],
        "Poids > 1A": df["Poids > 1Y"],
        "Financement stable disponible": df["Available_stable_funding"]
    })

    return summary_table

def show_asf_tab_financial_customers():
    st.markdown("###### Ligne ASF : other loans and advances to financial customers")

    row = "730"
    selection = st.checkbox("Inclure ligne 730", value=True, key="asf_730")
    user_selections = {row: selection}

    table_asf = create_summary_table_rsf_financial_customers(user_selections)
    styled_asf = style_table(table_asf, highlight_columns=["Poids % par type", "Poids < 6M", "Poids 6M-1A", "Poids > 1A"])
    st.markdown(styled_asf.to_html(), unsafe_allow_html=True)

def get_rsf_rows_details(user_selections=None):
    df = extract_rsf_data_financial_customers(user_selections)

    poids_df = pd.DataFrame({
        "Row": df["Row"],
        "Weight_less_than_6M": df["Poids < 6M"],
        "Weight_6M_to_1Y": df["Poids 6M-1Y"],
        "Weight_greater_than_1Y": df["Poids > 1Y"]
    })

    return poids_df
 

def propager_retrait_depots_vers_df80(df_80, bilan_df, pourcentage_retrait=0.15, poids_creances=0.5, annee="2025"):
    """
    Propage l'impact du stress 'Retrait Dépôts' vers la ligne 730 du df_80 en répartissant
    l'effet selon les poids de maturité.
    """
    df_80 = df_80.copy()

    try:
        # 1. Récupérer les poids de la ligne 730
        poids_df = get_rsf_rows_details()
        row_730_data = poids_df[poids_df["Row"] == "730"].iloc[0]

        poids_less_6m = float(row_730_data["Weight_less_than_6M"].strip('%')) / 100
        poids_6m_1y = float(row_730_data["Weight_6M_to_1Y"].strip('%')) / 100
        poids_greater_1y = float(row_730_data["Weight_greater_than_1Y"].strip('%')) / 100

        # 2. Récupérer les dépôts clients 2024 pour base du choc
        valeur_depots_2024 = get_valeur_poste_bilan(bilan_df, "Depots clients (passif)", str(int(annee) - 1))
        if valeur_depots_2024 is None:
            raise ValueError("Valeur des dépôts clients 2024 non trouvée.")

        # 3. Calculer le choc affectant les créances vers les clients financiers
        choc_creances = valeur_depots_2024 * pourcentage_retrait * poids_creances

        # 4. Répartition du choc par maturité (valeurs à soustraire)
        impact_less_6m = - choc_creances * poids_less_6m
        impact_6m_1y = - choc_creances * poids_6m_1y
        impact_greater_1y = - choc_creances * poids_greater_1y

        # 5. Appliquer les impacts à la ligne 730 du df_80
        mask_730 = df_80["row"] == 730
        if mask_730.any():
            idx = df_80[mask_730].index[0]
            df_80.at[idx, '0010'] = (df_80.at[idx, '0010'] if pd.notnull(df_80.at[idx, '0010']) else 0) + impact_less_6m
            df_80.at[idx, '0020'] = (df_80.at[idx, '0020'] if pd.notnull(df_80.at[idx, '0020']) else 0) + impact_6m_1y
            df_80.at[idx, '0030'] = (df_80.at[idx, '0030'] if pd.notnull(df_80.at[idx, '0030']) else 0) + impact_greater_1y
        else:
            raise ValueError("Ligne 730 non trouvée dans df_80")

    except Exception as e:
        print(f"Erreur dans propager_retrait_depots_vers_df80 : {str(e)}")

    return df_80


def propager_retrait_depots_vers_df81(df_81, bilan_df, pourcentage_retrait=0.15, annee="2025"):
    """
    Propage l'impact du stress 'Retrait Dépôts' vers les lignes 110 et 130 du df_81,
    en répartissant l'effet selon les poids de maturité (<6M, 6M–1Y, >1Y).

    :param df_81: DataFrame des ASF (feuille 81)
    :param bilan_df: DataFrame du bilan contenant les dépôts clients 2024
    :param pourcentage_retrait: pourcentage de retrait (ex : 0.15 pour 15%)
    :param annee: année de simulation (par défaut 2025)
    :return: df_81 mis à jour
    """
    df_81 = df_81.copy()

    try:
        # 1. Charger les poids par ligne ASF
        df_asf = extract_asf_data_v2()
        poids_df = pd.DataFrame({
            "Row": df_asf["Row"],
            "Poids_%_par_type": df_asf["Poids_%_par_type"].apply(lambda x: float(x.strip('%').replace(',', '.')) / 100 if isinstance(x, str) else 0),
            "Poids < 6M": df_asf["Poids < 6M"].apply(lambda x: float(x.strip('%').replace(',', '.')) / 100 if isinstance(x, str) else 0),
            "Poids 6M-1Y": df_asf["Poids 6M-1Y"].apply(lambda x: float(x.strip('%').replace(',', '.')) / 100 if isinstance(x, str) else 0),  # Make sure this matches
            "Poids > 1Y": df_asf["Poids > 1Y"].apply(lambda x: float(x.strip('%').replace(',', '.')) / 100 if isinstance(x, str) else 0)  # Space here
        })


        # 2. Dépôts clients 2024
        valeur_depots_2024 = get_valeur_poste_bilan(bilan_df, "Depots clients (passif)", str(int(annee) - 1))
        if valeur_depots_2024 is None:
            raise ValueError("Valeur des dépôts clients 2024 non trouvée dans le bilan.")

        # 3. Répartition de l'impact par ligne et par bucket
        lignes_cibles = ["0110", "0130"]
        colonnes = {"0010": "Poids < 6M", "0020": "Poids 6M-1Y", "0030": "Poids > 1Y"}
        for row_id in lignes_cibles:
            poids_ligne = poids_df[poids_df["Row"] == row_id]
            if poids_ligne.empty:
                continue

            poids_type = poids_ligne["Poids_%_par_type"].values[0]
            for col, poids_bucket_col in colonnes.items():
                poids_bucket = poids_ligne[poids_bucket_col].values[0]
                impact = - valeur_depots_2024 * pourcentage_retrait * poids_type * poids_bucket

                # Appliquer à df_81
                int_row = int(row_id)
                mask = df_81["row"] == int_row
                if mask.any():
                    idx = df_81[mask].index[0]
                    df_81.at[idx, col] = (df_81.at[idx, col] if pd.notnull(df_81.at[idx, col]) else 0) + impact
                else:
                    print(f"Ligne {row_id} non trouvée dans df_81.")

    except Exception as e:
        print(f"Erreur dans propager_retrait_depots_vers_df81 : {str(e)}")

    return df_81



























