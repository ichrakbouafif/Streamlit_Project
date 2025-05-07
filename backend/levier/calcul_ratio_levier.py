import pandas as pd
import os
import streamlit as st

def somme_sans_nan(row, colonnes):
    return sum(row.get(col) for col in colonnes if pd.notna(row.get(col)))

def charger_donnees_levier():
    # Fonction pour charger les données - inchangée
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
    bilan.columns.values[1] = "2024"
    bilan.columns.values[2] = "2025"
    bilan.columns.values[3] = "2026"
    bilan.columns.values[4] = "2027"
    bilan = bilan.dropna(how="all").reset_index(drop=True)
    if 25 in bilan.index:
        bilan = bilan.drop(index=25).reset_index(drop=True)

    df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
    if "Unnamed: 2" in df_c01.columns:
        df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
    if "row" in df_c01.columns and "0010" in df_c01.columns:
        df_c01 = df_c01[["row", "0010"]]
    df_c01 = df_c01.reset_index(drop=True)

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
    """
    Récupère la valeur du capital planning qui se trouve dans la ligne en dessous du poste du bilan.
    """
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
    rows_a_inclure = [
        10, 20, 30, 40, 50, 61, 65, 71, 81, 91, 92, 93,
        101, 102, 103, 104, 110, 120, 130, 140, 150, 160, 170, 180,
        181, 185, 186, 187, 188, 189, 190, 191, 193, 194, 195, 196,
        197, 198, 200, 210, 220, 230, 235, 240, 250, 251, 252, 253,
        254, 255, 256, 257, 260, 261, 262, 263, 264, 265, 266, 267, 270
    ]

    # Créer une copie pour ne pas modifier l'original
    df_temp = df_c4700.copy()
   
    # Si une valeur stressée est fournie, l'ajouter à la ligne 190
    if valeur_stressee_0190 is not None:
        idx = df_temp[df_temp['Row'] == 190].index
        if not idx.empty:
            df_temp.loc[idx[0], 'Amount'] += valeur_stressee_0190

    total_exposure = (
        df_temp[df_temp['Row'].isin(rows_a_inclure)]
        .apply(lambda row: somme_sans_nan(row, ['Amount']), axis=1)
        .sum()
    )
    return total_exposure

def calculer_ratio_levier(fonds_propres, exposition_totale):
    if exposition_totale > 0:
        return (fonds_propres / exposition_totale) * 100
    return None

def calculer_ratio_levier_double_etape(bilan, postes_cibles, stress_pct, horizon, df_c4700, df_c01):
    annees = [str(2024 + i) for i in range(horizon + 1)]
    resultats = []
    logs = []

    # Récupérer les fonds propres et l'exposition totale initiale
    fonds_propres = df_c01.loc[df_c01["row"] == 20, "0010"].values[0]
    exposition_totale_initiale = calcul_total_exposure(df_c4700)

    logs.append(f"Fonds propres de base: {fonds_propres:,.0f}")
    logs.append(f"Exposition totale initiale: {exposition_totale_initiale:,.0f}")

    # Stocker les valeurs initiales des postes cibles
    valeurs_initiales = {}
    for poste in postes_cibles:
        indice_poste = bilan[bilan["Poste du Bilan"] == poste].index
        if not indice_poste.empty:
            valeur = bilan.loc[indice_poste[0], "2024"]
            if pd.notna(valeur):
                valeurs_initiales[poste] = valeur
                logs.append(f"Valeur initiale '{poste}': {valeur:,.0f}")

    # Première année - pas de stress
    resultats.append({
        "Année": annees[0],
        "Fonds propres": fonds_propres,
        "Exposition totale": exposition_totale_initiale,
        "Ratio de levier": calculer_ratio_levier(fonds_propres, exposition_totale_initiale)
    })

    # Récupérer la valeur initiale de Other assets (ligne 190)
    other_assets_initial = 0
    idx_other_assets = df_c4700[df_c4700['Row'] == 190].index
    if not idx_other_assets.empty:
        other_assets_initial = df_c4700.loc[idx_other_assets[0], 'Amount']
        logs.append(f"Valeur initiale 'Other assets' (ligne 190): {other_assets_initial:,.0f}")
    
    # Valeur courante de Other assets qui sera mise à jour chaque année
    other_assets_courant = other_assets_initial
    
    # Pour chaque année après 2024
    for i in range(1, len(annees)):
        annee = annees[i]
        logs.append(f"\n--- Calcul pour l'année {annee} (étape {i}) ---")
        
        # Récupérer les valeurs du capital planning pour l'année courante en utilisant la fonction get_capital_planning_below
        impact_capital_planning_total = 0
        for poste in postes_cibles:
            # Utiliser la fonction get_capital_planning_below pour extraire la valeur du capital planning
            capital_planning_valeur = get_capital_planning_below(bilan, poste, annee)
            if capital_planning_valeur is not None:
                logs.append(f"Capital planning '{poste}' pour {annee}: {capital_planning_valeur:,.0f}")
                impact_capital_planning_total += capital_planning_valeur
        
        logs.append(f"Impact capital planning total pour {annee}: {impact_capital_planning_total:,.0f}")
        
        # Mettre à jour la valeur de Other assets avec le capital planning
        other_assets_courant += impact_capital_planning_total
        logs.append(f"Other assets après capital planning pour {annee}: {other_assets_courant:,.0f}")
        
        # Créer une copie du dataframe COREP et mettre à jour la ligne Other assets
        corep_avec_planning = df_c4700.copy()
        if not idx_other_assets.empty:
            corep_avec_planning.loc[idx_other_assets[0], 'Amount'] = other_assets_courant
        
        # Calculer l'exposition totale après capital planning
        exposition_apres_planning = calcul_total_exposure(corep_avec_planning)
        logs.append(f"Exposition totale après capital planning: {exposition_apres_planning:,.0f}")
        
        # Maintenant, appliquer le stress pour l'année courante
        impact_stress_total = 0
        for poste in postes_cibles:
            # Récupérer le stress pour ce poste depuis session_state
            stress_key = f"Retrait massif des dépôts_Dépôts et avoirs de la clientèle_{poste}"
            stress_poste = st.session_state.get(stress_key, 0)
            
            # Appliquer une progression linéaire du stress sur l'horizon
            ratio_progression = i / horizon
            stress_annuel = (stress_poste / 100) * ratio_progression
            
            # Calculer l'impact du stress sur le poste
            valeur_reference = valeurs_initiales.get(poste, 0)
            impact_stress = valeur_reference * stress_annuel
            impact_stress_total += impact_stress
            
            logs.append(f"Stress pour '{poste}' ({stress_key}): {stress_poste}% - Impact année {annee}: {impact_stress:,.0f}")
        
        # Ajouter l'impact du stress à l'exposition après capital planning
        exposition_totale = exposition_apres_planning + impact_stress_total
        ratio_levier = calculer_ratio_levier(fonds_propres, exposition_totale)
        
        logs.append(f"Impact stress total année {annee}: {impact_stress_total:,.0f}")
        logs.append(f"Exposition totale après capital planning et stress: {exposition_totale:,.0f}")
        logs.append(f"Ratio de levier: {ratio_levier:.4f}%")
        
        resultats.append({
            "Année": annee,
            "Fonds propres": fonds_propres,
            "Exposition totale": exposition_totale,
            "Ratio de levier": ratio_levier
        })

    df_resultats = pd.DataFrame(resultats)

    with st.expander("Logs de calcul détaillés - Levier"):
        for log in logs:
            st.text(log)

    return df_resultats[["Année", "Fonds propres", "Exposition totale", "Ratio de levier"]]