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


mapping_bilan_LCR_NSFR_retrait_depots = {
    "Caisse Banque Centrale / nostro": [
        ("row_0050", "df_72"),  # LB: Withdrawable central bank reserves
        ("row_0150", "df_74"),  # Inflow: Monies due from central banks
        ("row_0030", "df_80"),  # RSF from central bank assets 
    ],
    "Créances banques autres": [
        ("row_0160", "df_74"),  # Inflow: Monies due from financial customers
        ("row_0100", "df_74"),  # Inflow: Monies due from CB + financial customers
        ("row_0730", "df_80"),  # NSFR: RSF from loans to financial customers
    ],
    "Créances hypothécaires": [
        ("row_0030", "df_74"),  # Inflow – monies from non financial customers  
        ("row_0640", "df_80"),  # RSF from loans to finantial customers
        
    ],
    "Créances clientèle": [
        ("row_0060", "df_74"),  # Inflow – Monies from retail customers
        ("row_0070", "df_74"),  # Inflow – Monies from non financial corporate 
        ("row_0080", "df_74"),  # Inflow – Monies from ..
        ("row_0090", "df_74"),  # Inflow – Monies from ..
        ("row_0810", "df_80"), # RSF from loans to non finantial customers 
    ],
    "Portefeuille": [
        ("row_0190", "df_74"),  ## inflow – Monies from ..
        #("row_0570", "df_80"),  # RSF from securities other than liquid assets non hqla
        ("row_0580", "df_80"),  # RSF from securities other than liquid assets non hqla
    ],
    "Participations": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_0600", "df_80"),  # RSF non hqla traded equities
    ],
    "Immobilisations et Autres Actifs": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_1030", "df_80"), # RSF from other assets
    ],
    "Dettes envers les établissements de crédit (passif)": [
        ("row_0230", "df_73"), # outflow non operational deposits by finantial customers
        ("row_1350", "df_73"), #outflow intra group non operational deposits
        ("row_0270", "df_81"), # ASF from finantial cus and central banks - liabilities provided by finantial customers
    ],
    "Depots clients (passif)": [
        ("row_0035", "df_73"),("row_0040", "df_73"),("row_0060", "df_73"),("row_0070", "df_73"),("row_0080", "df_73"),("row_0090", "df_73"),("row_0100", "df_73"),("row_0110", "df_73"),   ## outflow retail deposits
        ("row_0240", "df_73"),  ## outflow Non-operational deposits by other customers
        ("row_0250", "df_73"), ## outflow covered by DGS
        ("row_0260", "df_73"), ## outflow not covered by DGS
        #("row_0070", "df_81"), #ASF from retail deposits
        ("row_0090", "df_81"), #ASF from retail deposits
        #("row_0130", "df_81"), #ASF from other non finantial customers
        ("row_0160", "df_81"), #ASF from other non finantial customers

    ],
    "Autres passifs (passif)": [
        ("row_0885", "df_73"), ## outflow other liabilities
        ("row_0890", "df_73"), ## outflow other liabilities
        ("row_0918", "df_73"), ## outflow other liabilities
        ("row_0390", "df_81"), #ASF from other liabilities
    ],
    "Comptes de régularisation (passif)": [
        ("row_0890", "df_73"), ## outflow other liabilities
        ("row_0430", "df_81"), #ASF from other liabilities
    ],
    "Provisions (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_0430", "df_81"), #ASF from other liabilities
    ],
    "Capital souscrit (passif)": [
        ("row_0030", "df_81"), # ASF common equity tier 1
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
    ],
    "Primes émission (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_0030", "df_81"), # ASF common equity tier 1
    ],
    "Réserves (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_0030", "df_81"), # ASF common equity tier 1
    ],
    "Report à nouveau (passif)": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_0030", "df_81"), # ASF common equity tier 1
    ],
    "Income Statement - Résultat de l'exercice": [
        ("row_X", "df_72"),  # Non considéré LCR
        ("row_X", "df_73"),  # Non considéré LCR
        ("row_X", "df_74"),  # Non considéré LCR
        ("row_0030", "df_81"), # ASF common equity tier 1
    ],
}

########################################      LCR      ########################################
def propager_retrait_depots_vers_df72(df_72, bilan_df, annee="2024", pourcentage=0.15, horizon=1, poids_portefeuille=0.15):
    """
    Propage l'impact du retrait massif des dépôts vers la ligne 70 de df_72.
    Formule : row_70 = row_70 - impact_portefeuille
    """
    df_72 = df_72.copy()

    poste_depots = "Depots clients (passif)"

    # Récupérer la valeur des dépôts en année de référence
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_depots, "2024")
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_depots}' introuvable ou sans valeur pour 2024.")

    # Calcul de l'impact portefeuille
    retrait_total = (valeur_initiale * pourcentage) / horizon
    impact_portefeuille = retrait_total * poids_portefeuille

    # Appliquer à la ligne row 70 de df_72 (colonne "0010")
    mask = df_72["row"] == 70
    df_72.loc[mask, "0010"] = df_72.loc[mask, "0010"] - impact_portefeuille

    return df_72





def propager_retrait_depots_vers_df73(df_73, bilan_df, annee="2024", pourcentage=0.15, horizon=1, poids_portefeuille=0.15):
    """
    Propage l'impact du retrait massif des dépôts vers la ligne 70 de df_72.
    Formule : row_70 = row_70 - impact_portefeuille
    """
    df_73 = df_73.copy()

    poste_depots = "Depots clients (passif)"

    # Récupérer la valeur des dépôts en année de référence
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_depots,"2024")
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_depots}' introuvable ou sans valeur pour.")

    # Calcul de l'impact portefeuille
    retrait_total = (valeur_initiale * pourcentage) / horizon
    impact_portefeuille = retrait_total * poids_portefeuille

    # Appliquer à la ligne row 70 de df_72 (colonne "0010")
    mask = df_73["row"] == 70
    df_73.loc[mask, "0010"] = df_73.loc[mask, "0010"] - impact_portefeuille

    return df_73
def propager_retrait_depots_vers_df74(df_74, bilan_df, annee="2024", pourcentage=0.15, horizon=1, poids_portefeuille=0.15):
    """
    Propage l'impact du retrait massif des dépôts vers la ligne 70 de df_72.
    Formule : row_70 = row_70 - impact_portefeuille
    """
    df_74 = df_74.copy()

    poste_depots = "Depots clients (passif)"

    # Récupérer la valeur des dépôts en année de référence
    valeur_initiale = get_valeur_poste_bilan(bilan_df, poste_depots, "2024")
    if valeur_initiale is None:
        raise ValueError(f"Poste '{poste_depots}' introuvable ou sans valeur pour {annee}.")

    # Calcul de l'impact portefeuille
    retrait_total = (valeur_initiale * pourcentage) / horizon
    impact_portefeuille = retrait_total * poids_portefeuille

    # Appliquer à la ligne row 70 de df_72 (colonne "0010")
    mask = df_74["row"] == 70
    df_74.loc[mask, "0010"] = df_74.loc[mask, "0010"] - impact_portefeuille

    return df_74


########################################      NSFR      ########################################




def get_asf_rows_details(user_selections=None):
    """Returns details for ASF rows impacted by deposit withdrawals"""
    data = {
        "Row": ["0090", "0110", "0130"],
        "Rubrique": [
            "Stable retail deposits",
            "Other retail deposits",
            "ASF from other non-financial customers (except central banks)"
        ],
        "Included_in_calculation": ["No", "Yes", "Yes"],  # Default 0090 not included
        "Amount": [70461721, 2687188132, 1854112318],
        "ASF_factor": [0.95, 0.90, 1.00],  # Adjust factors as needed
        "ASF_contribution": [70461721*0.95, 2687188132*0.90, 1854112318*1.00]
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
    df["ASF_contribution"] = df["Amount"] * df["ASF_factor"] * included_mask.astype(int)
    
    # Format numbers
    for col in ["Amount", "ASF_contribution"]:
        df[col] = df[col].apply(lambda x: f"{x:,.0f}".replace(",", " "))
    
    return df

def create_asf_rows_summary_table(user_selections=None):
    """Creates summary table for ASF rows"""
    df = get_asf_rows_details(user_selections)
    
    summary_table = pd.DataFrame({
        "Row": df["Row"],
        "Rubrique": df["Rubrique"],
        "Inclus dans le calcul": ["Oui" if x == "Yes" else "Non" for x in df["Included_in_calculation"]],
        "Montant": df["Amount"],
        "Facteur ASF": df["ASF_factor"],
        "Contribution ASF": df["ASF_contribution"]
    })
    
    return summary_table

def show_asf_lines_tab():
    """Displays ASF lines tab in Streamlit"""
    st.markdown("###### Rubriques COREP ASF impactées par le retrait de dépôts (lignes 0090, 0110, 0130)")

    # Create checkboxes for each row
    asf_rows = ["0090", "0110", "0130"]
    asf_selections = {}

    cols = st.columns(len(asf_rows))
    for i, row in enumerate(asf_rows):
        with cols[i]:
            # Default to True except for 0090
            default_value = False if row == "0090" else True
            asf_selections[row] = st.checkbox(
                f"Inclure ligne {row}",
                value=default_value,
                key=f"asf_row_{row}"
            )

    # Get table with user selections
    table = create_asf_rows_summary_table(asf_selections)
    styled = style_table(table, highlight_columns=["Facteur ASF", "Contribution ASF"])
    st.markdown(styled.to_html(), unsafe_allow_html=True)

def propager_impact_vers_df81_retrait_depots(df_81, impact_total, annee="2025"):
    """
    Propage l'impact du retrait de dépôts vers df_81 (ASF)
    Lignes impactées: 0090, 0110, 0130
    """
    df_81 = df_81.copy()
    
    try:
        # Get ASF weights from user selections
        asf_selections = {
            "0090": st.session_state.get(f"asf_row_0090", False),
            "0110": st.session_state.get(f"asf_row_0110", True),
            "0130": st.session_state.get(f"asf_row_0130", True)
        }
        asf_df = get_asf_rows_details(asf_selections)
        
        # Calculate total ASF from included rows
        included_mask = asf_df["Included_in_calculation"] == "Yes"
        total_asf = asf_df.loc[included_mask, "Amount"].astype(float).sum()
        
        if total_asf == 0:
            return df_81
            
        # Calculate impact per row based on their proportion in total ASF
        for _, row in asf_df[included_mask].iterrows():
            row_impact = (float(row["Amount"].replace(" ", "")) / total_asf) * impact_total
            
            # Apply to corresponding row in df_81
            mask = df_81["row"] == int(row["Row"])
            if mask.any():
                idx = df_81[mask].index[0]
                df_81.at[idx, '0010'] = (df_81.at[idx, '0010'] if pd.notnull(df_81.at[idx, '0010']) else 0) - row_impact
                
    except Exception as e:
        print(f"Erreur dans propager_impact_vers_df81_retrait_depots: {str(e)}")
    
    return df_81

def propager_impact_vers_df80_retrait_depots(df_80, impact_total, annee="2025"):
    """
    Propage l'impact du retrait de dépôts vers df_80 (RSF)
    Ligne impactée: 0730 (other loans and advances to financial customers)
    """
    df_80 = df_80.copy()
    
    try:
        # Get RSF weights (example - adjust based on your actual data)
        rsf_factors = {
            "less_than_6M": 0.10,
            "6M_to_1Y": 0.50,
            "greater_than_1Y": 1.00
        }
        
        # Distribute impact across maturities (example distribution - adjust as needed)
        impact_less_6m = impact_total * 0.3  # 30% <6M
        impact_6m_1y = impact_total * 0.4    # 40% 6M-1Y
        impact_greater_1y = impact_total * 0.3  # 30% >1Y
        
        # Apply to row 0730
        mask = df_80["row"] == 730
        if mask.any():
            idx = df_80[mask].index[0]
            df_80.at[idx, '0010'] = (df_80.at[idx, '0010'] if pd.notnull(df_80.at[idx, '0010']) else 0) + impact_less_6m
            df_80.at[idx, '0020'] = (df_80.at[idx, '0020'] if pd.notnull(df_80.at[idx, '0020']) else 0) + impact_6m_1y
            df_80.at[idx, '0030'] = (df_80.at[idx, '0030'] if pd.notnull(df_80.at[idx, '0030']) else 0) + impact_greater_1y
                
    except Exception as e:
        print(f"Erreur dans propager_impact_vers_df80_retrait_depots: {str(e)}")
    
    return df_80









########################################      old code      ########################################

def get_delta_bilan(original_df, stressed_df, poste_bilan, annee):
    """
    Calcule le delta (différence) entre la valeur originale et stressée pour un poste donné.

    Args:
        original_df (DataFrame): Le bilan original.
        stressed_df (DataFrame): Le bilan stressé.
        poste_bilan (str): Nom du poste.
        annee (str): Année considérée.

    Returns:
        float: La différence (delta > 0 si diminution).
    """
    val_orig = original_df.loc[original_df["Poste du Bilan"] == poste_bilan, annee].values[0]
    val_stressed = stressed_df.loc[stressed_df["Poste du Bilan"] == poste_bilan, annee].values[0]
    return val_orig - val_stressed

def get_mapping_df_row(post_bilan):
    """
    À partir d’un poste du bilan, retourne les lignes correspondantes et les DataFrames associées.

    Args:
        post_bilan (str): Le nom du poste du bilan (clé du dictionnaire `mapping_bilan_LCR_NSFR`).

    Returns:
        List[Tuple[int, str]]: Liste des tuples (row_number, df_name) .
    """
    result = []
    if post_bilan not in mapping_bilan_LCR_NSFR_retrait_depots:
        raise ValueError(f"Poste '{post_bilan}' non trouvé dans le mapping.")

    for row_str, feuille in mapping_bilan_LCR_NSFR_retrait_depots[post_bilan]:
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



def propager_delta_vers_COREP_LCR(poste_bilan, delta, df_72, df_73, df_74, ponderations=None):
    lignes = get_mapping_df_row(poste_bilan)
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
        df_72.loc[mask, "0010"] = df_72.loc[mask, "0010"] - part_delta

    for (row_num, _), poids in zip(lignes_73, ponderations_73):
        part_delta = delta * poids
        print("part delta in df_73 = ", part_delta)
        mask = df_73["row"] == row_num
        df_73.loc[mask, "0010"] = df_73.loc[mask, "0010"] + part_delta

    for (row_num, _), poids in zip(lignes_74, ponderations_74):
        part_delta = delta * poids
        print("part delta in df_74 = ", part_delta)
        mask = df_74["row"] == row_num
        df_74.loc[mask, "0010"] = df_74.loc[mask, "0010"] - part_delta

    return df_72, df_73, df_74


def propager_delta_vers_COREP_NSFR(poste_bilan, delta, df_80, df_81, ponderations=None):
    lignes = get_mapping_df_row(poste_bilan)
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
        df_80.loc[mask, "0010"] = df_80.loc[mask, "0010"] - part_delta

    # Apply delta to df_81
    for (row_num, _), poids in zip(lignes_81, ponderations_81):
        part_delta = delta * poids
        print("part delta in df_81 = ", part_delta)
        mask = df_81["row"] == row_num
        df_81.loc[mask, "0010"] = df_81.loc[mask, "0010"] - part_delta

    return df_80, df_81








