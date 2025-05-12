import pandas as pd
import os
import streamlit as st
import numpy as np

mapping_rows_levier = {
    10: "SFTs: Exposure value",
    20: "SFTs: Add-on for counterparty credit risk",
    30: "Derogation for SFTs: Add-on in accordance with Article 429e(5) and 222 CRR",
    40: "Counterparty credit risk of SFT agent transactions",
    50: "(-) Exempted CCP leg of client-cleared SFT exposures",
    61: "Derivatives: replacement cost under the SA-CCR (without the effect of collateral on NICA)",
    65: "(-) Effect of the recognition of collateral on NICA on QCCP client-cleared transactions",
    71: "(-) Effect of the eligible cash variation margin received offset",
    81: "(-) Effect of the exempted CCP leg of client-cleared trade exposures (replacement cost)",
    91: "Derivatives: Potential future exposure contribution (SA-CCR)",
    92: "(-) Effect lower multiplier for QCCP client-cleared transactions (PFE)",
    93: "(-) Exempted CCP leg (SA-CCR - potential future exposure)",
    101: "Derogation: replacement costs (simplified standardised approach)",
    102: "(-) Exempted CCP leg (replacement costs - simplified)",
    103: "Derogation: Potential future exposure (simplified)",
    104: "(-) Exempted CCP leg (PFE - simplified)",
    110: "Derogation: original exposure method",
    120: "(-) Exempted CCP leg (original exposure method)",
    130: "Capped notional amount of written credit derivatives",
    140: "(-) Purchased credit derivatives offset against written",
    150: "Off-balance sheet 10% CCF",
    160: "Off-balance sheet 20% CCF",
    170: "Off-balance sheet 50% CCF",
    180: "Off-balance sheet 100% CCF",
    181: "(-) Credit risk adjustments off-balance sheet",
    185: "Regular-way purchases/sales awaiting settlement (accounting value)",
    186: "Sales awaiting settlement (reverse offset)",
    187: "(-) Sales awaiting settlement (offset)",
    188: "Purchases awaiting settlement (commitments)",
    189: "(-) Settlement offset under date accounting",
    190: "Other assets",
    191: "(-) Credit risk adjustments on-balance sheet",
    193: "Cash pooling (not nettable): accounting value",
    194: "Cash pooling (not nettable): grossing-up",
    195: "Cash pooling (nettable): accounting value",
    196: "Cash pooling (nettable): grossing-up",
    197: "(-) Cash pooling netting under Article 429b(2)",
    198: "(-) Cash pooling netting under Article 429b(3)",
    200: "Gross up for derivatives collateral",
    210: "(-) Receivables for variation margin (derivatives)",
    220: "(-) Exempted CCP leg (initial margin)",
    230: "Adjustments for SFT sales",
    235: "(-) Reduction for pre-financing loans",
    240: "(-) Fiduciary assets",
    250: "(-) Intragroup exposures (solo basis)",
    251: "(-) IPS exposures",
    252: "(-) Guaranteed export credits",
    253: "(-) Excess collateral at triparty agents",
    254: "(-) Securitised exposures with risk transfer",
    255: "(-) Exposures to central bank",
    256: "(-) Ancillary services - CSDs",
    257: "(-) Ancillary services - designated institutions",
    260: "(-) Exposures under Article 429a(1)(j)",
    261: "(-) Public sector investments",
    262: "(-) Promotional loans (public development institution)",
    263: "(-) Promotional loans (entity directly set up by gov.)",
    264: "(-) Promotional loans via intermediate credit institution",
    265: "(-) Passing-through promotional loans (public institution)",
    266: "(-) Passing-through promotional loans (direct gov. entity)",
    267: "(-) Passing-through promotional loans (intermediated)",
    270: "(-) Asset deduction - Tier 1"
}

def somme_sans_nan(row, colonnes):
    return sum(row.get(col) for col in colonnes if pd.notna(row.get(col)))

def charger_donnees_levier():
    dossier = "data"
    bilan_path = os.path.join(dossier, "bilan.xlsx")
    corep_path = os.path.join(dossier, "solvabilite.xlsx")
    levier_path = os.path.join(dossier, "levier.xlsx")

    bilan = pd.read_excel(bilan_path)
    bilan = bilan.iloc[2:].reset_index(drop=True)
    if "Unnamed: 1" in bilan.columns:
        bilan = bilan.drop(columns=["Unnamed: 1"])
    for i, col in enumerate(bilan.columns):
        if str(col).startswith("Unnamed: 6"):
            bilan = bilan.iloc[:, :i]
            break
    bilan.columns.values[0] = "Poste du Bilan"
    bilan.columns.values[1:5] = ["2024", "2025", "2026", "2027"]
    bilan = bilan.dropna(how="all").reset_index(drop=True)
    if 25 in bilan.index:
        bilan = bilan.drop(index=25).reset_index(drop=True)

    df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
    if "Unnamed: 2" in df_c01.columns:
        df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
    if "row" in df_c01.columns and "0010" in df_c01.columns:
        df_c01 = df_c01[["row", "0010"]].reset_index(drop=True)

    try:
        df_c4700 = pd.read_excel(levier_path, sheet_name="C4700", header=9)
        df_c4700 = df_c4700.iloc[:, 2:]
        colonnes_utiles = [col for col in df_c4700.columns if not col.startswith('Unnamed: 4')]
        df_c4700 = df_c4700[colonnes_utiles]
        if 'Unnamed: 5' in df_c4700.columns:
            df_c4700 = df_c4700.drop(columns=['Unnamed: 5'])
        df_c4700 = df_c4700.rename(columns={'Unnamed: 2': 'Row', 'Unnamed: 3': 'Amount'})
        df_c4700['Row'] = pd.to_numeric(df_c4700['Row'], errors='coerce')
        df_c4700['Amount'] = pd.to_numeric(df_c4700['Amount'], errors='coerce')
    except Exception as e:
        st.error(f"Erreur lors du chargement de C4700: {e}")
        raise

    return bilan, df_c01, df_c4700

def get_capital_planning_below(bilan_df, poste_bilan, annee="2025"):
    bilan_df = bilan_df.reset_index(drop=True)
    index_poste = bilan_df[bilan_df["Poste du Bilan"].astype(str).str.strip() == poste_bilan].index
    if not index_poste.empty:
        i = index_poste[0] + 1
        if i < len(bilan_df) and annee in bilan_df.columns:
            valeur = bilan_df.loc[i, annee]
            if pd.notna(valeur):
                return valeur
    return None

def calcul_total_exposure(df_c4700, valeur_stressee_0190=None):
    rows_a_inclure = [10, 20, 30, 40, 50, 61, 65, 71, 81, 91, 92, 93,
                      101, 102, 103, 104, 110, 120, 130, 140, 150, 160, 170, 180,
                      181, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 196,
                      197, 198, 200, 210, 220, 230, 235, 240, 250, 251, 252, 253,
                      254, 255, 256, 257, 260, 261, 262, 263, 264, 265, 266, 267, 270]

    df_temp = df_c4700.copy()
    if valeur_stressee_0190 is not None:
        idx = df_temp[df_temp['Row'] == 190].index
        if not idx.empty:
            df_temp.loc[idx[0], 'Amount'] += valeur_stressee_0190

    total_exposure = (
        df_temp[df_temp['Row'].isin(rows_a_inclure)]
        .apply(lambda row: somme_sans_nan(row, ['Amount']), axis=1)
        .sum()
    )
    return total_exposure, df_temp

def calculer_ratio_levier(fonds_propres, exposition_totale):
    return (fonds_propres / exposition_totale) * 100 if exposition_totale > 0 else None
def calculer_ratio_levier_double_etape(bilan, postes_cibles, stress_pct, horizon, df_c4700, df_c01, return_details=False):
    """
    Calcul du ratio de levier avec capital planning et stress.
    """
    annees = [str(2024 + i) for i in range(horizon + 1)]
    resultats = []
    logs = []

    # Fonds propres de base
    fonds_propres = df_c01.loc[df_c01["row"] == 20, "0010"].values[0]
    exposition_totale_initiale, df_c4700_initial = calcul_total_exposure(df_c4700)

    logs.append(f"Fonds propres initiaux (T1) : {fonds_propres:,.0f}")
    logs.append(f"Exposition totale initiale : {exposition_totale_initiale:,.0f}")

    # Stock valeurs initiales
    valeurs_initiales = {}
    for poste in postes_cibles:
        idx = bilan[bilan["Poste du Bilan"] == poste].index
        if not idx.empty:
            val = bilan.loc[idx[0], "2024"]
            if pd.notna(val):
                valeurs_initiales[poste] = val
                logs.append(f"Valeur initiale '{poste}' : {val:,.0f}")

    # Valeur initiale Other assets
    other_assets_initial = 0
    idx_other_assets = df_c4700[df_c4700['Row'] == 190].index
    if not idx_other_assets.empty:
        other_assets_initial = df_c4700.loc[idx_other_assets[0], 'Amount']
        logs.append(f"Other assets (2024) : {other_assets_initial:,.0f}")

    # === Année 2024 (référence, pas de stress) ===
    ratio_levier_initial = calculer_ratio_levier(fonds_propres, exposition_totale_initiale)
    base_result = {
        "Année": annees[0],
        "Fonds propres": fonds_propres,
        "Exposition totale": exposition_totale_initiale,
        "Ratio de levier": ratio_levier_initial
    }

    if return_details:
        base_result["df_c4700_initial"] = df_c4700_initial
        base_result["df_c4700"] = df_c4700  # 🟢 Ajout clé visible dans recapitulatif

    resultats.append(base_result)

    other_assets_courant = other_assets_initial

    # === Années suivantes (2025+) ===
    for i in range(1, len(annees)):
        annee = annees[i]
        logs.append(f"\n--- Année {annee} ---")

        # Capital planning
        impact_cap_total = 0
        for poste in postes_cibles:
            val_cap = get_capital_planning_below(bilan, poste, annee)
            if val_cap is not None:
                impact_cap_total += val_cap
                logs.append(f"Capital planning {poste} : {val_cap:,.0f}")

        other_assets_courant += impact_cap_total
        logs.append(f"Other assets après capital planning : {other_assets_courant:,.0f}")

        df_cap = df_c4700.copy()
        if not idx_other_assets.empty:
            df_cap.loc[idx_other_assets[0], 'Amount'] = other_assets_courant

        expo_apres_planning, df_c4700_cap = calcul_total_exposure(df_cap)
        logs.append(f"Exposition après capital planning : {expo_apres_planning:,.0f}")

        # Stress
        impact_stress_total = 0
        for poste in postes_cibles:
            stress_key = f"Retrait massif des dépôts_Dépôts et avoirs de la clientèle_{poste}"
            stress_poste = st.session_state.get(stress_key, stress_pct)
            progression = i / horizon
            stress_annuel = (stress_poste / 100) * progression
            ref = valeurs_initiales.get(poste, 0)
            impact = ref * stress_annuel
            impact_stress_total += impact
            logs.append(f"{poste} - stress {stress_poste}% => impact {impact:,.0f}")

        other_assets_stresse = other_assets_courant + impact_stress_total
        df_stresse = df_c4700_cap.copy()
        if not idx_other_assets.empty:
            df_stresse.loc[idx_other_assets[0], 'Amount'] = other_assets_stresse

        expo_totale, df_c4700_stresse = calcul_total_exposure(df_stresse)
        ratio_final = calculer_ratio_levier(fonds_propres, expo_totale)

        row = {
            "Année": annee,
            "Fonds propres": fonds_propres,
            "Exposition totale": expo_totale,
            "Ratio de levier": ratio_final
        }

        if return_details:
            row["df_c4700_cap"] = df_c4700_cap
            row["df_c4700_stresse"] = df_c4700_stresse

        resultats.append(row)

    df_resultats = pd.DataFrame(resultats)

    if return_details:
        with st.expander("Logs de calcul détaillés - Levier"):
            for log in logs:
                st.text(log)

    return df_resultats