import pandas as pd
import os
import streamlit as st


# === Chargement des données ===
def charger_donnees():
    dossier = "data"
    bilan_path = os.path.join(dossier, "bilan.xlsx")
    corep_path = os.path.join(dossier, "solvabilite.xlsx")

    # === BILAN ===
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

    # === C01 ===
    df_c01 = pd.read_excel(corep_path, sheet_name="C0100", header=8)
    if "Unnamed: 2" in df_c01.columns:
        df_c01 = df_c01.rename(columns={"Unnamed: 2": "row"})
    df_c01 = df_c01[["row", "0010"]] if "row" in df_c01.columns and "0010" in df_c01.columns else df_c01
    df_c01 = df_c01.reset_index(drop=True)

    # === C02 ===
    df_c02 = pd.read_excel(corep_path, sheet_name="C0200", header=8)
    df_c02 = df_c02.drop(columns=["Unnamed: 0", "Unnamed: 1"], errors='ignore')
    if "Unnamed: 2" in df_c02.columns:
        df_c02 = df_c02.rename(columns={"Unnamed: 2": "row"})
    if "Unnamed: 4" in df_c02.columns:
        df_c02 = df_c02.drop(columns=["Unnamed: 4"])
    df_c02 = df_c02[["row", "0010"]] if "row" in df_c02.columns and "0010" in df_c02.columns else df_c02
    df_c02.reset_index(drop=True, inplace=True)

    # === BLOC INSTITUTIONNEL (C0700_0007_1) ===
    df_raw_bloc = pd.read_excel(corep_path, sheet_name="C0700_0007_1", header=12)
    df_bloc = df_raw_bloc.iloc[8:15].copy()
    colonnes_depart = df_raw_bloc.columns.get_loc("Unnamed: 2")
    df_bloc = df_bloc.iloc[:, colonnes_depart:]
    df_bloc.rename(columns={"Unnamed: 2": "row"}, inplace=True)
    df_bloc = df_bloc.drop(index=8).reset_index(drop=True)

    return bilan, df_c01, df_c02, df_bloc


# === Récupération du capital planning ===
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


# === Sous-fonctions de calcul ===
def somme_sans_nan(row, colonnes):
    return sum(row.get(col) for col in colonnes if pd.notna(row.get(col)))


def calculer_0040(row):
    return somme_sans_nan(row, ["0010", "0030"])


def calculer_0110(row):
    return somme_sans_nan(row, ["0040", "0050", "0060", "0070", "0080", "0090", "0100"])


def calculer_0150(row):
    return somme_sans_nan(row, ["0110", "0120", "0130"])


def calculer_0200(row):
    val_0170 = row.get("0170")
    val_0180 = row.get("0180")
    val_0190 = row.get("0190")
    if row.get("row") == 110.0:
        return row.get("0200")
    elif all(pd.isna(v) for v in [val_0170, val_0180, val_0190]):
        return row.get("0200")
    else:
        return (0.2 * val_0170 if pd.notna(val_0170) else 0) + \
               (0.5 * val_0180 if pd.notna(val_0180) else 0) + \
               (1.0 * val_0190 if pd.notna(val_0190) else 0)


def calculer_ratios_transformation(df):
    """
    Calcule les ratios RWA/Exposition pour chaque type de ligne (on_balance, off_balance, derivatives)
    """
    ratios = {}
    for type_row, nom in [(70.0, "on_balance"), (80.0, "off_balance"), (110.0, "derivatives")]:
        ligne = df[df["row"] == type_row]
        if not ligne.empty:
            rwa = ligne["0215"].values[0] if "0215" in ligne.columns else ligne["0220"].values[0]
            exposure = ligne["0200"].values[0]
            if pd.notna(rwa) and pd.notna(exposure) and exposure != 0:
                ratio_percent = round((rwa / exposure), 4)
                ratios[f"ratio_{nom}"] = ratio_percent
                ratios[type_row] = ratio_percent  # Aussi avec la clé numérique pour faciliter l'accès
            else:
                ratios[f"ratio_{nom}"] = None
                ratios[type_row] = 0.25  # Valeur par défaut si non disponible
        else:
            ratios[f"ratio_{nom}"] = None
            ratios[type_row] = 0.25  # Valeur par défaut si ligne manquante
    return ratios


def calculer_rwa_depuis_exposition(exposure, row_type, ratios):
    """
    Calcule le RWA en fonction de la valeur d'exposition et du type de ligne
    en utilisant les ratios calculés dynamiquement
    """
    # Utiliser les ratios calculés dynamiquement au lieu de valeurs codées en dur
    if row_type in ratios:
        return exposure * ratios[row_type]
    
    # Valeurs par défaut si le ratio n'est pas disponible
    default_coefficients = {
        70.0: 0.272,  # On-balance sheet (environ 27.2% du montant d'exposition)
        80.0: 0.2,    # Off-balance sheet (environ 20% du montant d'exposition)
        110.0: 0.322  # Derivatives (environ 32.2% du montant d'exposition)
    }
    
    # Si le type de ligne est connu, appliquer le coefficient par défaut
    if row_type in default_coefficients:
        return exposure * default_coefficients[row_type]
   
    # Sinon, retourner une valeur par défaut
    return exposure * 0.25  # 25% par défaut


def calculer_0220(row, ratios):
    """
    Calcule la colonne 0220 (RWA) à partir des colonnes d'exposition
    et du type de ligne, en utilisant les ratios calculés dynamiquement
    """
    # Si on travaille avec la ligne 70.0 (on-balance), recalculer le RWA
    # en fonction de la valeur d'exposition
    row_type = row.get("row")
    exposure = row.get("0200", 0)
   
    if row_type in [70.0, 80.0, 110.0]:
        # Pour ces lignes, recalculer le RWA à partir de l'exposition
        return calculer_rwa_depuis_exposition(exposure, row_type, ratios)
   
    # Pour les autres lignes, utiliser la somme des colonnes 0215, 0216, 0217
    val_215 = row.get("0215", 0)
    val_216 = row.get("0216", 0)
    val_217 = row.get("0217", 0)
   
    # Convertir en 0 si NaN
    val_215 = 0 if pd.isna(val_215) else val_215
    val_216 = 0 if pd.isna(val_216) else val_216
    val_217 = 0 if pd.isna(val_217) else val_217
   
    # Somme des trois colonnes
    return val_215 + val_216 + val_217


def construire_df_simulee(df_bloc):
    """
    Recalcule toutes les colonnes dérivées du bloc institutionnel
    à partir des valeurs de base (colonne 0010)
    """
    df_simulee = df_bloc.copy()
    
    # D'abord, calculer les ratios de transformation à partir du DataFrame d'origine
    ratios = calculer_ratios_transformation(df_bloc)
   
    # Pour chaque ligne du bloc
    for idx, row in df_bloc.iterrows():
        row_type = row.get("row")
        value_0010 = row.get("0010")
       
        # Recalcul de la colonne 0040 = somme des colonnes 0010 et 0030
        df_simulee.at[idx, "0040"] = calculer_0040(row)
       
        # Recalcul de la colonne 0110 = somme des colonnes 0040 à 0100
        df_simulee.at[idx, "0110"] = calculer_0110({**row, "0040": df_simulee.at[idx, "0040"]})
       
        # Recalcul de la colonne 0150 = somme des colonnes 0110, 0120, 0130
        df_simulee.at[idx, "0150"] = calculer_0150({**row, "0110": df_simulee.at[idx, "0110"]})
       
        # Recalcul de la colonne 0200 (valeur d'exposition)
        df_simulee.at[idx, "0200"] = value_0010  # Pour simplifier, on suppose que l'exposition = valeur 0010
       
        # Recalcul des RWA en fonction du type de ligne et de l'exposition
        if row_type in [70.0, 80.0, 110.0]:
            # Calcul du RWA pour les lignes spécifiques
            exposure = df_simulee.at[idx, "0200"]
            rwa = calculer_rwa_depuis_exposition(exposure, row_type, ratios)
            df_simulee.at[idx, "0220"] = rwa
            df_simulee.at[idx, "0215"] = rwa  # Mettre à jour aussi la composante principale du RWA
        else:
            # Pour les autres lignes, utiliser le calcul standard
            df_simulee.at[idx, "0220"] = calculer_0220({**row, "0200": df_simulee.at[idx, "0200"]}, ratios)
   
    return df_simulee


def calculer_ratios_solva_double_etape(bilan, poste_cible, stress_pct, horizon, df_bloc_base, df_c01, df_c02):
    """
    Calcule l'évolution du ratio de solvabilité avec application d'un stress sur un poste cible
    Version corrigée avec utilisation des ratios de transformation dynamiques
    """
    annees = [str(2024 + i) for i in range(horizon + 1)]
    resultats = []
    logs = []

    # Valeurs de base
    fonds_propres = df_c01.loc[df_c01["row"] == 20, "0010"].values[0]
    rwa_total_initial = df_c02.loc[df_c02["row"] == 10, "0010"].values[0]
    rwa_bloc_initial = df_bloc_base[df_bloc_base["row"].isin([70.0, 80.0, 110.0])]["0220"].sum()
   
    logs.append(f"Fonds propres de base: {fonds_propres:,.0f}")
    logs.append(f"RWA total initial: {rwa_total_initial:,.0f}")
    logs.append(f"RWA bloc initial: {rwa_bloc_initial:,.0f}")
   
    # Calculer les ratios de RWA pour chaque type d'exposition dans le COREP de référence
    # IMPORTANT: Utiliser la fonction calculer_ratios_transformation
    ratios_reference = calculer_ratios_transformation(df_bloc_base)
    
    for row_type, nom in [(70.0, "on_balance"), (80.0, "off_balance"), (110.0, "derivatives")]:
        logs.append(f"Ratio RWA/Exposition pour ligne {row_type} ({nom}): {ratios_reference.get(row_type, 0.25):.4f}")
   
    # Gardons une copie du bloc de référence
    df_bloc_ref = df_bloc_base.copy()

    # Calculons pour chaque année
    for i, annee in enumerate(annees):
        logs.append(f"\n--- Calcul pour l'année {annee} (étape {i}) ---")
       
        # Étape 1: Appliquer le capital planning
        df_bloc_cap = df_bloc_ref.copy()
        idx_70 = df_bloc_cap[df_bloc_cap["row"] == 70.0].index[0] if not df_bloc_cap[df_bloc_cap["row"] == 70.0].empty else None
        
        if idx_70 is None:
            logs.append(f"❌ ERREUR: Ligne 70.0 non trouvée dans le bloc")
            raise ValueError(f"❌ Ligne 70.0 non trouvée dans le bloc")

        if i == 0:
            # Pour l'année 0 (2024), nous utilisons les valeurs de référence
            df_bloc_stresse = df_bloc_cap.copy()
            logs.append(f"Année 0: Utilisation des valeurs de référence")
        else:
            # Pour les années suivantes, appliquer le capital planning puis le stress
            valeur_capital = get_capital_planning_below(bilan, poste_cible, annee=annee)
            if valeur_capital is None:
                logs.append(f"❌ ERREUR: Capital planning manquant pour '{poste_cible}' en {annee}")
                raise ValueError(f"❌ Capital planning manquant pour '{poste_cible}' en {annee}")
           
            logs.append(f"Capital planning pour {poste_cible} en {annee}: {valeur_capital:,.0f}")
           
            # Valeur avant mise à jour
            valeur_avant = df_bloc_cap.at[idx_70, "0010"]
            logs.append(f"Valeur ligne 70.0 avant mise à jour: {valeur_avant:,.0f}")
               
            # Ajouter la valeur du capital planning
            nouvelle_valeur = valeur_avant + valeur_capital
            df_bloc_cap.at[idx_70, "0010"] = nouvelle_valeur
            logs.append(f"Nouvelle valeur ligne 70.0 après capital planning: {nouvelle_valeur:,.0f} ({valeur_avant:,.0f} + {valeur_capital:,.0f})")
           
            # Recalculer l'exposition et les RWA
            # On suppose que l'exposition = valeur 0010 pour cette ligne
            df_bloc_cap.at[idx_70, "0200"] = nouvelle_valeur
           
            # Utiliser le ratio de RWA/Exposition calculé dynamiquement pour calculer le nouveau RWA
            ratio_rwa = ratios_reference.get(70.0, 0.272)  # Utiliser le ratio calculé ou 27.2% par défaut
            nouveau_rwa = nouvelle_valeur * ratio_rwa
            df_bloc_cap.at[idx_70, "0220"] = nouveau_rwa
            df_bloc_cap.at[idx_70, "0215"] = nouveau_rwa  # Mettre à jour aussi la composante principale du RWA
           
            logs.append(f"RWA recalculé après capital planning: {nouveau_rwa:,.0f} ({nouvelle_valeur:,.0f} × {ratio_rwa:.4f})")

            # Étape 2: Appliquer le stress cumulé
            stress_cumule = (stress_pct / 100) * (i / horizon)
            logs.append(f"Stress cumulé: {stress_cumule:.4f} ({stress_pct}% × {i}/{horizon})")
           
            # Appliquer le stress à la valeur après capital planning
            valeur_stressee = nouvelle_valeur * (1 + stress_cumule)
            logs.append(f"Valeur après stress: {valeur_stressee:,.0f} ({nouvelle_valeur:,.0f} × (1 + {stress_cumule:.4f}))")
           
            # Créer un bloc stressé
            df_bloc_stresse = df_bloc_cap.copy()
            df_bloc_stresse.at[idx_70, "0010"] = valeur_stressee
            df_bloc_stresse.at[idx_70, "0200"] = valeur_stressee  # Mettre à jour l'exposition
           
            # Recalculer le RWA pour la ligne stressée en utilisant le ratio calculé dynamiquement
            rwa_stresse = valeur_stressee * ratio_rwa
            df_bloc_stresse.at[idx_70, "0220"] = rwa_stresse
            df_bloc_stresse.at[idx_70, "0215"] = rwa_stresse  # Mettre à jour aussi la composante principale du RWA
           
            logs.append(f"RWA recalculé après stress: {rwa_stresse:,.0f} ({valeur_stressee:,.0f} × {ratio_rwa:.4f})")

        # Étape 3: Calculer le nouveau RWA total et le ratio de solvabilité
        # Calculer le RWA du bloc stressé (somme des lignes 70, 80 et 110)
        rwa_bloc_stresse = df_bloc_stresse[df_bloc_stresse["row"].isin([70.0, 80.0, 110.0])]["0220"].sum()
        logs.append(f"RWA bloc stressé: {rwa_bloc_stresse:,.0f}")
       
        # Calculer la variation de RWA
        delta_rwa = rwa_bloc_stresse - rwa_bloc_initial
        logs.append(f"Delta RWA: {delta_rwa:,.0f} ({rwa_bloc_stresse:,.0f} - {rwa_bloc_initial:,.0f})")
       
        # Calculer le nouveau RWA total
        rwa_total = rwa_total_initial + delta_rwa
        logs.append(f"RWA total stressé: {rwa_total:,.0f} ({rwa_total_initial:,.0f} + {delta_rwa:,.0f})")
       
        # Calculer le ratio de solvabilité
        ratio_solva = (fonds_propres / rwa_total) * 100 if rwa_total else None
        logs.append(f"Ratio de solvabilité: {ratio_solva:.4f}% ({fonds_propres:,.0f} / {rwa_total:,.0f} × 100)")

        # Ajouter les résultats pour cette année
        resultats.append({
            "Année": annee,
            "Fonds propres": fonds_propres,
            "RWA total": rwa_total,
            "Ratio de solvabilité": ratio_solva
        })

        # Pour l'année suivante, nous partons du bloc avec capital planning
        df_bloc_ref = df_bloc_cap.copy()

    # Créer un DataFrame avec les résultats
    df_resultats = pd.DataFrame(resultats)
   
    # Afficher les logs dans Streamlit si disponible
    try:
        with st.expander("Logs de calcul détaillés - Solvabilité"):
            for log in logs:
                st.text(log)
    except:
        pass
   
    # Retourner uniquement les colonnes nécessaires
    return df_resultats[["Année", "Fonds propres", "RWA total", "Ratio de solvabilité"]]