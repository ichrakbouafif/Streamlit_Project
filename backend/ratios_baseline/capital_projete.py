import pandas as pd
import numpy as np
import streamlit as st
import os
# Mappings globaux
noms_lignes_c0100 = {
    15: "TIER 1 CAPITAL",
    20: "COMMON EQUITY TIER 1 CAPITAL",
    30: "Capital instruments and share premium eligible as CET1 Capital",
    40: "Fully paid up capital instruments",
    45: "Of which: Capital instruments subscribed by public authorities in emergency situations",
    50: "Memorandum item: Capital instruments not eligible",
    60: "Share premium",
    70: "(-) Own CET1 instruments",
    80: "(-) Direct holdings of CET1 instruments",
    90: "(-) Indirect holdings of CET1 instruments",
    91: "(-) Synthetic holdings of CET1 instruments",
    92: "(-) Actual or contingent obligations to purchase own CET1 instruments",
    130: "Retained earnings",
    140: "Previous years retained earnings",
    150: "Profit or loss eligible",
    160: "Profit or loss attributable to owners of the parent",
    170: "(-) Part of interim or year-end profit not eligible",
    180: "Accumulated other comprehensive income",
    200: "Other reserves",
    210: "Funds for general banking risk",
    220: "Transitional adjustments due to grandfathered CET1 Capital instruments",
    230: "Minority interest given recognition in CET1 capital",
    240: "Transitional adjustments due to additional minority interests",
    250: "Adjustments to CET1 due to prudential filters",
    260: "(-) Increases in equity resulting from securitised assets",
    270: "Cash flow hedge reserve",
    280: "Cumulative gains and losses due to changes in own credit risk on fair valued liabilities",
    285: "Fair value gains and losses arising from the institution's own credit risk related to derivative liabilities",
    290: "(-) Value adjustments due to the requirements for prudent valuation",
    300: "(-) Goodwill",
    310: "(-) Goodwill accounted for as intangible asset",
    320: "(-) Goodwill included in the valuation of significant investments",
    330: "Deferred tax liabilities associated to goodwill",
    335: "Accounting revaluation of subsidiaries' goodwill derived from the consolidation of subsidiaries attributable to third persons",
    340: "(-) Other intangible assets",
    350: "(-) Other intangible assets before deduction of deferred tax liabilities",
    352: "(-) Of which: software assets accounted for as intangible assets before deduction of deferred tax liabilities",
    360: "Deferred tax liabilities associated to other intangible assets",
    362: "Of which: Deferred tax liabilities associated with software assets accounted for as intangible assets",
    365: "Accounting revaluation of subsidiaries' other intangible assets derived from the consolidation of subsidiaries attributable to third persons",
    370: "(-) Deferred tax assets that rely on future profitability and do not arise from temporary differences net of associated tax liabilities",
    380: "(-) IRB shortfall of credit risk adjustments to expected losses",
    390: "(-)Defined benefit pension fund assets",
    400: "(-)Defined benefit pension fund assets",
    410: "Deferred tax liabilities associated to defined benefit pension fund assets",
    420: "Defined benefit pension fund assets which the institution has an unrestricted ability to use",
    430: "(-) Reciprocal cross holdings in CET1 Capital",
    440: "(-) Excess of deduction from AT1 items over AT1 Capital (see 1.2.10)",
    450: "(-) Qualifying holdings outside the financial sector which can alternatively be subject to a 1.250% risk weight",
    460: "(-) Securitisation positions which can alternatively be subject to a 1.250% risk weight",
    470: "(-) Free deliveries which can alternatively be subject to a 1.250% risk weight",
    471: "(-) Positions in a basket for which an institution cannot determine the risk weight under the IRB approach, and can alternatively be subject to a 1.250% risk weight",
    472: "(-) Equity exposures under an internal models approach which can alternatively be subject to a 1.250% risk weight",
    480: "(-) CET1 instruments of financial sector entities where the institution does not have a significant investment",
    490: "(-) Deductible deferred tax assets that rely on future profitability and arise from temporary differences",
    500: "(-) CET1 instruments of financial sector entities where the institution has a significant investment",
    510: "(-) Amount exceeding the 17.65% threshold",
    511: "(-) Amount exceeding the 17.65% threshold related to CET1 instruments of financial sector entities where the institution has a significant investment",
    512: "(-) Amount exceeding the 17.65% threshold related to deferred tax assets arising from temporary differences",
    513: "(-) Insufficient coverage for non-performing exposures",
    514: "(-) Minimum value commitment shortfalls",
    515: "(-) Other foreseeable tax charges",
    520: "Other transitional adjustments to CET1 Capital",
    524: "(-) Additional deductions of CET1 Capital due to Article 3 of Regulation (EU) No 575/2013",
    529: "CET1 capital elements or deductions - other",
    530: "ADDITIONAL TIER 1 CAPITAL",
    540: "Capital instruments and share premium eligible as AT1 Capital",
    551: "Fully paid up, directly issued capital instruments",
    560: "Memorandum item: Capital instruments not eligible",
    571: "Share premium",
    580: "(-) Own AT1 instruments",
    590: "(-) Direct holdings of AT1 instruments",
    620: "(-) Indirect holdings of AT1 instruments",
    621: "(-) Synthetic holdings of AT1 instruments",
    622: "(-) Actual or contingent obligations to purchase own AT1 instruments",
    660: "Transitional adjustments due to grandfathered AT1 Capital instruments",
    670: "Instruments issued by subsidiaries that are given recognition in AT1 Capital",
    680: "Transitional adjustments due to additional recognition in AT1 Capital of instruments issued by subsidiaries",
    690: "(-) Reciprocal cross holdings in AT1 Capital",
    700: "(-) AT1 instruments of financial sector entities where the institution does not have a significant investment",
    710: "(-) AT1 instruments of financial sector entities where the institution has a significant investment",
    720: "(-) Excess of deduction from T2 items over T2 Capital",
    730: "Other transitional adjustments to AT1 Capital",
    740: "Excess of deduction from AT1 items over AT1 Capital (deducted in CET1)",
    744: "(-) Additional deductions of AT1 Capital due to Article 3 of Regulation (EU) No 575/2013",
    748: "AT1 capital elements or deductions - other",
    750: "TIER 2 CAPITAL",
    760: "Capital instruments and share premium eligible as T2 Capital",
    771: "Fully paid up, directly issued capital instruments",
    780: "Memorandum item: Capital instruments not eligible",
    791: "Share premium",
    800: "(-) Own T2 instruments",
    810: "(-) Direct holdings of T2 instruments",
    840: "(-) Indirect holdings of T2 instruments",
    841: "(-) Synthetic holdings of T2 instruments",
    842: "(-) Actual or contingent obligations to purchase own T2 instruments",
    880: "Transitional adjustments due to grandfathered T2 Capital instruments",
    890: "Instruments issued by subsidiaries that are given recognition in T2 Capital",
    900: "Transitional adjustments due to additional recognition in T2 Capital of instruments issued by subsidiaries",
    910: "IRB Excess of provisions over expected losses eligible",
    920: "SA General credit risk adjustments",
    930: "(-) Reciprocal cross holdings in T2 Capital",
    940: "(-) T2 instruments of financial sector entities where the institution does not have a significant investment",
    950: "(-) T2 instruments of financial sector entities where the institution has a significant investment",
    955: "(-) Excess of deductions from eligible liabilities over eligible liabilities",
    960: "Other transitional adjustments to T2 Capital",
    970: "Excess of deduction from T2 items over T2 Capital (deducted in AT1)",
    974: "(-) Additional deductions of T2 Capital due to Article 3 of Regulation (EU) No 575/2013",
    978: "T2 capital elements or deductions - other"
}
#new
mapping_feuilles_rwa = {
    "Créances banques autres": ["C0700_0007_1"],
    "Créances clientèle": ["C0700_0008_1", "C0700_0009_1", "C0700_0010_1"],  # ✅ Ajout hypothécaire
    "Immobilisations et Autres Actifs": ["C0700_0010_1"]
}

mapping_c0700_to_c0200 = {
    "C0700_0007_1": "0120",
    "C0700_0008_1": "0130",
    "C0700_0009_1": "0140",
    "C0700_0010_1": "0150"
}
noms_lignes_c4700= {
        10: "SFTs: Exposure value",
        20: "SFTs: Add-on for counterparty credit risk",
        30: "Derogation for SFTs: Add-on (Art. 429e(5) & 222 CRR)",
        40: "Counterparty credit risk of SFT agent transactions",
        50: "(-) Exempted CCP leg of client-cleared SFT exposures",
        61: "Derivatives: Replacement cost (SA-CCR)",
        65: "(-) Collateral effect on QCCP client-cleared (SA-CCR)",
        71: "(-) Variation margin offset (SA-CCR)",
        81: "(-) Exempted CCP leg (SA-CCR - RC)",
        91: "Derivatives: PFE (SA-CCR)",
        92: "(-) Lower multiplier QCCP (SA-CCR - PFE)",
        93: "(-) Exempted CCP leg (SA-CCR - PFE)",
        101: "Replacement cost (simplified approach)",
        102: "(-) Exempted CCP leg (simplified RC)",
        103: "PFE (simplified)",
        104: "(-) Exempted CCP leg (simplified PFE)",
        110: "Derivatives: Original exposure method",
        120: "(-) Exempted CCP leg (original exposure)",
        130: "Written credit derivatives",
        140: "(-) Purchased credit derivatives offset",
        150: "Off-BS 10% CCF",
        160: "Off-BS 20% CCF",
        170: "Off-BS 50% CCF",
        180: "Off-BS 100% CCF",
        181: "(-) Adjustments off-BS items",
        185: "Pending settlement: Trade date accounting",
        186: "Pending settlement: Reverse offset (trade date)",
        187: "(-) Settlement offset 429g(2)",
        188: "Commitments under settlement date accounting",
        189: "(-) Offset under 429g(3)",
        190: "Other assets",
        191: "(-) General credit risk adjustments (on-BS)",
        193: "Cash pooling: accounting value",
        194: "Cash pooling: grossing-up effect",
        195: "Cash pooling: value (prudential)",
        196: "Cash pooling: grossing-up effect (prudential)",
        197: "(-) Netting (Art. 429b(2))",
        198: "(-) Netting (Art. 429b(3))",
        200: "Gross-up for derivatives collateral",
        210: "(-) Receivables for cash variation margin",
        220: "(-) Exempted CCP (initial margin)",
        230: "Adjustments for SFT sales",
        235: "(-) Pre-financing or intermediate loans",
        240: "(-) Fiduciary assets",
        250: "(-) Intragroup exposures (solo basis)",
        251: "(-) IPS exposures",
        252: "(-) Export credits guarantees",
        253: "(-) Excess collateral at triparty agents",
        254: "(-) Securitised exposures (risk transfer)",
        255: "(-) Central bank exposures (Art. 429a(1)(n))",
        256: "(-) Ancillary services CSD/institutions",
        257: "(-) Ancillary services designated institutions",
        260: "(-) Exposures exempted (Art. 429a(1)(j))",
        261: "(-) Public sector investments (PDCI)",
        262: "(-) Promotional loans (PDCI)",
        263: "(-) Promotional loans by gov. entities",
        264: "(-) Promotional loans via intermediaries",
        265: "(-) Promotional loans by non-PDCI",
        266: "(-) Promotional loans via non-PDCI",
        267: "(-) Pass-through promotional loans",
        270: "(-) Asset amount deducted - Tier 1"
    }

mapping_bilan_to_c4700 = {
    "Caisse Banque Centrale / nostro": 190,
    "Créances banques autres": 190,
    "Créances clientèle": 190,
    "Immobilisations et Autres Actifs": 190
}

"""
Calcul du Ratio de Solvabilité avec Capital Planning - Version debuggée
"""



def charger_c4700(levier_path="data/levier.xlsx"):
    """
    Charge les données C4700 pour le calcul du ratio de levier
    """
    try:
        df_c4700 = pd.read_excel(levier_path, sheet_name="C4700", header=9)
        df_c4700 = df_c4700.iloc[:, 2:]
        colonnes_utiles = [col for col in df_c4700.columns if not col.startswith('Unnamed: 4')]
        df_c4700 = df_c4700[colonnes_utiles]
        if 'Unnamed: 5' in df_c4700.columns:
            df_c4700 = df_c4700.drop(columns=['Unnamed: 5'])
        df_c4700 = df_c4700.rename(columns={'Unnamed: 2': 'Row', 'Unnamed: 3': '0010'})
        df_c4700['Row'] = pd.to_numeric(df_c4700['Row'], errors='coerce')
        df_c4700['0010'] = pd.to_numeric(df_c4700['0010'], errors='coerce')
        return df_c4700
    except Exception as e:
        st.error(f"Erreur lors du chargement de C4700: {e}")
        return pd.DataFrame(columns=['Row', '0010'])

def charger_tier1(corep_path="data/solvabilite.xlsx"):
    """
    Charge les données Tier1 (CET1 + AT1) depuis C0100
    """
    try:
        df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
        if "Unnamed: 2" in df_c01.columns:
            df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
        df_c01 = df_c01[["row", "0010"]] if "row" in df_c01.columns and "0010" in df_c01.columns else df_c01
        return df_c01.reset_index(drop=True)
    except Exception as e:
        st.error(f"Erreur lecture C0100 pour Tier1: {e}")
        return pd.DataFrame(columns=['row', '0010'])
def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(0 if pd.isna(row.get(c, 0)) else row.get(c, 0) for c in cols)

def charger_donnees(corep_path="data/solvabilite.xlsx", debug=False):
    """
    Charge toutes les données nécessaires : bilan, C0100, C0200 et blocs C0700
    """
    import os
    dossier = "data"
    bilan_path = os.path.join(dossier, "bilan.xlsx")

    # === BILAN ===
    if not os.path.exists(bilan_path):
        st.error(f"Fichier de bilan non trouvé : {bilan_path}")
        return None, None, None, None

    bilan = pd.read_excel(bilan_path)
    bilan = bilan.iloc[2:].reset_index(drop=True)

    if "Unnamed: 1" in bilan.columns:
        bilan = bilan.drop(columns=["Unnamed: 1"])

    for i, col in enumerate(bilan.columns):
        if str(col).startswith("Unnamed: 6"):
            bilan = bilan.iloc[:, :i]
            break

    bilan.columns.values[0] = "Poste du Bilan"
    bilan.columns.values[1] = "2024"
    bilan.columns.values[2] = "2025"
    bilan.columns.values[3] = "2026"
    bilan.columns.values[4] = "2027"
    bilan = bilan.dropna(how="all").reset_index(drop=True)

    if 25 in bilan.index:
        bilan = bilan.drop(index=25).reset_index(drop=True)

    
    if debug:
        st.write("### ✅ Liste des Postes du Bilan (après nettoyage)")
        st.dataframe(bilan[["Poste du Bilan"]])
    # === C0100 ===
    try:
        df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
        if "Unnamed: 2" in df_c01.columns:
            df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
        df_c01 = df_c01[["row", "0010"]] if "row" in df_c01.columns and "0010" in df_c01.columns else df_c01
        df_c01 = df_c01.reset_index(drop=True)
        df_c01["row"] = pd.to_numeric(df_c01["row"], errors='coerce')
        df_c01["0010"] = pd.to_numeric(df_c01["0010"], errors='coerce')
        if debug:
            st.write("### DEBUG: Aperçu C0100")
            st.dataframe(df_c01.head(20))
    except Exception as e:
        st.error(f"Erreur lecture C0100 : {e}")
        df_c01 = pd.DataFrame(columns=["row", "0010"])

    # === C0200 ===
    try:
        df_c02 = pd.read_excel(corep_path, sheet_name="C0200", header=8)
        df_c02 = df_c02.drop(columns=["Unnamed: 0", "Unnamed: 1"], errors='ignore')
        if "Unnamed: 2" in df_c02.columns:
            df_c02 = df_c02.rename(columns={"Unnamed: 2": "row"})
        if "Unnamed: 4" in df_c02.columns:
            df_c02 = df_c02.drop(columns=["Unnamed: 4"])
        df_c02 = df_c02[["row", "0010"]] if "row" in df_c02.columns and "0010" in df_c02.columns else df_c02
        df_c02["row"] = pd.to_numeric(df_c02["row"], errors='coerce')
        df_c02["0010"] = pd.to_numeric(df_c02["0010"], errors='coerce')
        df_c02.reset_index(drop=True, inplace=True)
        if debug:
            st.write("### DEBUG: Aperçu C0200")
            st.dataframe(df_c02.head(20))
    except Exception as e:
        st.error(f"Erreur lecture C0200 : {e}")
        df_c02 = pd.DataFrame(columns=["row", "0010"])

    # === BLOCS C0700 ===
    blocs_c0700 = {}
    for feuille in sum(mapping_feuilles_rwa.values(), []):
        try:
            if debug:
                st.write(f"### DEBUG: Chargement bloc {feuille}")
            df_raw_bloc = pd.read_excel(corep_path, sheet_name=feuille, header=12)
            df_bloc = df_raw_bloc.iloc[8:15].copy()
            colonnes_depart = df_raw_bloc.columns.get_loc("Unnamed: 2")
            df_bloc = df_bloc.iloc[:, colonnes_depart:]
            df_bloc.rename(columns={df_bloc.columns[0]: "row"}, inplace=True)
            if 8 in df_bloc.index:
                df_bloc = df_bloc.drop(index=8)
            for col in df_bloc.columns:
                if col != "row" and not pd.api.types.is_numeric_dtype(df_bloc[col]):
                    df_bloc[col] = pd.to_numeric(df_bloc[col], errors='coerce')
            df_bloc["row"] = pd.to_numeric(df_bloc["row"], errors='coerce')
            df_bloc.reset_index(drop=True, inplace=True)
            colonnes_requises = ["row", "0010", "0200", "0215", "0220"]
            for col in colonnes_requises:
                if col not in df_bloc.columns:
                    df_bloc[col] = np.nan
            blocs_c0700[feuille] = df_bloc
            if debug:
                st.write(f"Bloc {feuille} chargé avec succès")
                st.dataframe(df_bloc)
        except Exception as e:
            st.warning(f"Erreur chargement bloc {feuille} : {e}")
            blocs_c0700[feuille] = pd.DataFrame(columns=["row", "0010", "0200", "0215", "0220"])

    return bilan, df_c01, df_c02, blocs_c0700


def calculer_ratios_transformation(df_ref, debug=False):
    """
    Calcule les ratios implicites (RWA/exposition) pour chaque type de ligne à partir des données de référence.
    Ces ratios seront utilisés pour les calculs futurs.
    """
    ratios = {}
    
    for row_type, name in [(70.0, "on_balance"), (80.0, "off_balance"), (110.0, "derivatives")]:
        ligne = df_ref[df_ref["row"] == row_type]
        
        if not ligne.empty:
            # Récupération de l'exposition (0200) et du RWA (0215 ou 0220)
            rwa_col = "0215" if "0215" in ligne.columns else "0220"
            
            rwa = ligne[rwa_col].values[0] if not pd.isna(ligne[rwa_col].values[0]) else 0
            expo = ligne["0200"].values[0] if "0200" in ligne.columns and not pd.isna(ligne["0200"].values[0]) else 0
            
            # Calcul du ratio RWA/exposition
            if expo != 0:
                ratio = round(rwa / expo, 4)
            else:
                ratio = 0.25  # Valeur par défaut si exposition = 0
                
            ratios[row_type] = ratio
            
            if debug:
                st.write(f"Ratio calculé pour ligne {row_type} ({name}): {ratio}")
                st.write(f"  - RWA: {rwa}, Exposition: {expo}")
        else:
            ratios[row_type] = 0.25  # Valeur par défaut si ligne non trouvée
            if debug:
                st.warning(f"Ligne {row_type} ({name}) non trouvée, utilisation ratio par défaut 0.25")
    
    return ratios

def calculer_0200(row, debug=False):
    """
    Calcule la colonne 0200 en fonction des pondérations et avec relation entre 0010 et 0190.
    Pour la ligne 070, 0200 est égal à 0150. Pour la ligne 80.0, le calcul basé sur 0170, 0180 et 0190 est appliqué.
    """
    if row.get("row") == 70.0:  # Pour la ligne 70.0, 0200 = 0150
        return row.get("0150", 0)

    if row.get("row") == 110.0:  # Pour la ligne 110.0, ne pas recalculer 0200
        return row.get("0200", 0)

    # Récupérer les valeurs de 0170, 0180, 0190 avec gestion des NaN
    v170 = row.get("0170", 0)
    v180 = row.get("0180", 0)
    v190 = row.get("0190", 0)
   
    v170 = 0 if pd.isna(v170) else v170
    v180 = 0 if pd.isna(v180) else v180
    v190 = 0 if pd.isna(v190) else v190

    v010 = row.get("0010", 0)
    v010 = 0 if pd.isna(v010) else v010
   
   

    # Calculer 0200 selon la pondération
    result = (0.2 * v170) + (0.5 * v180) + (1.0 * v190)

   

    return result

#new
def repartir_capital_planning_clientele(valeur_totale, pourcentage_retail, pourcentage_corporate):
    """
    Répartit le capital planning entre les 3 feuilles C0700 :
    - 50% fixe pour Hypothécaire
    - Le reste réparti selon les pourcentages utilisateur
    """
    valeur_hypo = 0.5 * valeur_totale
    reste = 0.5 * valeur_totale

    valeur_retail = (pourcentage_retail / 100) * reste
    valeur_corp = (pourcentage_corporate / 100) * reste

    return {
        "C0700_0008_1": valeur_retail,
        "C0700_0009_1": valeur_corp,
        "C0700_0010_1": valeur_hypo
    }

def calculer_0220(row, ratios, debug=False):
    """Calcule la colonne 0220 (RWA) avec les ratios déjà calculés"""
    row_type = row.get("row")
    expo = row.get("0200", 0)
    
    # Si l'exposition est nulle ou NaN, on la met à 0
    if pd.isna(expo):
        expo = 0
    
    # Utilisation des ratios pré-calculés
    if row_type in [70.0, 80.0, 110.0]:
        ratio = ratios.get(row_type)  # Utiliser le ratio de transformation déjà calculé
        rwa = expo * ratio
        if debug:
            st.write(f"RWA calculé pour ligne {row_type}: {rwa}")
        return rwa
    
    # Pour les autres lignes, somme de 0215, 0216, 0217 si disponibles
    sum_cols = 0
    for k in ["0215", "0216", "0217"]:
        if k in row and not pd.isna(row.get(k)):
            sum_cols += row.get(k)
    
    if debug and row_type in [70.0, 80.0, 110.0]:
        st.write(f"RWA calculé pour ligne {row_type}: {sum_cols}")
    
    return sum_cols

def calculer_0040(row):
    return somme_sans_nan(row, ["0010", "0030"])

def calculer_0110(row):
    return somme_sans_nan(row, ["0040", "0050", "0060", "0070", "0080", "0090", "0100"])

def calculer_0150(row):
    return somme_sans_nan(row, ["0110", "0120", "0130"])


def calculer_rwa_depuis_exposition(expo, row_type, ratios, debug=False):
    """Calcule le RWA (0220) à partir de l'exposition (0200) et du ratio implicite"""
    if pd.isna(expo) or expo == 0:
        return 0
   
    ratio = ratios.get(row_type, 0.25)
    rwa = expo * ratio
   
    if debug:
        st.write(f"Calcul RWA pour ligne {row_type}:")
        st.write(f"  - Exposition: {expo}")
        st.write(f"  - Ratio: {ratio}")
        st.write(f"  - RWA calculé: {rwa}")
   
    return rwa


def construire_df_c0700_recalcule(df_bloc, debug=False):
    """
    Recalcule toutes les colonnes du bloc C0700 après injection du capital planning
    avec propagation de 0010 vers 0190 et 0200
    """
    if debug:
        st.write("### RECALCUL DU BLOC C0700 AVEC PROPAGATION AMÉLIORÉE")
       
    df_simulee = df_bloc.copy()
   
    # S'assurer que toutes les colonnes nécessaires existent
    colonnes_requises = ["row", "0010", "0040", "0110", "0150", "0170", "0180", "0190", "0200", "0215", "0220"]
    for col in colonnes_requises:
        if col not in df_simulee.columns:
            df_simulee[col] = np.nan
            if debug:
                st.write(f"Colonne {col} ajoutée (manquante)")
   
    # Calculer les ratios une seule fois pour tout le bloc
    ratios = calculer_ratios_transformation(df_bloc, debug)
   
    if debug:
        st.write(f"Ratios de transformation calculés: {ratios}")
   
    # Recalculer ligne par ligne
    for idx, row in df_simulee.iterrows():
        row_copy = row.copy()
        row_type = row_copy["row"]
       
        if debug:
            st.write(f"\nRecalcul ligne {row_type}:")
       
        # Calcul des colonnes intermédiaires
        row_copy["0040"] = calculer_0040(row_copy)
        row_copy["0110"] = calculer_0110(row_copy)
        row_copy["0150"] = calculer_0150(row_copy)
       
        # Pour toutes les lignes, utiliser la nouvelle logique de calcul 0200
        old_0200 = row_copy.get("0200", 0)
        old_0200 = 0 if pd.isna(old_0200) else old_0200
       
        # Propager 0010 vers 0190 si nécessaire
        if row_type == 70.0:  # Pour les actifs du bilan (on-balance)
            v010 = row_copy.get("0010", 0)
            v010 = 0 if pd.isna(v010) else v010
           
            v190 = row_copy.get("0190", 0)
            v190 = 0 if pd.isna(v190) else v190
           
            # Si 0190 est vide ou 0 mais 0010 existe, mettre à jour 0190
            if (v190 == 0) and (v010 > 0):
                row_copy["0190"] = v010
                if debug:
                    st.write(f"  Mise à jour 0190 depuis 0010: {v010}")
       
        # Recalculer 0200 avec la nouvelle fonction
        row_copy["0200"] = calculer_0200(row_copy, debug)
       
        # Calculer 0220 (RWA) en dernier
        old_0220 = row_copy.get("0220", 0)
        old_0220 = 0 if pd.isna(old_0220) else old_0220
       
        row_copy["0220"] = calculer_0220(row_copy, ratios, debug)
       
        # Définir 0215 égal à 0220 (dans ce modèle)
        row_copy["0215"] = row_copy["0220"]
       
        if debug:
            st.write(f"  Résultats ligne {row_type}:")
            st.write(f"  - 0010: {row_copy.get('0010', 0)}")
            st.write(f"  - 0190: {row_copy.get('0190', 0)}")
            st.write(f"  - 0200: {old_0200} → {row_copy['0200']}")
            st.write(f"  - 0220: {old_0220} → {row_copy['0220']}")
       
        # Mettre à jour les valeurs dans le dataframe
        for col in colonnes_requises:
            if col in row_copy and not pd.isna(row_copy.get(col)):
                df_simulee.at[idx, col] = row_copy.get(col)
   
    return df_simulee

def injecter_capital_planning_dans_bloc(df_bloc, capital_planning_value, debug=False):
    """
    Injecte le capital planning dans le bloc C0700 et recalcule uniquement pour la ligne 70.0.
    La fonction gère également le recalcul complet du bloc.
    """
    if debug:
        st.write("\n### DEBUG: injecter_capital_planning_dans_bloc")
        st.write(f"Capital planning à injecter: {capital_planning_value}")

    if capital_planning_value is None or pd.isna(capital_planning_value) or capital_planning_value == 0:
        if debug:
            st.write("⚠️ Valeur invalide ou nulle")
        return df_bloc  # Retourner tel quel si la valeur est invalide

    df_new = df_bloc.copy()

    # Identifier la ligne 70.0 dans le bloc
    idx = df_new[df_new["row"] == 70.0].index

    if not idx.empty:
        # Injection du capital planning uniquement dans la ligne 70.0
        ancienne_valeur = df_new.at[idx[0], "0010"]
        ancienne_valeur = 0 if pd.isna(ancienne_valeur) else ancienne_valeur
        nouvelle_valeur = ancienne_valeur + capital_planning_value
        df_new.at[idx[0], "0010"] = nouvelle_valeur

        if debug:
            st.write(f"Mise à jour ligne 70.0: {ancienne_valeur:,.2f} + {capital_planning_value:,.2f} = {nouvelle_valeur:,.2f}")
    else:
        if debug:
            st.error("❌ Ligne 70.0 introuvable")
        raise ValueError("Ligne 70.0 introuvable")

    # Recalculer le bloc après injection
    df_new = construire_df_c0700_recalcule(df_new, debug)  
    return df_new  # Retourner le bloc mis à jour et déjà recalculé



def calculer_somme_rwa_bloc(df_bloc, debug=False):
    """
    Calcule la somme des RWA (0220) pour un bloc avec meilleure gestion des erreurs
    """
    if debug:
        st.write("### CALCUL SOMME RWA BLOC")
   
    # Vérifier si la colonne 0220 existe
    if "0220" not in df_bloc.columns:
        if debug:
            st.error("Colonne 0220 absente du bloc")
        return 0
       
    # Lignes à inclure dans le total RWA
    rwa_lignes = [70.0, 80.0, 110.0]
   
    # Filtrer le dataframe et calculer la somme
    df_filtered = df_bloc[df_bloc["row"].isin(rwa_lignes)]
   
    if df_filtered.empty:
        if debug:
            st.warning("Aucune des lignes RWA (70.0, 80.0, 110.0) n'est présente dans le bloc")
        return 0
   
    # Remplacer les NaN par 0 et calculer la somme
    somme_rwa = df_filtered["0220"].fillna(0).sum()
   
    if debug:
        st.write(f"Somme RWA calculée: {somme_rwa}")
        st.write("Détail par ligne:")
        for ligne in rwa_lignes:
            if ligne in df_filtered["row"].values:
                val = df_filtered[df_filtered["row"] == ligne]["0220"].fillna(0).values[0]
                st.write(f"  - Ligne {ligne}: {val}")
   
    return somme_rwa

def somme_si_dispo(df, lignes):
    """Somme les valeurs de la colonne 0010 pour les lignes spécifiées avec gestion des erreurs"""
    total = 0
    for l in lignes:
        ligne = df[df["row"] == l]
        if not ligne.empty and "0010" in ligne.columns:
            val = ligne["0010"].values[0]
            if not pd.isna(val):
                total += val
    return total

def recalculer_arborescence_c0200(df_c02):
    """
    Recalcule toutes les lignes du tableau C0200 selon la structure arborescente
    en sommant les dépendants pour chaque parent.
    """
    df = df_c02.copy()

    formules = {
        10: [40, 520, 590, 640],
        40: [50, 240, 250, 310],
        50: [60],
        60: [70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 211],
        240: [241, 242],
        250: [260, 270, 280, 290, 300],
        310: [320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 450],
        490: [500, 510],
        520: [530, 580],
        530: [540, 550, 555, 560, 570],
        590: [600, 610, 620],
        640: [650, 660, 670],
        690: [710, 720, 730, 740, 750, 760]
    }

    # Convertir 'row' en float si elle est string
    if df["row"].dtype == object:
        df["row"] = pd.to_numeric(df["row"], errors="coerce")

    for parent, enfants in formules.items():
        somme = 0
        for enfant in enfants:
            val = df.loc[df["row"] == enfant, "0010"]
            if not val.empty and not pd.isna(val.values[0]):
                somme += val.values[0]
        idx_parent = df[df["row"] == parent].index
        if not idx_parent.empty:
            df.at[idx_parent[0], "0010"] = somme

    return df


def calculer_fonds_propres_annee(df_c01_prec, bilan_df, annee):
    """
    Calcule les fonds propres CET1 en tenant compte :
    - du capital planning appliqué au Résultat de l'exercice (ligne 150)
    - et au Report à nouveau (ligne 200)
    """
    # Copie du COREP C01 de l'année précédente
    df_c01_annee = df_c01_prec.copy()

    # === 1. Capital planning sur Résultat de l'exercice
    poste_resultat = "Income Statement - Résultat de l'exercice"
    cp_resultat = get_capital_planning_below(bilan_df, poste_resultat, annee)

    idx_resultat = df_c01_annee[df_c01_annee["row"] == 200].index
    if not idx_resultat.empty and cp_resultat is not None:
        ancienne_val = df_c01_annee.at[idx_resultat[0], "0010"] or 0
        df_c01_annee.at[idx_resultat[0], "0010"] = ancienne_val + cp_resultat

    # === 2. Capital planning sur Report à nouveau
    poste_report = "Report à nouveau (passif)"
    cp_report = get_capital_planning_below(bilan_df, poste_report, annee)

    idx_report = df_c01_annee[df_c01_annee["row"] == 200].index
    if not idx_report.empty and cp_report is not None:
        ancienne_val = df_c01_annee.at[idx_report[0], "0010"] or 0
        df_c01_annee.at[idx_report[0], "0010"] = ancienne_val + cp_report

    # === 3. Recalcul de l'arborescence (CET1 → Tier1 → Total funds)
    df_c01_annee = recalculer_c0100_arborescence(df_c01_annee)

    # === 4. Extraction du montant total des fonds propres (CET1 + AT1 + T2) : ligne 20
    idx_20 = df_c01_annee[df_c01_annee["row"] == 15].index
    fonds_propres = df_c01_annee.at[idx_20[0], "0010"] if not idx_20.empty else None

    return df_c01_annee, fonds_propres

def recalculer_c0100_arborescence(df_c01):
    """
    Recalcule les blocs CET1, AT1 et Tier 2 du tableau C0100
    """
    df = df_c01.copy()

    formules_cet1 = {
        30: [40, 60, 70, 92],
        70: [80, 90, 91],
        130: [140, 150],
        150: [160, 170],
        250: [260, 270, 280, 285, 290],
        300: [310, 320, 330, 335],
        340: [350, 360, 365],
        390: [400, 410, 420],
        20: [30, 130, 180, 200, 210, 220, 240, 230, 250, 300, 340, 370, 380, 390,
             430, 440, 450, 460, 470, 471, 472, 480, 490, 500, 510, 511, 512,
             513, 514, 515, 520, 524, 529]
    }

    formules_at1 = {
        530: [540, 660, 670, 680, 690, 700, 710, 720, 730, 740, 744, 748],
        540: [551, 571, 580, 622],
        580: [590, 620, 621],
    }

    formules_tier2 = {
        750: [760, 880, 890, 900, 910, 920, 930, 940, 950, 955, 960, 970, 974, 978],
        760: [771, 791, 800, 842],
        800: [810, 840, 841],
    }

    for bloc in [formules_cet1, formules_at1, formules_tier2]:
        for ligne_parent, dependants in bloc.items():
            total = somme_si_dispo(df, dependants)
            idx = df[df["row"] == ligne_parent].index
            if not idx.empty:
                df.at[idx[0], "0010"] = total

    return df

def calculer_ratio_solvabilite(df_c01, df_c02):
    """
    Calcule le ratio de solvabilité = fonds propres réglementaires / total RWA
    """
    # Numérateur : ligne 20 dans C0100
    fp = df_c01.loc[df_c01["row"] == 20, "0010"]
    # Dénominateur : ligne 10 dans C0200
    rwa = df_c02.loc[df_c02["row"] == 10, "0010"]

    if fp.empty or rwa.empty or rwa.values[0] == 0:
        return None

    ratio = fp.values[0] / rwa.values[0] * 100
    return round(ratio, 2)
def traiter_poste_capital_planning(poste, feuille, bilan, annee, df_bloc_prec, df_c02, debug=False):
    """
    Injecte le capital planning pour un poste donné et met à jour le C0200.
    Corrigée : conversion des index 'row' en string pour une bonne correspondance avec le mapping.
    La fonction utilise l'injection qui inclut déjà le recalcul.
    """
    if debug:
        st.write(f"\n### DEBUG traiter_poste_capital_planning")
        st.write(f"Processing {poste} pour feuille {feuille}")

    cp_value = get_capital_planning_below(bilan, poste, annee, debug=debug)
    if debug:
        st.write(f"Capital planning value: {cp_value}")

    if cp_value is None or pd.isna(cp_value):
        if debug:
            st.write("⚠️ No capital planning value found")
        return df_bloc_prec.copy(), 0, df_c02

    # Injection et recalcul (le recalcul est déjà géré dans injecter_capital_planning_dans_bloc)
    df_bloc_recalcule = injecter_capital_planning_dans_bloc(df_bloc_prec, cp_value, debug=debug)

    # Calcul du delta RWA
    rwa_ancien = calculer_somme_rwa_bloc(df_bloc_prec, debug=debug)
    rwa_nouveau = calculer_somme_rwa_bloc(df_bloc_recalcule, debug=debug)
    delta_rwa = rwa_nouveau - rwa_ancien

    if debug:
        st.write(f"RWA ancien: {rwa_ancien:,.2f}")
        st.write(f"RWA nouveau: {rwa_nouveau:,.2f}")
        st.write(f"Delta RWA: {delta_rwa:,.2f}")

    # Mise à jour de la ligne cible dans C0200
    code_ligne = mapping_c0700_to_c0200.get(feuille)
    if code_ligne:
        df_c02_new = df_c02.copy()
        df_c02_new["row"] = df_c02_new["row"].astype(str)  # Cast obligatoire

        idx = df_c02_new[df_c02_new["row"] == code_ligne].index
        if not idx.empty:
            ancienne_valeur = float(df_c02_new.at[idx[0], "0010"] or 0)
            df_c02_new.at[idx[0], "0010"] = ancienne_valeur + delta_rwa
            
            if debug:
                st.write(f"Mise à jour C0200 ligne {code_ligne}:")
                st.write(f"- Ancienne valeur: {ancienne_valeur:,.2f}")
                st.write(f"- Nouvelle valeur: {(ancienne_valeur + delta_rwa):,.2f}")

        return df_bloc_recalcule, delta_rwa, df_c02_new

    if debug:
        st.write("⚠️ No mapping found for C0200 update")
    return df_bloc_recalcule, delta_rwa, df_c02
#new
def traiter_tous_postes(bilan, annee, blocs_prec, df_c02_prec, pourcentage_retail=50, pourcentage_corporate=50, debug=False):
    # Initialisation des variables de retour
    blocs_recalcules = {nom: df.copy() for nom, df in blocs_prec.items()}
    df_c02_new = df_c02_prec.copy()
    journal_deltas = []
    repartition = {}

    if debug:
        st.write(f"\n### DEBUG: Traitement année {annee}")
        st.write("📊 Blocs initiaux:")
        for nom, bloc in blocs_prec.items():
            st.write(f"Bloc {nom}:")
            st.dataframe(bloc)

    # === PHASE 1 : Créances Clientèle ===
    poste_client = "Créances clientèle"
    valeur_creance_totale = get_capital_planning_below(bilan, poste_client, annee, debug=debug) or 0
    
    if valeur_creance_totale > 0:
        # Utilisation de la fonction de répartition pour le capital planning clientèle
        repartition = repartir_capital_planning_clientele(valeur_creance_totale, pourcentage_retail, pourcentage_corporate)

        if debug:
            st.write("📊 Répartition Créances Clientèle:")
            st.json(repartition)

        # Injection Retail/Corporate
        for feuille in ['C0700_0008_1', 'C0700_0009_1']:
            valeur = repartition[feuille]
            if feuille in blocs_recalcules:
                if debug:
                    st.write(f"\n🔄 Injection {valeur:,.2f} dans {feuille}")
                # Le bloc est déjà recalculé dans injecter_capital_planning_dans_bloc
                bloc_modifie = injecter_capital_planning_dans_bloc(blocs_recalcules[feuille], valeur, debug=debug)
                delta = calculer_somme_rwa_bloc(bloc_modifie) - calculer_somme_rwa_bloc(blocs_recalcules[feuille])
                blocs_recalcules[feuille] = bloc_modifie
                journal_deltas.append((f"{poste_client} - {feuille[-5]}", feuille, delta))

    # === PHASE 2 : Part hypothécaire + Immobilisations ===
    poste_immobilisations = "Immobilisations et Autres Actifs"
    valeur_immobilisations = get_capital_planning_below(bilan, poste_immobilisations, annee, debug=debug) or 0
    valeur_part_hypo = repartition.get("C0700_0010_1", 0)
    valeur_totale_0010_1 = valeur_part_hypo + valeur_immobilisations

    if valeur_totale_0010_1 > 0:
        feuille = "C0700_0010_1"
        if debug:
            st.write(f"\n🟣 Injection combinée dans {feuille}:")
            st.write(f"- Part hypothécaire: {valeur_part_hypo:,.2f}")
            st.write(f"- Immobilisations: {valeur_immobilisations:,.2f}")
            st.write(f"→ Total injecté: {valeur_totale_0010_1:,.2f}")

        # Le bloc est déjà recalculé dans injecter_capital_planning_dans_bloc
        bloc_modifie = injecter_capital_planning_dans_bloc(blocs_recalcules[feuille], valeur_totale_0010_1, debug=debug)
        delta = calculer_somme_rwa_bloc(bloc_modifie) - calculer_somme_rwa_bloc(blocs_recalcules[feuille])
        blocs_recalcules[feuille] = bloc_modifie
        journal_deltas.append(("Part hypo + Immobilisations", feuille, delta))

    # === PHASE 3 : Autres postes standards ===
    for poste, feuilles in mapping_feuilles_rwa.items():
        if poste in [poste_client, poste_immobilisations]:
            continue

        valeur = get_capital_planning_below(bilan, poste, annee, debug=debug) or 0
        if valeur > 0:
            for feuille in feuilles:
                if feuille in blocs_recalcules:
                    if debug:
                        st.write(f"\n🔍 Traitement poste {poste} sur feuille {feuille}")
                        st.write(f"Valeur CP: {valeur:,.2f}")
                    # Le bloc est déjà recalculé dans injecter_capital_planning_dans_bloc
                    bloc_modifie = injecter_capital_planning_dans_bloc(blocs_recalcules[feuille], valeur, debug=debug)
                    delta = calculer_somme_rwa_bloc(bloc_modifie) - calculer_somme_rwa_bloc(blocs_recalcules[feuille])
                    blocs_recalcules[feuille] = bloc_modifie
                    journal_deltas.append((poste, feuille, delta))

    # === PHASE 4 : Mise à jour du RWA total ===
    total_delta = sum(delta for _, _, delta in journal_deltas)
    idx_10 = df_c02_new[df_c02_new["row"] == "10"].index
    if not idx_10.empty:
        ancien_rwa = float(df_c02_new.at[idx_10[0], "0010"] or 0)
        nouveau_rwa = ancien_rwa + total_delta
        df_c02_new.at[idx_10[0], "0010"] = nouveau_rwa
        if debug:
            st.write(f"\n📌 MAJ RWA total (ligne 10): {ancien_rwa:,.2f} → {nouveau_rwa:,.2f}")

    # === Retour systématique des résultats ===
    return blocs_recalcules, df_c02_new, journal_deltas

def simuler_solvabilite_pluriannuelle(
    bilan, df_c01_2024, df_c02_2024, blocs_c0700_2024,
    annees=["2025", "2026", "2027"],
    pourcentage_retail=50, pourcentage_corporate=50
):
    resultats = {
        "2024": {
            "ratio": calculer_ratio_solvabilite(df_c01_2024, df_c02_2024),
            "fonds_propres": df_c01_2024.loc[df_c01_2024["row"] == 20, "0010"].values[0],
            "rwa": df_c02_2024.loc[df_c02_2024["row"] == 10, "0010"].values[0],
            "df_c01": df_c01_2024.copy(),
            "df_c02": df_c02_2024.copy(),
            "blocs_rwa": {nom: df.copy() for nom, df in blocs_c0700_2024.items()},
            "rwa_cumule": df_c02_2024.loc[df_c02_2024["row"] == 10, "0010"].values[0]
        }
    }

    # MODIFICATION CLÉ : On garde une référence mutable des blocs qui sera mise à jour année après année
    blocs_courants = {nom: df.copy() for nom, df in blocs_c0700_2024.items()}
    df_c02_courant = df_c02_2024.copy()
    rwa_cumule = resultats["2024"]["rwa_cumule"]

    for annee in annees:
        annee_prec = str(int(annee)-1)
        
        # MODIFICATION : On utilise les blocs courants (déjà mis à jour) plutôt que blocs_reference
        blocs_annee, df_c02_new, log_deltas = traiter_tous_postes(
            bilan, annee, 
            blocs_prec=blocs_courants,  # On utilise les blocs de l'année précédente modifiés
            df_c02_prec=df_c02_courant,
            pourcentage_retail=pourcentage_retail,
            pourcentage_corporate=pourcentage_corporate
        )

        # Mise à jour des références pour l'année suivante
        blocs_courants = {nom: df.copy() for nom, df in blocs_annee.items()}
        df_c02_courant = df_c02_new.copy()
        
        delta_total = sum(delta for _, _, delta in log_deltas)
        rwa_cumule += delta_total

        df_c01_new, fonds_propres = calculer_fonds_propres_annee(
            resultats[annee_prec]["df_c01"],  # Prend les FP de l'année précédente
            bilan, annee
        )
        
        ratio = round(fonds_propres / rwa_cumule * 100, 2) if rwa_cumule else None

        resultats[annee] = {
            "ratio": ratio,
            "fonds_propres": fonds_propres,
            "rwa": rwa_cumule,
            "df_c01": df_c01_new,
            "df_c02": df_c02_new,
            "blocs_rwa": blocs_annee,
            "deltas": log_deltas,
            "rwa_cumule": rwa_cumule
        }

    return resultats


# def format_large_number(num):
#     """Formate les grands nombres pour l'affichage"""
#     if pd.isna(num) or num == 0:
#         return "0"
#     abs_num = abs(num)
#     if abs_num >= 1_000_000_000:
#         return f"{num/1_000_000_000:.2f}B"
#     elif abs_num >= 1_000_000:
#         return f"{num/1_000_000:.2f}M"
#     else:
#         return f"{num:,.2f}"

def afficher_ratios_solvabilite(resultats_solva):
    """Affiche les résultats des ratios de solvabilité dans Streamlit"""
    st.subheader("Ratio de Solvabilité")
    with st.expander("Ratio de Solvabilité", expanded=True):
        st.write("**Définition :** Le ratio de solvabilité mesure la capacité d'une banque à absorber les pertes par rapport à ses actifs pondérés par le risque.")
        st.latex(r"\\text{Solvabilité} = \\frac{\\text{Fonds propres réglementaires}}{\\text{RWA}}")
        st.write("**Interprétation :** Un ratio ≥ 8% indique une bonne couverture des risques.")

    for annee, result in resultats_solva.items():
        with st.expander(f"Détails pour {annee}", expanded=(annee == "2024")):
            st.markdown(f"### Année {annee}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ratio", f"{result['ratio']:.2f}%")
            with col2:
                st.metric("Fonds propres", (result["fonds_propres"]))
            with col3:
                st.metric("RWA", (result["rwa"]))

            # Tableau C0100 filtré (Fonds propres)
            st.markdown("**Fonds Propres (C0100)**")
            df_c01_filtre = result["df_c01"]
            lignes_fp = [20, 30, 150, 530, 750]
            df_fp = df_c01_filtre[df_c01_filtre["row"].isin(lignes_fp)]
            if not df_fp.empty:
                st.dataframe(df_fp, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour C0100.")

            # Tableau C0200 filtré (RWA)
            st.markdown("**Actifs Pondérés par le Risque (C0200)**")
            df_c02_filtre = result["df_c02"]
            lignes_rwa = [10, 40, 60, 120, 130, 140, 210, 211]
            df_rwa = df_c02_filtre[df_c02_filtre["row"].isin(lignes_rwa)]
            if not df_rwa.empty:
                st.dataframe(df_rwa, use_container_width=True)
            else:
                st.info("Aucune donnée disponible pour C0200.")

            # Détails des blocs C0700 si disponibles
            if "blocs_rwa" in result:
                for nom_bloc, bloc in result["blocs_rwa"].items():
                    st.markdown(f"**Bloc RWA - {nom_bloc} (C0700)**")
                    if not bloc.empty:
                        st.dataframe(bloc, use_container_width=True)
                    else:
                        st.info(f"Aucune donnée disponible pour {nom_bloc}.")

def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(row.get(c, 0) for c in cols if pd.notna(row.get(c, 0)))



'''def get_tier1_value(df_c01):
    """
    Récupère la valeur du Tier 1 (ligne 15) du tableau C0100
    """
    idx = df_c01[df_c01["row"] == 15].index
    if not idx.empty:
        return df_c01.loc[idx[0], "0010"]
    return None'''

# Mapping pour identifier les postes du bilan correspondant aux lignes dans C4700
# Ce mapping relie les postes du bilan aux catégories d'exposition dans le calcul du ratio de levier
mapping_bilan_to_c4700 = {
    "Caisse Banque Centrale / nostro": 190,  # Other assets
    "Créances banques autres": 190,  # Other assets
    "Créances sur la clientèle (total)": 190,  # Other assets
   # Other assets
    "Immobilisations et Autres Actifs": 190   # Other assets
}

def calcul_total_exposure(df_c4700, valeur_stressee_0190=None):
    """
    Calcule l'exposition totale pour le ratio de levier
    """
    rows_a_inclure = [
        10, 20, 30, 40, 50, 61, 65, 71, 81, 91, 92, 93,
        101, 102, 103, 104, 110, 120, 130, 140, 150, 160, 170, 180,
        181, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 196,
        197, 198, 200, 210, 220, 230, 235, 240, 250, 251, 252, 253,
        254, 255, 256, 257, 260, 261, 262, 263, 264, 265, 266, 267, 270
    ]
   
    df_temp = df_c4700.copy()
   
    if valeur_stressee_0190 is not None:
        idx = df_temp[df_temp['Row'] == 190].index
        if not idx.empty:
            df_temp.loc[idx[0], '0010'] += valeur_stressee_0190
        else:
            # Si ligne 190 absente, on l'ajoute
            new_row = pd.DataFrame([{"Row": 190, "0010": valeur_stressee_0190}])
            df_temp = pd.concat([df_temp, new_row], ignore_index=True)
   
    total_exposure = (
        df_temp[df_temp['Row'].isin(rows_a_inclure)]
        .apply(lambda row: somme_sans_nan(row, ['0010']), axis=1)
        .sum()
    )
   
    return total_exposure, df_temp

def calculer_ratio_levier(tier1_value, total_exposure):
    """
    Calcule le ratio de levier = Tier 1 / Total Exposure
    """
    if pd.isna(tier1_value) or pd.isna(total_exposure) or total_exposure == 0:
        return None
   
    ratio = (tier1_value / total_exposure) * 100
    return round(ratio, 2)


    # === Récupération du capital planning ===
def get_capital_planning_below(bilan_df, poste_bilan, annee="2025", debug=False):
    """
    Récupère la valeur du capital planning sous un poste du bilan
    """
    if debug:
        st.write(f"### DEBUG: get_capital_planning_below")
        st.write(f"Recherche capital planning pour {poste_bilan} en {annee}")
        
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index
    
    if debug:
        st.write(f"Index trouvé pour le poste: {index_poste}")
        
    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if debug:
                st.write(f"Valeur trouvée à l'index {i}: {valeur}")
            if pd.notna(valeur):
                return valeur
            elif debug:
                st.write("Valeur trouvée est NaN")
        elif debug:
            st.write("Index hors limites ou année non trouvée")
    elif debug:
        st.write("Poste non trouvé dans le bilan")
        
    if debug:
        st.write("Retourne None (aucune valeur valide trouvée)")
    return None



def calculer_fonds_propres_tier1_annee(df_c01_prec, bilan_df, annee):
    """
    Ajoute le capital planning au résultat (ligne 150) et recalcule les fonds propres Tier 1
    """
    poste = "Income Statement - Résultat de l'exercice"
    cp_annee = get_capital_planning_below(bilan_df, poste, annee)

    df_c01_annee = df_c01_prec.copy()
    idx_150 = df_c01_annee[df_c01_annee["row"] == 150].index

    if not idx_150.empty and cp_annee is not None:
        ancienne_val = df_c01_annee.at[idx_150[0], "0010"] or 0
        df_c01_annee.at[idx_150[0], "0010"] = ancienne_val + cp_annee

    df_c01_annee = recalculer_c0100_arborescence(df_c01_annee)

    idx_15 = df_c01_annee[df_c01_annee["row"] == 15].index
    tier1 = df_c01_annee.at[idx_15[0], "0010"] if not idx_15.empty else None

    return df_c01_annee, tier1

def recalculer_c0100_arborescence(df_c01):
    """
    Recalcule les blocs CET1, AT1 et Tier 2 du tableau C0100
    """
    df = df_c01.copy()

    formules_cet1 = {
        30: [40, 60, 70, 92],
        70: [80, 90, 91],
        130: [140, 150],
        150: [160, 170],
        250: [260, 270, 280, 285, 290],
        300: [310, 320, 330, 335],
        340: [350, 360, 365],
        390: [400, 410, 420],
        20: [30, 130, 180, 200, 210, 220, 240, 230, 250, 300, 340, 370, 380, 390,
             430, 440, 450, 460, 470, 471, 472, 480, 490, 500, 510, 511, 512,
             513, 514, 515, 520, 524, 529]
    }

    formules_at1 = {
        530: [540, 660, 670, 680, 690, 700, 710, 720, 730, 740, 744, 748],
        540: [551, 571, 580, 622],
        580: [590, 620, 621],
    }

    # Ajout de la formule pour Tier1 = CET1 + AT1
    formules_tier1 = {
        15: [20, 530]  # Tier1 = CET1 + AT1
    }

    for bloc in [formules_cet1, formules_at1, formules_tier1]:
        for ligne_parent, dependants in bloc.items():
            idx = df[df["row"] == ligne_parent].index
            if not idx.empty:
                total = sum(
                    df.loc[df["row"] == l, "0010"].values[0]
                    for l in dependants
                    if l in df["row"].values and not df.loc[df["row"] == l, "0010"].isna().all()
                )
                df.at[idx[0], "0010"] = total

    return df

def simuler_levier_pluriannuel(
    bilan, df_c01_2024, df_c4700_2024,
    annees=["2025", "2026", "2027"]
):
    """
    Simule la projection des ratios de levier pour plusieurs années,
    en harmonisant le calcul du Tier 1 avec celui utilisé pour la solvabilité.
    """
    # === Traitement 2024 avec capital planning ===
    df_c01_2024_calcule, tier1_2024 = calculer_fonds_propres_annee(df_c01_2024, bilan, "2024")
    total_exposure_2024, df_c4700_2024_modifie = calcul_total_exposure(df_c4700_2024)

    resultats = {
        "2024": {
            "ratio": calculer_ratio_levier(tier1_2024, total_exposure_2024),
            "tier1": tier1_2024,
            "total_exposure": total_exposure_2024,
            "df_c01": df_c01_2024_calcule,
            "df_c4700": df_c4700_2024_modifie
        }
    }

    # Dictionnaires de suivi pour les années suivantes
    dict_df_c01 = {"2024": df_c01_2024_calcule}
    dict_df_c4700 = {"2024": df_c4700_2024_modifie}

    # === Projection pluriannuelle ===
    for annee in annees:
        annee_prec = str(int(annee) - 1)

        # 1. Recalcul du Tier 1 avec capital planning
        df_c01_new, tier1_value = calculer_fonds_propres_annee(
            dict_df_c01[annee_prec], bilan, annee
        )

        # 2. Recalcul de l’exposition totale avec capital planning appliqué à "Other assets"
        df_c4700_prec = dict_df_c4700[annee_prec].copy()
        somme_capital_planning = sum(
            get_capital_planning_below(bilan, poste, annee) or 0
            for poste in mapping_bilan_to_c4700
        )

        total_exposure, df_c4700_new = calcul_total_exposure(df_c4700_prec, somme_capital_planning)
        ratio = calculer_ratio_levier(tier1_value, total_exposure)

        # 3. Sauvegarde des résultats
        resultats[annee] = {
            "ratio": ratio,
            "tier1": tier1_value,
            "total_exposure": total_exposure,
            "df_c01": df_c01_new,
            "df_c4700": df_c4700_new
        }

        dict_df_c01[annee] = df_c01_new
        dict_df_c4700[annee] = df_c4700_new

    return resultats

def format_large_number(num):
    """Formate les grands nombres pour l'affichage"""
    if pd.isna(num) or num == 0:
        return "0"
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    else:
        return f"{num:,.2f}"

def afficher_ratios_levier(resultats_levier):
    """Affiche les résultats des ratios de levier dans Streamlit"""
    st.subheader("Ratio de Levier")
    with st.expander("Ratio de Levier", expanded=True):
        st.write("**Définition :** Le ratio de levier mesure la capacité d'une banque à faire face à ses engagements, indépendamment de la pondération des risques.")
        st.latex(r"\\text{Levier} = \\frac{\\text{Tier 1}}{\\text{Exposition Totale}}")
        st.write("**Interprétation :** Un ratio ≥ 3% est généralement requis par la réglementation bancaire européenne.")

    for annee, result in resultats_levier.items():
        with st.expander(f"Détails pour {annee}", expanded=(annee == "2024")):
            st.markdown(f"### Année {annee}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Ratio", f"{result['ratio']:.2f}%")
            with col2:
                st.metric("Tier 1 (C0100)", format_large_number(result['tier1']))
            with col3:
                st.metric("Exposition Totale (C4700)", format_large_number(result['total_exposure']))

            st.markdown("**Tier 1 (extrait de C0100)**")
            st.dataframe(result["df_c01"][result["df_c01"]["row"].isin([15, 20, 530])], use_container_width=True)

            st.markdown("**C4700 (exposition totale)**")
            key_rows = [10, 61, 91, 130, 150, 160, 170, 180, 190, 270]  # Lignes principales pour C4700
            st.dataframe(result["df_c4700"][result["df_c4700"]["Row"].isin(key_rows)], use_container_width=True)
