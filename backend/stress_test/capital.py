import numpy as np
import pandas as pd
def recuperer_corep_principal_projete(resultats, annee: str):
    """
    Récupère les tableaux COREP principaux projetés pour une année donnée.

    Args:
        resultats (dict): Résultats issus de simuler_solvabilite_pluriannuelle()
        annee (str): Année cible au format '2025', '2026', ...

    Returns:
        dict: Contient df_c01, C0700_0008_1, C0700_0009_1, C0700_0010_1, rwa_total
    """
    if annee not in resultats:
        st.error(f" Année {annee} non trouvée dans les résultats simulés.")
        return {}

    data = resultats[annee]
    blocs = data.get("blocs_rwa", {})

    corep = {
        "df_c01": data.get("df_c01", pd.DataFrame()),
        "C0700_0008_1": blocs.get("C0700_0008_1", pd.DataFrame()),
        "C0700_0009_1": blocs.get("C0700_0009_1", pd.DataFrame()),
        "C0700_0010_1": blocs.get("C0700_0010_1", pd.DataFrame()),
        "rwa_total": data.get("rwa", None)
    }

    return corep
def extraire_rwa_par_bloc(blocs_c0700: dict) -> dict:
    """
    Calcule le RWA (colonne 0220) total pour chaque bloc C0700 (Retail, Corporate, Hypothécaire).

    Args:
        blocs_c0700 (dict): dictionnaire contenant les DataFrames de chaque bloc (C0700_0008_1, etc.)

    Returns:
        dict: {"C0700_0008_1": rwa_retail, "C0700_0009_1": rwa_corporate, "C0700_0010_1": rwa_hypo}
    """
    rwa_blocs = {}

    for nom_bloc, df_bloc in blocs_c0700.items():
        if "row" in df_bloc.columns and "0220" in df_bloc.columns:
            rwa_total = df_bloc[df_bloc["row"].isin([70.0, 80.0, 110.0])]["0220"].fillna(0).sum()
            rwa_blocs[nom_bloc] = rwa_total
        else:
            rwa_blocs[nom_bloc] = 0.0

    return rwa_blocs
def calculer_delta_rwa_et_rwa_total_stresse(corep_projete: dict, corep_stresse: dict) -> dict:
    """
    Compare les blocs projetés et stressés pour calculer :
    - le ΔRWA par bloc C0700
    - le ΔRWA total
    - le RWA total stressé (en ajoutant les deltas à rwa_total projeté)

    Args:
        corep_projete (dict): issu de recuperer_corep_principal_projete()
        corep_stresse (dict): dictionnaire avec les mêmes blocs modifiés par le stress

    Returns:
        dict: {
            "delta_rwa_par_bloc": {bloc: delta_rwa, ...},
            "delta_total": float,
            "rwa_total_stresse": float
        }
    """
    blocs = ["C0700_0008_1", "C0700_0009_1", "C0700_0010_1"]
    delta_rwa = {}
    total_delta = 0.0

    for bloc in blocs:
        df_projete = corep_projete.get(bloc, pd.DataFrame())
        df_stresse = corep_stresse.get(bloc, pd.DataFrame())

        rwa_projete = df_projete[df_projete["row"].isin([70.0, 80.0, 110.0])]["0220"].fillna(0).sum()
        rwa_stresse = df_stresse[df_stresse["row"].isin([70.0, 80.0, 110.0])]["0220"].fillna(0).sum()

        delta = rwa_stresse - rwa_projete
        delta_rwa[bloc] = delta
        total_delta += delta

    rwa_projete_total = corep_projete.get("rwa_total", 0)
    rwa_total_stresse = rwa_projete_total + total_delta

    return {
        "delta_rwa_par_bloc": delta_rwa,
        "delta_total": total_delta,
        "rwa_total_stresse": rwa_total_stresse
    }

####calcul de c0700 en tenant compte de 80.0 et 70.0
def somme_sans_nan(row, cols):
    """Calcule la somme des valeurs non-NaN pour les colonnes spécifiées"""
    return sum(row.get(c, 0) for c in cols if pd.notna(row.get(c, 0)))

def calculer_0040(row):
    return somme_sans_nan(row, ["0010", "0030"])

def calculer_0110(row):
    return somme_sans_nan(row, ["0040", "0050", "0060", "0070", "0080", "0090", "0100"])

def calculer_0150(row):
    return somme_sans_nan(row, ["0110", "0120", "0130"])
def calculer_0200(row, debug=False):
    """
    Calcule la colonne 0200 (exposition brute ajustée) selon la nature de la ligne :
    - Ligne 70.0 (on-balance) : 0200 = 0150 (exposition ajustée)
    - Ligne 80.0 (off-balance) : 0200 = 0.2×0170 + 0.5×0180 + 1.0×0190
    - Ligne 110.0 (dérivés) : conserver la valeur existante de 0200 (pas de recalcul)
    - Autres lignes : 0200 reste inchangé ou 0 si absent
    """
    row_type = row.get("row")

    if row_type == 70.0:
        val = row.get("0150", 0)
        return 0 if pd.isna(val) else val

    if row_type == 80.0:
        v170 = 0 if pd.isna(row.get("0170")) else row.get("0170")
        v180 = 0 if pd.isna(row.get("0180")) else row.get("0180")
        v190 = 0 if pd.isna(row.get("0190")) else row.get("0190")
        expo = (0.2 * v170) + (0.5 * v180) + (1.0 * v190)
        if debug:
            st.write(f"Calcul 0200 pour 80.0 : 0.2×{v170} + 0.5×{v180} + 1×{v190} = {expo}")
        return expo

    if row_type == 110.0:
        val = row.get("0200", 0)
        return 0 if pd.isna(val) else val

    # Par défaut : conserver la valeur existante ou mettre à 0
    val = row.get("0200", 0)
    return 0 if pd.isna(val) else val
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
def calculer_0220(row, ratios, debug=False):
    """
    Calcule ou renvoie la valeur existante de la colonne 0220 (RWA).
    - Si ligne = 70.0, 80.0, 110.0 → 0220 = 0200 × ratio
    - Sinon → renvoie 0220 existant ou somme 0215+0216+0217
    """
    row_type = row.get("row")
    expo = row.get("0200", 0)
    if pd.isna(expo):
        expo = 0

    if row_type in [70.0, 80.0, 110.0]:
        ratio = ratios.get(row_type, 0.25)
        rwa = expo * ratio
        if debug:
            st.write(f" Recalcul RWA (ligne {row_type}): Expo={expo:.2f} × Ratio={ratio:.4f} → RWA={rwa:.2f}")
        return rwa

    # Si valeur 0220 déjà présente, on la garde
    if "0220" in row and pd.notna(row["0220"]):
        if debug:
            st.write(f" Utilisation de la valeur existante 0220 pour ligne {row_type}: {row['0220']}")
        return row["0220"]

    # Sinon, calcul alternatif : somme des colonnes RWA partielles
    sum_cols = sum(row.get(col, 0) for col in ["0215", "0216", "0217"] if pd.notna(row.get(col)))
    if debug:
        st.write(f" Somme alternative des RWA (ligne {row_type}): {sum_cols}")
    return sum_cols


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
def appliquer_stress_pnu_sur_c0700(blocs_c0700: dict, tirages_par_segment: dict, debug=False) -> dict:
    """
    Applique le stress PNU sur les blocs C0700 sélectionnés :
    - Soustrait le montant tiré de la ligne 80.0 (off-balance)
    - Ajoute le même montant à la ligne 70.0 (on-balance)
    - Recalcule tout le bloc avec propagation jusqu’au RWA

    Args:
        blocs_c0700 (dict): dictionnaire des blocs C0700 existants
        tirages_par_segment (dict): {"C0700_0008_1": montant, ...}
        debug (bool): affiche les étapes si True

    Returns:
        dict: blocs_c0700 modifiés avec stress appliqué et RWA recalculés
    """
    blocs_stresses = {}

    for feuille, montant in tirages_par_segment.items():
        df = blocs_c0700.get(feuille, pd.DataFrame()).copy()

        if df.empty or montant == 0:
            blocs_stresses[feuille] = df
            continue

        if debug:
            st.write(f" Traitement {feuille} - Montant tiré : {montant:,.2f}")

        # Appliquer -montant sur 80.0 (off-balance)
        idx_80 = df[df["row"] == 80.0].index
        if not idx_80.empty:
            valeur_80 = df.at[idx_80[0], "0010"] or 0
            df.at[idx_80[0], "0010"] = max(valeur_80 - montant, 0)  # pas de négatif
            if debug:
                st.write(f" 80.0 → {valeur_80:,.2f} - {montant:,.2f} = {df.at[idx_80[0], '0010']:,.2f}")

        # Appliquer +montant sur 70.0 (on-balance)
        idx_70 = df[df["row"] == 70.0].index
        if not idx_70.empty:
            valeur_70 = df.at[idx_70[0], "0010"] or 0
            df.at[idx_70[0], "0010"] = valeur_70 + montant
            if debug:
                st.write(f" 70.0 → {valeur_70:,.2f} + {montant:,.2f} = {df.at[idx_70[0], '0010']:,.2f}")

        # Recalcul complet
        df_recalcule = construire_df_c0700_recalcule(df, debug)
        blocs_stresses[feuille] = df_recalcule

    return blocs_stresses
def calculer_ratio_solvabilite_stresse(df_c01: pd.DataFrame, rwa_total_stresse: float, debug=False) -> float:
    """
    Calcule le ratio de solvabilité stressé après recalcul du RWA total.

    Args:
        df_c01 (pd.DataFrame): tableau C01.00 (fonds propres) stressé ou projeté.
        rwa_total_stresse (float): RWA total après stress PNU.
        debug (bool): active l'affichage des valeurs internes.

    Returns:
        float: ratio de solvabilité (Tier 1 / RWA) exprimé en %
    """
    if df_c01.empty or rwa_total_stresse == 0:
        return 0.0

    # Récupérer la valeur de Tier 1 Capital : ligne 1.1.1.2.1 (row 010) col "0100"
    tier1_row = df_c01[df_c01["row"] == 10.0]  # ligne 010
    if tier1_row.empty or "0100" not in df_c01.columns:
        return 0.0

    tier1_value = tier1_row["0100"].values[0]
    if pd.isna(tier1_value) or tier1_value == 0:
        return 0.0

    ratio = (tier1_value / rwa_total_stresse) * 100

    if debug:
        st.write(f" Tier 1: {tier1_value:,.2f}")
        st.write(f" RWA stressé: {rwa_total_stresse:,.2f}")
        st.write(f" Ratio de solvabilité stressé: {ratio:.2f}%")

    return round(ratio, 2)
def executer_stress_pnu_capital(
    resultats_proj: dict,
    annee: str,
    tirages_par_segment: dict,
    horizon: int,
    debug=False
) -> dict:
    """
    Applique le stress PNU capital sur les blocs C0700 cochés à partir d’une année donnée,
    en répartissant l’impact sur l’horizon sélectionné.

    Args:
        resultats_proj (dict): Résultats issus de simuler_solvabilite_pluriannuelle()
        annee (str): Année de départ (ex: '2025')
        tirages_par_segment (dict): {nom_bloc_C0700: montant_total_tiré}
        horizon (int): nombre d’années d’impact (ex: 3)
        debug (bool): active les logs

    Returns:
        dict: {
            "blocs_stresses": dict des blocs recalculés pour la première année,
            "rwa_total_stresse": float,
            "delta_rwa_total": float,
            "ratio_solva_stresse": float
        }
    """
    # 1. Récupérer données projetées de l’année
    donnees = recuperer_corep_principal_projete(resultats_proj, annee)
    df_c01 = donnees.get("df_c01", pd.DataFrame())
    rwa_total_projete = donnees.get("rwa_total", 0)

    if debug:
        st.write(f" Année de départ : {annee}, Horizon : {horizon}")
        st.write(f" RWA total projeté : {rwa_total_projete:,.0f}")

    # 2. Calcul du stress annuel par bloc
    tirages_annuels = {
        feuille: montant / horizon for feuille, montant in tirages_par_segment.items()
    }

    if debug:
        st.write(" Stress annuel appliqué par bloc :")
        for k, v in tirages_annuels.items():
            st.write(f"  {k} → {v:,.0f} par an")

    # 3. Appliquer le stress pour la première année uniquement (itération = 1ère année)
    blocs_originaux = {
        k: donnees[k].copy() for k in tirages_annuels if k in donnees
    }

    blocs_stresses = appliquer_stress_pnu_sur_c0700(blocs_originaux, tirages_annuels, debug=debug)

    # 4. Calcul du delta RWA total
    delta_rwa_total = 0
    for feuille, df_stresse in blocs_stresses.items():
        if "0220" in df_stresse.columns:
            rwa_stresse = df_stresse["0220"].sum()
            rwa_initiale = blocs_originaux[feuille]["0220"].sum()
            delta = rwa_stresse - rwa_initiale
            delta_rwa_total += delta

            if debug:
                st.write(f" Bloc {feuille} — ΔRWA : {rwa_initiale:,.0f} → {rwa_stresse:,.0f} ➜ Δ = {delta:,.0f}")

    rwa_total_stresse = rwa_total_projete + delta_rwa_total

    # 5. Calcul du ratio de solvabilité stressé
    fonds_propres = df_c01["0100"].sum() if "0100" in df_c01.columns else 0
    ratio_solva_stresse = (fonds_propres / rwa_total_stresse) * 100 if rwa_total_stresse > 0 else 0

    return {
        "blocs_stresses": blocs_stresses,
        "rwa_total_stresse": rwa_total_stresse,
        "delta_rwa_total": delta_rwa_total,
        "ratio_solva_stresse": ratio_solva_stresse
    }
def executer_stress_pnu_capital_pluriannuel(
    resultats_proj: dict,
    annee_debut: str,
    tirages_par_segment: dict,
    horizon: int,
    debug=False
) -> dict:
    """
    Applique le stress PNU capital sur les blocs C0700 cochés à partir d’une année donnée,
    en répartissant l’impact sur l’horizon sélectionné (ex: 3 ans).

    Returns:
        dict: Pour chaque année, contient:
            - blocs_stresses: blocs C0700 recalculés
            - rwa_total_stresse
            - delta_rwa_total
            - ratio_solva_stresse
    """
    resultats_stress = {}

    # 1. Calcul du stress annuel par bloc
    tirages_annuels = {
        feuille: montant / horizon for feuille, montant in tirages_par_segment.items()
    }

    for i in range(horizon):
        annee = str(int(annee_debut) + i)
        donnees = recuperer_corep_principal_projete(resultats_proj, annee)
        df_c01 = donnees.get("df_c01", pd.DataFrame())
        rwa_total_projete = donnees.get("rwa_total", 0)

        if debug:
            st.write(f"\n\u2B50 Traitement de l'année {annee}")
            st.write(f"  - RWA projeté : {rwa_total_projete:,.0f}")

        # 2. Appliquer le stress sur cette année uniquement
        blocs_originaux = {
            k: donnees[k].copy() for k in tirages_annuels if k in donnees
        }

        blocs_stresses = appliquer_stress_pnu_sur_c0700(blocs_originaux, tirages_annuels, debug=debug)

        # 3. Calcul du delta RWA total
        delta_rwa_total = 0
        for feuille, df_stresse in blocs_stresses.items():
            if "0220" in df_stresse.columns:
                rwa_stresse = df_stresse["0220"].sum()
                rwa_initiale = blocs_originaux[feuille]["0220"].sum()
                delta = rwa_stresse - rwa_initiale
                delta_rwa_total += delta

                if debug:
                    st.write(f"  - Bloc {feuille} ➜ ΔRWA : {rwa_initiale:,.0f} → {rwa_stresse:,.0f} = {delta:,.0f}")

        rwa_total_stresse = rwa_total_projete + delta_rwa_total

        # 4. Calcul du ratio de solvabilité stressé
        fonds_propres = df_c01["0100"].sum() if "0100" in df_c01.columns else 0
        ratio_solva_stresse = (fonds_propres / rwa_total_stresse) * 100 if rwa_total_stresse > 0 else 0

        resultats_stress[annee] = {
            "blocs_stresses": blocs_stresses,
            "rwa_total_stresse": rwa_total_stresse,
            "delta_rwa_total": delta_rwa_total,
            "ratio_solva_stresse": ratio_solva_stresse
        }

    return resultats_stress
import pandas as pd
import streamlit as st

""" def afficher_resultats_solva_tirage_pnu(bilan_stresse, params, resultats_proj):
    try:
        st.markdown("## 🔍 Résultats du stress test PNU – Capital")

        horizon = params.get("horizon", 3)
        pourcentage = params.get("pourcentage", 0.10)

        # === Étape 1 : Lecture du bilan
        bilan = pd.read_excel("data/bilan.xlsx").iloc[2:].reset_index(drop=True)
        bilan.columns = bilan.columns.fillna("Poste")
        bilan = bilan.rename(columns={bilan.columns[0]: "Poste", bilan.columns[1]: "2024"})

        # === Étape 2 : Initialisation des tirages par segment cochés
        tirage_par_segment = {}

        if params.get("inclure_corpo", False):
            ligne_corpo = bilan[bilan["Poste"].str.contains("Dont Corpo", case=False, na=False)]
            if not ligne_corpo.empty:
                valeur_corpo = ligne_corpo["2024"].values[0]
                tirage_par_segment["C0700_0009_1"] = valeur_corpo * pourcentage

        if params.get("inclure_retail", False):
            ligne_retail = bilan[bilan["Poste"].str.contains("Dont Retail", case=False, na=False)]
            if not ligne_retail.empty:
                valeur_retail = ligne_retail["2024"].values[0]
                tirage_par_segment["C0700_0008_1"] = valeur_retail * pourcentage

        if params.get("inclure_hypo", False):
            ligne_hypo = bilan[bilan["Poste"].str.contains("Dont Hypo", case=False, na=False)]
            if not ligne_hypo.empty:
                valeur_hypo = ligne_hypo["2024"].values[0]
                tirage_par_segment["C0700_0010_1"] = valeur_hypo * pourcentage

        if not tirage_par_segment:
            st.warning(" Aucun segment sélectionné ou lignes 'Dont' manquantes dans le bilan.")
            return

        # === Étape 3 : Exécution du stress pluriannuel
        resultats_stress = executer_stress_pnu_capital_pluriannuel(
            resultats_proj=resultats_proj,
            annee_debut="2025",
            tirages_par_segment=tirage_par_segment,
            horizon=horizon,
            debug=True
        )

        # === Étape 4 : Construction du tableau récapitulatif pour affichage
        recap_data = []
        for i in range(horizon):
            annee = str(2025 + i)
            resultat = resultats_stress.get(annee)
            if not resultat:
                continue

            recap_data.append({
                "Année": annee,
                "Fonds propres": resultats_proj[annee]["fonds_propres"],
                "RWA total": resultat["rwa_total_stresse"],
                "Ratio de solvabilité (%)": resultat["ratio_solva_stresse"]
            })

        # === Étape 5 : Affichage du tableau récapitulatif formaté
        if recap_data:
            from backend.ratios_baseline.capital_projete import format_large_number  # si tu veux formatter

            st.markdown("## Tableau récapitulatif – PNU Capital")
            df_recap = pd.DataFrame(recap_data)
            df_recap["Fonds propres"] = df_recap["Fonds propres"].apply(lambda x: f"{x:,.2f}")
            df_recap["RWA total"] = df_recap["RWA total"].apply(lambda x: f"{x:,.2f}")
            df_recap["Ratio de solvabilité (%)"] = df_recap["Ratio de solvabilité (%)"].apply(lambda x: f"{x:.2f}%")
            st.dataframe(df_recap, use_container_width=True)

        # === Étape 6 : Affichage détaillé (C0700 recalculés par bloc)
        for annee in resultats_stress:
            result = resultats_stress[annee]
            with st.expander(f" Détails de l’année {annee}"):
                st.metric("Ratio de solvabilité stressé", f"{result['ratio_solva_stresse']:.2f}%")
                st.write(f"RWA stressé : {result['rwa_total_stresse']:,.0f}")
                st.write(f"Δ RWA : {result['delta_rwa_total']:,.0f}")

                st.markdown("### Blocs C0700 recalculés")
                for nom_bloc, df in result["blocs_stresses"].items():
                    nom_affiche = {
                        "C0700_0008_1": "Retail",
                        "C0700_0009_1": "Corporate",
                        "C0700_0010_1": "Hypothécaire"
                    }.get(nom_bloc, nom_bloc)
                    st.markdown(f"**{nom_affiche}**")
                    st.dataframe(df)

    except Exception as e:
        st.error(f"Erreur dans le stress PNU capital : {e}")
        import traceback
        st.error(traceback.format_exc())
 """