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
        if debug:
            st.warning("❌ Données C01 ou RWA stressé manquants")
        return 0.0

    if "0100" not in df_c01.columns:
        if debug:
            st.warning("❌ Colonne 0100 manquante dans df_c01")
        return 0.0

    tier1_row = df_c01[df_c01["row"] == 10.0]
    if tier1_row.empty:
        if debug:
            st.warning("❌ Ligne row 10.0 manquante dans df_c01")
        return 0.0

    tier1_value = tier1_row["0100"].values[0]
    if pd.isna(tier1_value) or tier1_value == 0:
        if debug:
            st.warning("❌ Tier 1 vide ou nul")
        return 0.0

    ratio = (tier1_value / rwa_total_stresse) * 100

    if debug:
        st.markdown("### 🔍 Détail du calcul du ratio de solvabilité")
        st.write(f"Tier 1 (ligne 10.0, col 0100) : {tier1_value:,.2f}")
        st.write(f"RWA total stressé : {rwa_total_stresse:,.2f}")
        st.write(f"Ratio de solvabilité : {ratio:.2f}%")

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

        # 4. Calcul du ratio de solvabilité stressé (CET1 / RWA)
        fonds_propres = 0
        if not df_c01.empty and "0100" in df_c01.columns:
            tier1_row = df_c01[df_c01["row"] == 10.0]
            if not tier1_row.empty:
                fonds_propres = tier1_row["0100"].values[0]
                if pd.isna(fonds_propres):
                    fonds_propres = 0

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
def appliquer_tirage_pnu_silencieux(bilan_df, params):
    from backend.ratios_baseline.capital_projete import simuler_solvabilite_pluriannuelle
    from backend.stress_test.capital import executer_stress_pnu_capital_pluriannuel

    # 1. Charger ou simuler les résultats projetés de solvabilité
    resultats_proj = st.session_state.get("resultats_solva")
    if resultats_proj is None:
        resultats_proj = simuler_solvabilite_pluriannuelle()
        st.session_state["resultats_solva"] = resultats_proj

    # 2. Extraire les paramètres
    pourcentage = params.get("pourcentage", 0.10)
    horizon = params.get("horizon", 3)

    # 3. Déterminer les montants à tirer par segment
    tirage_par_segment = {}

    if params.get("inclure_corpo"):
        ligne = bilan_df[bilan_df["Poste du Bilan"].str.contains("Dont Corpo", case=False, na=False)]
        if not ligne.empty:
            tirage_par_segment["C0700_0009_1"] = ligne["2024"].values[0] * pourcentage

    if params.get("inclure_retail"):
        ligne = bilan_df[bilan_df["Poste du Bilan"].str.contains("Dont Retail", case=False, na=False)]
        if not ligne.empty:
            tirage_par_segment["C0700_0008_1"] = ligne["2024"].values[0] * pourcentage

    if params.get("inclure_hypo"):
        ligne = bilan_df[bilan_df["Poste du Bilan"].str.contains("Dont Hypo", case=False, na=False)]
        if not ligne.empty:
            tirage_par_segment["C0700_0010_1"] = ligne["2024"].values[0] * pourcentage

    if not tirage_par_segment:
        st.warning("⚠️ Aucun segment PNU valide trouvé.")
        return

    # 4. Appliquer le stress PNU (capital)
    resultats_stress = executer_stress_pnu_capital_pluriannuel(
        resultats_proj=resultats_proj,
        annee_debut="2025",
        tirages_par_segment=tirage_par_segment,
        horizon=horizon,
        debug=False
    )

    # 5. Stocker les résultats pour combinaison future
    st.session_state["delta_rwa_pnu"] = {
        annee: resultat["delta_rwa_total"]
        for annee, resultat in resultats_stress.items()
    }

    st.session_state["blocs_stresses_pnu"] = {
        annee: resultat["blocs_stresses"]
        for annee, resultat in resultats_stress.items()
    }
def afficher_corep_levier_detaille(df_c4700_stresse, key_prefix="corep_levier"):
    #st.markdown("**Détails du ratio de levier COREP**")

    # Mapping complet des lignes COREP C47.00 avec description
    mapping_rows_levier = {
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

    df = df_c4700_stresse.copy()

    if 'Row' not in df.columns or 'Amount' not in df.columns:
        st.warning("Données de levier manquantes ou mal formatées.")
        st.dataframe(df)
        return

    # Nettoyage et mapping
    df['Row'] = pd.to_numeric(df['Row'], errors='coerce')
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df["Amount"] = df["Amount"].apply(
        lambda x: f"{x:,.2f}".format(x).replace(",", " ").replace(".", ".") if pd.notnull(x) else ""
    )
    df['Description'] = df['Row'].map(mapping_rows_levier)

    colonnes_affichees = ['Row', 'Amount', 'Description']
    df_affiche =df[colonnes_affichees]
    df_affiche['Row'] = df_affiche['Row'].apply(lambda x: f"{int(x):04d}" if pd.notna(x) else "")


    # Fonction de style pour colorer la ligne Other assets en rouge
    def highlight_other_assets(row):
        if row['Row'] == '0190':
            return ['background-color: #ffcccc'] * len(row)
        return [''] * len(row)

    # Affichage stylisé
    st.dataframe(df_affiche.style.apply(highlight_other_assets, axis=1), use_container_width=True)

    # Légende explicative
    st.caption("🔴 La ligne 'Other assets' (ligne 190) représente la variable stressée dans le calcul du ratio de levier.")

def afficher_ratios_rwa(df_bloc):

    """

    Affiche les ratios RWA / Exposition pour les lignes principales COREP.

    """

    import pandas as pd


    st.markdown("**Ratios RWA/Exposition**")


    lignes = {

        70.0: "On-Balance Sheet",

        80.0: "Off-Balance Sheet",

        110.0: "Derivatives"

    }


    ratios_data = []

    for row_type, label in lignes.items():

        ligne = df_bloc[df_bloc["row"] == row_type]

        if not ligne.empty:

            exposition = ligne["0200"].values[0] if "0200" in ligne.columns and not ligne["0200"].empty else 0

            rwa = ligne["0220"].values[0] if "0220" in ligne.columns and not ligne["0220"].empty else 0

            if pd.notna(exposition) and exposition != 0:

                ratio = rwa / exposition

                ratios_data.append({

                    "Type d'exposition": label,

                    "Exposition": format_large_number(exposition),

                    "RWA": format_large_number(rwa),

                    "Ratio RWA/Exposition": f"{ratio:.4f} ({ratio*100:.2f}%)"

                })


    if ratios_data:

        st.dataframe(pd.DataFrame(ratios_data), use_container_width=True)



def afficher_corep_detaille(df_bloc):
    """
    Affiche un DataFrame de COREP (C02.00) avec descriptions claires et formatage amélioré.
    Corrige les intitulés, inclut 0200, et respecte le flux logique d'exposition vers RWA.
    """
    df_affichage = df_bloc.copy()

    # === Mapping conforme au flux réglementaire COREP ===
    mapping_colonnes = {
        "0010": "Exposition initiale",
        "0110": "Valeur ajustée du collatéral (Cvam)",
        "0150": "Valeur ajustée de l'exposition (E*)",  # Fully adjusted exposure value
        "0200": "Exposition après CRM",                 # Exposure value
        "0215": "Montant pondéré brut (avant facteur soutien PME)",
        "0220": "Montant pondéré net après ajustements"
    }
    df_affichage.rename(columns={k: v for k, v in mapping_colonnes.items() if k in df_affichage.columns}, inplace=True)

    # === Colonnes à afficher selon le flux logique ===
    colonnes_flux = ["row"] + list(mapping_colonnes.values())
    colonnes_disponibles = [col for col in colonnes_flux if col in df_affichage.columns]
    df_affichage = df_affichage[colonnes_disponibles].copy()

    # === Mapping des lignes COREP ===
    def get_description(row_val):
        mapping = {
            70.0: "Expositions On-Balance Sheet",
            80.0: "Expositions Off-Balance Sheet",
            90.0: "Expositions sur dérivés (long settlement)",
            100.0: "Expositions CCR nettes (non cleared CCP)",
            110.0: "Expositions Derivatives",
            130.0: "Total Expositions",
            140.0: "Total RWA"
        }
        if pd.isna(row_val):
            return None
        return mapping.get(row_val, f"Ligne {int(row_val)}" if isinstance(row_val, float) else str(row_val))

    df_affichage["Description"] = df_affichage["row"].map(get_description)
    df_affichage = df_affichage[df_affichage["Description"].notna()]  # Supprime les lignes inutiles

    # === Réorganisation des colonnes ===
    colonnes_finales = ["Description"] + [col for col in df_affichage.columns if col not in ["Description", "row"]]
    df_affichage = df_affichage[colonnes_finales]

    # === Formatage des valeurs numériques ===
    for col in df_affichage.columns[1:]:
        df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.2f}".replace(","," ").replace(".",".") if pd.notna(x) else "")

    # === Surlignage rose de la ligne stressée (70.0) ===
    def highlight_on_balance(row):
        if row.get("Description") == "Expositions On-Balance Sheet":
            return ['background-color: #ffeeee'] * len(row)
        return [''] * len(row)

    st.dataframe(df_affichage.style.apply(highlight_on_balance, axis=1), use_container_width=True)
    st.caption("*La ligne surlignée en rose (On-Balance Sheet) est celle modifiée par le stress test.*")

    # === Affichage des ratios RWA/Exposition ===
    afficher_ratios_rwa(df_bloc)