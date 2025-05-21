import pandas as pd
import streamlit as st
from backend.stress_test.event1 import ajuster_annees_suivantes,get_valeur_poste_bilan
from config import style_table
from backend.stress_test import event1 as bst



##############################################  Constantes  ####################################################


def part_loans_mb_outflow():
    bilan = bst.charger_bilan()
    df_72, df_73, df_74 = bst.charger_lcr()
    try:
        valeur_outflow_mb = df_73.loc[df_73['row'] == 230]['0010'].values[0]
        print("valeur_outflow_mb = ", valeur_outflow_mb)
        dette_etab_credit = get_valeur_poste_bilan(bilan, "Dettes envers les établissements de crédit (passif)","2024")
        print("dette_etab_credit = ", dette_etab_credit)
        return round((valeur_outflow_mb / dette_etab_credit) * 100, 2) if dette_etab_credit else 0.0
    except Exception as e:
        print(f"[Erreur part_loans_mb_outflow] : {e}")
        return 0.0

def part_credit_clientele_inflow():
    bilan = bst.charger_bilan()
    df_72, df_73, df_74 = bst.charger_lcr()
    try:
        valeur_inflow_credit = df_74.loc[df_74['row'] == 50]['0010'].values[0]
        print("valeur_inflow_credit = ", valeur_inflow_credit)
        creance_clientele = get_valeur_poste_bilan(bilan, "Créances clientèle", "2024")
        print("creance_clientele = ", creance_clientele)
        return round((valeur_inflow_credit / creance_clientele) * 100, 2) if creance_clientele else 0.0
    except Exception as e:
        print(f"[Erreur part_credit_clientele_inflow] : {e}")
        return 0.0

def part_depots_mb_inflow():
    bilan = bst.charger_bilan()
    df_72, df_73, df_74 = bst.charger_lcr()
    try:
        valeur_inflow_mb = df_74.loc[df_74['row'] == 160]['0010'].values[0]
        print("valeur_inflow_mb = ", valeur_inflow_mb)
        creance_banques = get_valeur_poste_bilan(bilan, "Créances banques autres", "2024")
        print("creance_banques = ", creance_banques)
        return round((valeur_inflow_mb / creance_banques) * 100, 2) if creance_banques else 0.0
    except Exception as e:
        print(f"[Erreur part_depots_mb_inflow] : {e}")
        return 0.0






#####################################  IMPACT PNU SUR BILAN  ##########################################



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


########################################      LCR      ########################################



def propager_impact_portefeuille_vers_df72(df_72, bilan_df, annee="2024", pourcentage=0.1, horizon=3, poids_portefeuille=0.15):
    """
    Propagation de l'impact du portefeuille vers la ligne row_0070 de df_72 suite au tirage PNU.
    On applique : row_0070 = row_0070 - impact_portefeuille
    """
    df_72 = df_72.copy()
    
    poste_engagements = "Engagements de garantie donnés"

    # Récupérer la valeur initiale du poste engagements
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, "2024")
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
    part_mb = part_depots_mb_inflow()
    print(f"Part Dépôts MB (Inflow) : {part_mb}")
    part_credit = part_credit_clientele_inflow()
    print(f"Part Crédits Clientèle (Inflow) : {part_credit}")

    # Étape 2 : tirage total
    poste_engagements = "Engagements de garantie donnés"
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, "2024")
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_engagements}' introuvable pour {annee}")

    tirage_total = (valeur_initiale * pourcentage) / horizon
    print(f"Tirage total = {tirage_total}")

    # Étape 3 : capital plannings
    capital_creances = get_capital_planning(bilan_df, "Créances clientèle", annee=str(int(annee) + 1))
    capital_banques = get_capital_planning(bilan_df, "Créances banques autres", annee=str(int(annee) + 1))
    print(f"Capital créances : {capital_creances}")
    print(f"Capital banques : {capital_banques}")

    # Étape 4 : application de l’impact pour chaque année cible
    

    #impact_160 = (part_mb / 100) * capital_banques
    #impact_50 = (part_credit / 100) * (capital_creances + tirage_total)
    impact_50 = (part_credit / 100) * tirage_total
    impact_160 = 0

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
    pt_out_loans = part_loans_mb_outflow() / 100
    print("pt_out_loans",pt_out_loans)
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_engagements, "2024")
    print(f"Valeur initiale pourrrrrrrrr {poste_engagements} en {annee} : {valeur_initiale}")
    tirage_total = (valeur_initiale * pourcentage) / horizon

    # Pour rows 480 et 499
    retail = get_valeur_poste_bilan(bilan_df, poste_retail, "2024")
    hypo = get_valeur_poste_bilan(bilan_df, poste_hypo, "2024")
    corpo = get_valeur_poste_bilan(bilan_df, poste_corpo, "2024")

    # Impact dettes annuel
    impact_annuel_dettes = tirage_total * poids_dettes
    print("imp dette", impact_annuel_dettes)
    

    impact_230 = pt_out_loans * impact_annuel_dettes 
    print(f"Impact 230 : {impact_230}")
    impact_480 = - (pourcentage * retail) / horizon
    print(f"Impact 480 : {impact_480}")
    impact_490 =  ((pourcentage * hypo) + (pourcentage * corpo)) / horizon
    print(f"Impact 490 : {impact_490}")


    df_73.loc[df_73["row"] == 230, "0010"] += impact_230
    df_73.loc[df_73["row"] == 480, "0010"] += impact_480
    df_73.loc[df_73["row"] == 490, "0010"] -= impact_490

    return df_73


#################################       NSFR       #####################################
def extract_other_liabilities_data(user_selections=None):
    # Data for "Other liabilities" only - no Total row
    data = {
        "Row": ["0300"],
        "Rubrique": [
            "Other liabilities",
        ],
        "Included_in_calculation": ["Yes"],
        "Amount_less_than_6M": [466211782],
        "Amount_6M_to_1Y": [108096124],
        "Amount_greater_than_1Y": [1435000000],
        "Available_stable_funding": [1489048062]
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
                "Total_amount", "Available_stable_funding"]:
        df[col] = df[col].apply(lambda x: f"{x:,.0f}".replace(",", " "))
    
    return df

def create_summary_table_other_liabilities(user_selections=None):
    df = extract_other_liabilities_data(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": [
            "Other liabilities",
        ],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M": df["Amount_less_than_6M"],
        "Montant 6M-1A": df["Amount_6M_to_1Y"],
        "Montant > 1A": df["Amount_greater_than_1Y"],
        "Montant total": df["Total_amount"],
        "Poids < 6M": df["Weight_less_than_6M"],
        "Poids 6M-1A": df["Weight_6M_to_1Y"],
        "Poids > 1A": df["Weight_greater_than_1Y"],
        "Financement stable disponible": df["Available_stable_funding"]
    })
    
    return summary_table

def show_other_liabilities_tab():
    st.markdown("###### Les rubriques COREP impactées par l'évenement dans Other Liabilities")

    # Create checkbox for Other Liabilities row
    other_liab_rows = ["0300"]
    other_liab_selections = {}

    cols = st.columns(len(other_liab_rows))
    for i, row in enumerate(other_liab_rows):
        with cols[i]:
            other_liab_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=True,  # Default to checked
                key=f"other_liab_{row}"
            )

    # Get Other Liabilities table with user selections
    table_other_liab = create_summary_table_other_liabilities(other_liab_selections)
    styled_other_liab = style_table(table_other_liab, highlight_columns=["Poids < 6M", "Poids 6M-1A", "Poids > 1A"])
    st.markdown(styled_other_liab.to_html(), unsafe_allow_html=True)


def get_rsf_rows_details(user_selections=None):
    data = {
        "Row": ["820", "1060"],
        "Rubrique": [
            "Other loans to non-financial customers (unencumbered or encumbered < 1 year)",
            "Committed facilities"
        ],
        "Included_in_calculation": ["Yes", "Yes"],
        "Amount_less_than_6M": [1398399253, 515703],
        "Amount_6M_to_1Y": [57733609, 2748191],
        "Amount_greater_than_1Y": [1359266078, 1175868996],
        "RSF_factor_less_than_6M": [0.50, 0.05],
        "RSF_factor_6M_to_1Y": [0.50, 0.05],
        "RSF_factor_greater_than_1Y": [0.85, 0.05],
        "Required_stable_funding": [1883442598, 58956645]
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
    
    # Verify RSF calculation
    df["RSF_calculated"] = (
        df["Amount_less_than_6M"] * df["RSF_factor_less_than_6M"] +
        df["Amount_6M_to_1Y"] * df["RSF_factor_6M_to_1Y"] +
        df["Amount_greater_than_1Y"] * df["RSF_factor_greater_than_1Y"]
    )
    
    # Format percentages
    for col in ["Weight_less_than_6M", "Weight_6M_to_1Y", "Weight_greater_than_1Y"]:
        df[col] = df[col].apply(lambda x: f"{x:.2%}" if x != 0 else "0.00%")
    
    # Format large numbers
    for col in ["Amount_less_than_6M", "Amount_6M_to_1Y", "Amount_greater_than_1Y", 
                "Total_amount", "Required_stable_funding", "RSF_calculated"]:
        df[col] = df[col].apply(lambda x: f"{x:,.0f}".replace(",", " "))
    
    return df

def create_rsf_rows_summary_table(user_selections=None):
    df = get_rsf_rows_details(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": df["Rubrique"],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant < 6M": df["Amount_less_than_6M"],
        "Montant 6M-1A": df["Amount_6M_to_1Y"],
        "Montant > 1A": df["Amount_greater_than_1Y"],
        "Montant total": df["Total_amount"],
        "Poids < 6M": df["Weight_less_than_6M"],
        "Poids 6M-1A": df["Weight_6M_to_1Y"],
        "Poids > 1A": df["Weight_greater_than_1Y"],
        "Financement stable requis": df["Required_stable_funding"]
    })
    
    return summary_table

def show_rsf_lines_tab():
    st.markdown("###### Les rubriques COREP impactées par l'évenement dans lignes 820 et 1060")

    # Create checkboxes for each row
    rsf_rows = ["820", "1060"]
    rsf_selections = {}

    cols = st.columns(len(rsf_rows))
    for i, row in enumerate(rsf_rows):
        with cols[i]:
            rsf_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=True,  # Default to checked
                key=f"rsf_row_{row}"
            )

    # Get table with user selections
    table = create_rsf_rows_summary_table(rsf_selections)
    styled = style_table(table, highlight_columns=["Poids < 6M", "Poids 6M-1A", "Poids > 1A"])
    st.markdown(styled.to_html(), unsafe_allow_html=True)

    
def propager_impact_vers_df81(df_81, bilan_df, annee="2024", pourcentage=0.1, horizon=3, poids_dettes=0.85):
    """
    Propage l'impact du tirage PNU vers df_81 (ligne 300 - ASF) en utilisant les poids de maturité.
    """
    df_81 = df_81.copy()

    try:
        # 1. Récupérer les poids à partir de la fonction extract_other_liabilities_data
        poids_df = extract_other_liabilities_data()
        row_300_data = poids_df[poids_df["Row"] == "0300"].iloc[0]

        poids_less_6m = float(row_300_data["Weight_less_than_6M"].strip('%')) / 100
        poids_6m_1y = float(row_300_data["Weight_6M_to_1Y"].strip('%')) / 100
        poids_greater_1y = float(row_300_data["Weight_greater_than_1Y"].strip('%')) / 100

        # 2. Calculer l'impact total du tirage PNU
        poste_engagements = "Engagements de garantie donnés"
        poste_dettes = "Dettes envers les établissements de crédit (passif)"

        valeur_engagements = get_valeur_poste_bilan(bilan_df, poste_engagements, "2024")
        if valeur_engagements is None:
            raise ValueError(f"Valeur engagements non trouvée pour 2024 df 81")

        tirage_total = (valeur_engagements * pourcentage) / horizon
        impact_dette = tirage_total * poids_dettes

        # 3. Récupérer le capital planning
        #capital_dette = get_capital_planning(bilan_df, poste_dettes, annee=str(int(annee)))
        #total_impact = impact_dette + capital_dette

        # 4. Répartir par maturité
        amount_less_6m = impact_dette * poids_less_6m
        amount_6m_1y = impact_dette * poids_6m_1y
        amount_greater_1y = impact_dette * poids_greater_1y

        # 5. Appliquer à la ligne 300
        mask_300 = df_81["row"] == 300
        if mask_300.any():
            idx = df_81[mask_300].index[0]
            df_81.at[idx, '0010'] = (df_81.at[idx, '0010'] if pd.notnull(df_81.at[idx, '0010']) else 0) + amount_less_6m
            df_81.at[idx, '0020'] = (df_81.at[idx, '0020'] if pd.notnull(df_81.at[idx, '0020']) else 0) + amount_6m_1y
            df_81.at[idx, '0030'] = (df_81.at[idx, '0030'] if pd.notnull(df_81.at[idx, '0030']) else 0) + amount_greater_1y

    except IndexError:
        print("Ligne 0300 non trouvée dans les données Other Liabilities")
    except Exception as e:
        print(f"Erreur dans propager_impact_vers_df81: {str(e)}")

    return df_81

def propager_impact_vers_df80(df_80, bilan_df, annee="2024", pourcentage=0.1, horizon=3):
    """
    Propage l'impact du tirage PNU vers df_80 (lignes 820 et 1060) en utilisant les poids de maturité.
    """
    df_80 = df_80.copy()

    try:
        # 1. Récupérer les poids à partir de la fonction get_rsf_rows_details
        poids_df = get_rsf_rows_details()
        
        # Poids pour la ligne 820
        row_820_data = poids_df[poids_df["Row"] == "820"].iloc[0]
        poids_820_less_6m = float(row_820_data["Weight_less_than_6M"].strip('%')) / 100
        poids_820_6m_1y = float(row_820_data["Weight_6M_to_1Y"].strip('%')) / 100
        poids_820_greater_1y = float(row_820_data["Weight_greater_than_1Y"].strip('%')) / 100
        
        # Poids pour la ligne 1060
        row_1060_data = poids_df[poids_df["Row"] == "1060"].iloc[0]
        poids_1060_less_6m = float(row_1060_data["Weight_less_than_6M"].strip('%')) / 100
        poids_1060_6m_1y = float(row_1060_data["Weight_6M_to_1Y"].strip('%')) / 100
        poids_1060_greater_1y = float(row_1060_data["Weight_greater_than_1Y"].strip('%')) / 100

        # 2. Calculer l'impact total du tirage PNU
        poste_engagements = "Engagements de garantie donnés"
        poste_creances = "Créances clientèle"

        valeur_engagements = get_valeur_poste_bilan(bilan_df, poste_engagements,"2024")
        if valeur_engagements is None:
            raise ValueError(f"Valeur engagements non trouvée pour 2024")

        tirage_total = (valeur_engagements * pourcentage) / horizon
        impact_creances = tirage_total
        
        # 3. Récupérer le capital planning
        #capital_creances = get_capital_planning(bilan_df, poste_creances, annee=str(int(annee)))
        total_impact_820 = impact_creances 
        total_impact_1060 = impact_creances

        # 4. Répartir par maturité pour la ligne 820 (ajout)
        amount_820_less_6m = total_impact_820 * poids_820_less_6m
        amount_820_6m_1y = total_impact_820 * poids_820_6m_1y
        amount_820_greater_1y = total_impact_820 * poids_820_greater_1y

        # 5. Répartir par maturité pour la ligne 1060 (retrait)
        amount_1060_less_6m = -total_impact_1060 * poids_1060_less_6m
        amount_1060_6m_1y = -total_impact_1060 * poids_1060_6m_1y
        amount_1060_greater_1y = -total_impact_1060 * poids_1060_greater_1y

        # 6. Appliquer à la ligne 820
        mask_820 = df_80["row"] == 820
        if mask_820.any():
            idx = df_80[mask_820].index[0]
            df_80.at[idx, '0010'] = (df_80.at[idx, '0010'] if pd.notnull(df_80.at[idx, '0010']) else 0) + amount_820_less_6m
            df_80.at[idx, '0020'] = (df_80.at[idx, '0020'] if pd.notnull(df_80.at[idx, '0020']) else 0) + amount_820_6m_1y
            df_80.at[idx, '0030'] = (df_80.at[idx, '0030'] if pd.notnull(df_80.at[idx, '0030']) else 0) + amount_820_greater_1y

        # 7. Appliquer à la ligne 1060
        mask_1060 = df_80["row"] == 1060
        if mask_1060.any():
            idx = df_80[mask_1060].index[0]
            df_80.at[idx, '0010'] = (df_80.at[idx, '0010'] if pd.notnull(df_80.at[idx, '0010']) else 0) + amount_1060_less_6m
            df_80.at[idx, '0020'] = (df_80.at[idx, '0020'] if pd.notnull(df_80.at[idx, '0020']) else 0) + amount_1060_6m_1y
            df_80.at[idx, '0030'] = (df_80.at[idx, '0030'] if pd.notnull(df_80.at[idx, '0030']) else 0) + amount_1060_greater_1y

    except IndexError as e:
        print(f"Ligne non trouvée dans les données RSF: {str(e)}")
    except Exception as e:
        print(f"Erreur dans propager_impact_vers_df80: {str(e)}")

    return df_80