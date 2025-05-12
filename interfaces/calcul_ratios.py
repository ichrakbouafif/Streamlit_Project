import streamlit as st
import pandas as pd

###importation des modules nécessaires pour le bilan
from backend.ratios_baseline.ratios_baseline import charger_bilan
from backend.ratios_baseline.capital_projete import noms_lignes_c0100  # Assure-toi que le mapping est importé
from backend.ratios_baseline.capital_projete import noms_lignes_c4700  # Assure-toi que le mapping est importé

###importation des modules nécessaires pour le LCR
from backend.lcr.utils import affiche_LB_lcr
from backend.lcr.utils import affiche_outflow_lcr
from backend.lcr.utils import affiche_inflow_lcr

###importation des modules nécessaires pour le NSFR
from backend.nsfr.utils import affiche_RSF
from backend.nsfr.utils import affiche_ASF

from backend.ratios_baseline.ratios_baseline import get_capital_planning
from backend.ratios_baseline.ratios_baseline import get_mapping_df_row
from backend.ratios_baseline.ratios_baseline import add_capital_planning_df

from backend.stress_test import event1 as bst
from backend.ratios_baseline.ratios_baseline import calcul_ratios_sur_horizon
#capital projete import
from backend.ratios_baseline.capital_projete import (
    charger_donnees,
    simuler_solvabilite_pluriannuelle,
    simuler_levier_pluriannuel,
    charger_c4700,
    format_large_number
)

def format_large_number(num):
    """Format number with space as thousands separator and 2 decimal digits"""
    if pd.isna(num) or num == 0:
        return "0"
    return f"{num:,.2f}".replace(",", " ").replace(".", ",")

def format_number_espace(n):
    return f"{n:,.2f}".replace(",", " ").replace(".", ",")

def affiche_bilan(bilan: pd.DataFrame):
    bilan_affichage = bilan.copy()

    # Remplacer les postes vides avec valeur 2024 NaN → Capital Planning
    bilan_affichage["Poste du Bilan"] = bilan_affichage["Poste du Bilan"].fillna("").astype(str)
    bilan_affichage["Type"] = bilan_affichage.apply(
        lambda row: "Capital Planning" if (row["Poste du Bilan"].strip() == "" and pd.isna(row["2024"])) else "",
        axis=1
    )
    bilan_affichage["Poste du Bilan"] = bilan_affichage.apply(
        lambda row: "Capital Planning" if row["Type"] == "Capital Planning" else row["Poste du Bilan"],
        axis=1
    )

    # Formatage des montants
    for year in ["2024", "2025", "2026", "2027"]:
        bilan_affichage[year] = pd.to_numeric(bilan_affichage[year], errors="coerce")
        bilan_affichage[year] = bilan_affichage[year].apply(
            #lambda x: "{:,.2f}".format(x).replace(",", " ").replace(".", ",") if pd.notnull(x) else ""
            lambda x: "{:,.2f}".format(x) if pd.notnull(x) else ""
        )

    # Fonction de surlignage conditionnel
    def highlight_rows(row):
        if row["Poste du Bilan"] == "Capital Planning":
            return ["background-color: #ffe6f0"] * len(row)
        return [""] * len(row)

    styled_df = bilan_affichage.drop(columns=["Type"]).style.apply(highlight_rows, axis=1)

    st.subheader("Bilan de Référence")
    st.dataframe(styled_df, use_container_width=True)

def show():
    st.title("Calcul des Ratios Baseline")

    # ====================== BILAN DE RÉFÉRENCE ======================
    bilan = charger_bilan()
    affiche_bilan(bilan)

    # ====================== HORIZON DE STRESS TEST ======================
    st.subheader("Horizon de Stress Test")
    horizon = st.number_input("Durée de l'horizon de stress test (en années)", min_value=1, max_value=10, value=3)
    
    # Load data upfront
    df_72, df_73, df_74 = bst.charger_lcr()
    df_80, df_81 = bst.charger_nsfr()
    
    # Calculate ratios for all years in horizon immediately
    resultats_horizon = calcul_ratios_sur_horizon(horizon, bilan, df_72, df_73, df_74, df_80, df_81)

    if 'show_ratios' not in st.session_state:
        st.session_state.show_ratios = True

    # ====================== RATIOS DISPLAY SECTION ======================
    if st.session_state.show_ratios:
        st.subheader("Ratios Réglementaires")
        
        # ====================== LCR RATIO ======================
        st.markdown("##### Ratio LCR")
        with st.expander("Ratio LCR", expanded=False):
            st.write("**Définition:** Le ratio de liquidité à court terme mesure la capacité de la banque à faire face à ses sorties de trésorerie à 30 jours.")
            st.latex(r"LCR = \frac{\text{Actifs liquides de haute qualité}}{\text{Sorties nettes de trésorerie sur 30 jours}}")
            st.write("**Composantes:**")
            st.write("- Actifs liquides de haute qualité (par exemple : bons du Trésor, obligations d'État)")
            st.write("- Sorties nettes de trésorerie sur 30 jours (composées de remboursements de prêts, de retraits de dépôts, etc.)")
            st.write("**Interprétation:** Un LCR supérieur à 100 % signifie que la banque dispose d'une réserve suffisante d'actifs liquides pour faire face à ses obligations à court terme.")
        
        # Créer un tableau pour LCR avec les colonnes Année, HQLA, Inflow, Outflow, LCR%
        lcr_years = []
        for year in range(2024, 2024+horizon+1):
            if year in resultats_horizon:
                lcr_years.append({
                    "Année": year,
                    "HQLA": f"{resultats_horizon[year]['HQLA']:,.2f}".replace(",", " "),
                    "Inflow":f"{resultats_horizon[year]['INFLOWS']:,.2f}".replace(",", " "),
                    "Outflow": f"{resultats_horizon[year]['OUTFLOWS']:,.2f}".replace(",", " "),
                    #"Net Outflow": format_large_number(resultats_horizon[year]['OUTFLOWS'] - resultats_horizon[year]['INFLOWS']),
                    "LCR%": f"{resultats_horizon[year]['LCR']*100:,.2f}%"
                })
        
        lcr_table = pd.DataFrame(lcr_years)
        st.table(lcr_table)
        
                # LCR details expander for each year
        st.markdown("#####  Détail du calcul du ratio LCR")

        pwc_orange = "#f47721"
        pwc_dark_gray = "#3d3d3d"
        pwc_light_beige = "#f5f0e6"
        pwc_brown = "#6e4c1e"
        pwc_soft_black = "#2c2c2c"

        for year in range(2024, 2024+horizon+1):
            if year in resultats_horizon:
                with st.expander(f"Détails de calcul LCR pour {year}"):
                    st.markdown(f"#### Année {year}")
                    
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">LCR</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                                    {resultats_horizon[year]['LCR']*100:.2f}%
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">HQLA</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_horizon[year]['HQLA'])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Outflows</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_horizon[year]['OUTFLOWS'])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col4:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Inflows</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_horizon[year]['INFLOWS'])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # DÉTAIL DU CALCUL LCR : FEUILLE 72 - Utiliser les dataframes spécifiques à l'année
                    st.markdown("**Actifs liquides de haute qualité (HQLA)**")
                    try:
                        # Utilisez le df_72 spécifique à l'année
                        df_72_year = resultats_horizon[year]['df_72']
                        lignes_non_vides = affiche_LB_lcr(df_72_year)
                        if not lignes_non_vides.empty:
                            st.dataframe(lignes_non_vides, use_container_width=True)
                        else:
                            st.info("Aucune ligne non vide trouvée pour HQLA.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'extraction des données HQLA : {e}")

                    # DÉTAIL DU CALCUL LCR : FEUILLE 73 - Utiliser les dataframes spécifiques à l'année
                    st.markdown("**Sorties de liquidités (Outflows)**")
                    try:
                        # Utilisez le df_73 spécifique à l'année
                        df_73_year = resultats_horizon[year]['df_73']
                        lignes_non_vides = affiche_outflow_lcr(df_73_year)  
                        if not lignes_non_vides.empty:
                            st.dataframe(lignes_non_vides, use_container_width=True)  
                        else:
                            st.info("Aucune ligne non vide trouvée pour Outflows.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'extraction des données Outflows : {e}")

                    # DÉTAIL DU CALCUL LCR : FEUILLE 74 - Utiliser les dataframes spécifiques à l'année
                    st.markdown("**Entrées de liquidités (Inflows)**")
                    try: 
                        # Utilisez le df_74 spécifique à l'année
                        df_74_year = resultats_horizon[year]['df_74']
                        lignes_non_vides = affiche_inflow_lcr(df_74_year)  
                        if not lignes_non_vides.empty:
                            st.dataframe(lignes_non_vides, use_container_width=True)  
                        else:
                            st.info("Aucune ligne non vide trouvée pour Inflows.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'extraction des données Inflows : {e}")

        # ====================== NSFR RATIO ======================
        st.markdown("##### Ratio NSFR")
        with st.expander("Ratio NSFR", expanded=False):
            st.write("**Définition:** Le ratio de financement stable à long terme évalue si les ressources stables de la banque couvrent ses besoins stables à long terme.")
            st.latex(r"NSFR = \frac{\text{Financements stables disponibles}}{\text{Besoins en financements stables}}")
            st.write("**Composantes:**")
            st.write("- Financements stables disponibles (par exemple : dépôts à long terme, fonds propres)")
            st.write("- Besoins en financements stables (corresponds aux besoins de la banque pour financer ses actifs à long terme)")
            st.write("**Interprétation:** Un NSFR supérieur à 100 % indique que la banque dispose de ressources financières stables suffisantes pour soutenir ses activités à long terme.")
        
        # Créer un tableau pour NSFR avec les colonnes Année, ASF, RSF, NSFR%
        nsfr_years = []
        for year in range(2024, 2024+horizon+1):
            if year in resultats_horizon:
                nsfr_years.append({
                    "Année": year,
                    "ASF": f"{resultats_horizon[year]['ASF']:,.2f}".replace(",", " "),
                    "RSF": f"{resultats_horizon[year]['RSF']:,.2f}".replace(",", " "),
                    "NSFR%": f"{resultats_horizon[year]['NSFR']:,.2f}%"
                })
        
        nsfr_table = pd.DataFrame(nsfr_years)
        st.table(nsfr_table)
        
        # NSFR details expander for each year
        st.markdown("##### Détail du calcul du ratio NSFR")
        
        # Pour chaque année, créer un expander avec les détails
        for year in range(2024, 2024+horizon+1):
            if year in resultats_horizon:
                with st.expander(f"Détails de calcul NSFR pour {year}"):
                    st.markdown(f"##### Année {year}")
                    
                    # Afficher métriques principales
                    pwc_orange = "#f47721"
                    pwc_dark_gray = "#3d3d3d"
                    pwc_light_beige = "#f5f0e6"
                    pwc_brown = "#6e4c1e"
                    pwc_soft_black = "#2c2c2c"

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">NSFR</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                                    {resultats_horizon[year]['NSFR']:.2f}%
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">ASF</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_horizon[year]['ASF'])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">RSF</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_horizon[year]['RSF'])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    # DÉTAIL DU CALCUL NSFR : FEUILLE 81 (ASF) - Utiliser les dataframes spécifiques à l'année
                    st.markdown("**Available Stable Funding (ASF)**")
                    try:
                        # Utilisez le df_81 spécifique à l'année
                        df_81_year = resultats_horizon[year]['df_81']
                        lignes_non_vides = affiche_ASF(df_81_year)
                        if not lignes_non_vides.empty:
                            st.dataframe(lignes_non_vides, use_container_width=True)
                        else:
                            st.info("Aucune ligne non vide trouvée pour ASF.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'extraction des données ASF : {e}")

                    # DÉTAIL DU CALCUL NSFR : FEUILLE 80 (RSF) - Utiliser les dataframes spécifiques à l'année
                    st.markdown("**Required Stable Funding (RSF)**")
                    try:
                        # Utilisez le df_80 spécifique à l'année
                        df_80_year = resultats_horizon[year]['df_80']
                        lignes_non_vides = affiche_RSF(df_80_year)
                        if not lignes_non_vides.empty:
                            st.dataframe(lignes_non_vides, use_container_width=True)
                        else:
                            st.info("Aucune ligne non vide trouvée pour RSF.")
                    except Exception as e:
                        st.error(f"Erreur lors de l'extraction des données RSF : {e}")

        # ====================== LEVIER RATIO (Placeholder) ======================
        # Chargement des données
        bilan, df_c01, df_c02, blocs_c0700 = charger_donnees()
        df_c4700 = charger_c4700()

        if bilan is None or df_c01.empty or df_c02.empty or df_c4700.empty:
            st.error("❌ Données manquantes. Veuillez vérifier vos fichiers COREP.")
            return

        annees = [str(2024 + i) for i in range(horizon + 1)]

        # Simulations
        resultats_solva = simuler_solvabilite_pluriannuelle(bilan, df_c01, df_c02, blocs_c0700, annees=annees[1:])
        resultats_levier = simuler_levier_pluriannuel(bilan, df_c01, df_c4700, annees=annees[1:])

        # === AFFICHAGE SOLVABILITÉ ===
        st.markdown("##### Ratio Solvabilité")
        with st.expander("Ratio Solvabilité", expanded=False):
            st.write("**Définition:** Le ratio de solvabilité mesure la capacité d'une banque à absorber les pertes par rapport à ses actifs pondérés par le risque.")
            st.latex(r"Solvabilité = \frac{\text{Fonds propres réglementaires}}{\text{Risques pondérés}}")
            st.write("**Composantes:**")
            st.write("- Fonds propres réglementaires (capital de base et réserves)")
            st.write("- Risques pondérés (actifs ajustés en fonction de leur risque, comme les prêts à faible ou à haut risque)")
            st.write("**Interprétation:** Un ratio de solvabilité >=8% montre que la banque a suffisamment de capital pour couvrir ses risques.")
        tableau_solva = []

        tableau_solva = []
        for annee in annees:
            if annee in resultats_solva:
                tableau_solva.append({
                    "Année": annee,
                    "Fonds Propres": format_number_espace(resultats_solva[annee]["fonds_propres"]),
                    "RWA": format_number_espace(resultats_solva[annee]["rwa"]),
                    "Solvabilité": f"{resultats_solva[annee]['ratio']:.2f}%"
                })

        st.dataframe(pd.DataFrame(tableau_solva), use_container_width=True)


        for annee in annees:
            if annee in resultats_solva:
                with st.expander(f" Détails Solvabilité - {annee}", expanded=False):
                    pwc_orange = "#f47721"
                    pwc_dark_gray = "#3d3d3d"
                    pwc_light_beige = "#f5f0e6"
                    pwc_brown = "#6e4c1e"
                    pwc_soft_black = "#2c2c2c"

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio Solvabilité</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                                    {resultats_solva[annee]['ratio']:.2f}%
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Fonds Propres</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_solva[annee]["fonds_propres"])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px; 
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">RWA</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_solva[annee]["rwa"])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    st.markdown("**Fonds propres (C0100)**")
                    df_complet_c01 = resultats_solva[annee]["df_c01"]
                    if not df_complet_c01.empty:
                            df_c01_affiche = df_complet_c01.copy()
                            df_c01_affiche = df_c01_affiche[df_c01_affiche["row"] != 10]

                    if "row" in df_c01_affiche.columns:
                                df_c01_affiche["Rubrique"] = df_c01_affiche["row"].apply(lambda x: noms_lignes_c0100.get(int(x), f"Ligne {x}"))
                                df_c01_affiche = df_c01_affiche[["Rubrique", "0010"]]  # Garde uniquement la colonne utile
                                df_c01_affiche = df_c01_affiche.rename(columns={"0010": "Montant (EUR)"})
                                  # Formatage des montants
                                df_c01_affiche["Montant (EUR)"] = df_c01_affiche["Montant (EUR)"].apply(format_number_espace)
                                st.dataframe(df_c01_affiche, use_container_width=True)
                                
                    else:
                                st.warning("❗ Colonne 'row' manquante dans le dataframe C0100.")
                    if "blocs_rwa" in resultats_solva[annee]:
                        for nom_bloc, df_bloc in resultats_solva[annee]["blocs_rwa"].items():
                            st.markdown(f"**Bloc RWA - {nom_bloc} (C0700)**")
                              # Formatage des montants
                               # Appliquer le format sur toutes les colonnes numériques
                            df_formate = df_bloc.copy()
                            for col in df_formate.select_dtypes(include=["float", "int"]).columns:
                                df_formate[col] = df_formate[col].apply(format_number_espace)
                            st.dataframe(df_formate, use_container_width=True)
        # === AFFICHAGE LEVIER ===
        st.markdown("#####  Ratio Levier")
        with st.expander("Ratio Levier", expanded=False):
            st.write("**Définition:** Le ratio de levier mesure le niveau d'endettement de la banque en comparant ses fonds propres au total de ses expositions.")
            st.latex(r"Levier = \frac{\text{Fonds propres de base}}{\text{Total des expositions}}")
            st.write("**Composantes:**")
            st.write("- Fonds propres de base (par exemple : capital social, réserves consolidées)")
            st.write("- Total des expositions (y compris les prêts, titres, dérivés, engagements)")
            st.write("**Interprétation:** Un ratio de levier>=3%  indique une banque plus robuste, avec une plus grande capacité à absorber les pertes.")
        tableau_levier = []
        for annee in annees:
            if annee in resultats_levier:
                tableau_levier.append({
                    "Année": annee,
                    "Tier 1": format_number_espace(resultats_levier[annee]["tier1"]),
                    "Exposition Totale": format_number_espace(resultats_levier[annee]["total_exposure"]),
                    "Levier": f"{resultats_levier[annee]['ratio']:.2f}%"
                })
          # Formatage des montants
      
        st.dataframe(pd.DataFrame(tableau_levier), use_container_width=True)

        for annee in annees:
            if annee in resultats_levier:
                with st.expander(f" Détails Levier - {annee}", expanded=False):
                    pwc_orange = "#f47721"
                    pwc_dark_gray = "#3d3d3d"
                    pwc_light_beige = "#f5f0e6"
                    pwc_brown = "#6e4c1e"
                    pwc_soft_black = "#2c2c2c"

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio Levier</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                                    {resultats_levier[annee]['ratio']:.2f}%
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col2:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Tier 1</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_levier[annee]["tier1"])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            f"""
                            <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                                <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Exposition Totale</h4>
                                <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                    {format_large_number(resultats_levier[annee]["total_exposure"])}
                                </p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                                                                    # Affichage explicite du tableau C4700 avec noms de lignes
                                                # === AFFICHAGE TIER 1 (C0100) ===
                    st.markdown("**Tier 1 (extrait C0100)**")
                    df_c01_complet = resultats_levier[annee]["df_c01"].copy()
                    df_c01_complet = df_c01_complet[df_c01_complet["row"] != 10]  # supprimer ligne globale inutilisée

                        # Ajout des noms explicites des lignes via mapping
                    df_c01_complet["Rubrique"] = df_c01_complet["row"].astype(int).map(noms_lignes_c0100)
                    df_c01_complet["Montant (EUR)"] = df_c01_complet["0010"]

                        # Lignes liées au TIER 1 (CET1 + AT1)
                    lignes_tier1 = [
                            15, 20, 30, 40, 45, 50, 60, 70, 80, 90, 91, 92,
                            130, 140, 150, 160, 170, 180, 200, 210, 220, 230,
                            240, 250, 260, 270, 280, 285, 290, 300, 310, 320,
                            330, 335, 340, 350, 360, 365, 370, 380, 390, 400,
                            410, 420, 430, 440, 450, 460, 470, 471, 472, 480,
                            490, 500, 510, 511, 512, 513, 514, 515, 520, 524, 529,
                            530, 540, 551, 571, 580, 590, 620, 621, 622, 660, 670,
                            680, 690, 700, 710, 720, 730, 740, 744, 748
                        ]

                    df_c01_tier1 = df_c01_complet[df_c01_complet["row"].isin(lignes_tier1)].sort_values("row")
                    df_c01_tier1["Montant (EUR)"] = df_c01_tier1["Montant (EUR)"].apply(format_number_espace)
                    st.dataframe(df_c01_tier1[["Rubrique", "Montant (EUR)"]], use_container_width=True)


                        # === AFFICHAGE C4700 ===
                    st.markdown("**Exposition Totale (C4700)**")
                    df_c47 = resultats_levier[annee]["df_c4700"].copy()
                    df_c47 = df_c47[df_c47["0010"].notna()]  # retirer les lignes vides

                        # Ajout des noms explicites
                    df_c47["Rubrique"] = df_c47["Row"].astype(int).map(noms_lignes_c4700)
                    df_c47["Montant (EUR)"] = df_c47["0010"]

                        # Tri réglementaire
                    df_c47_affiche = df_c47.sort_values("Row")[["Rubrique", "Montant (EUR)"]]
                    df_c47_affiche["Montant (EUR)"] = df_c47_affiche["Montant (EUR)"].apply(format_number_espace)
                    st.dataframe(df_c47_affiche, use_container_width=True)


        # ====================== SOLVABILITÉ RATIO (Placeholder) ======================

        
        # ====================== RÉSUMÉ DES RÉSULTATS ======================
        st.subheader("Résumé des Résultats")
        result_data = []

        # LCR and NSFR with real calculated values
        lcr_baseline = resultats_horizon[2024]['LCR'] * 100
        nsfr_baseline = resultats_horizon[2024]['NSFR']

        result_data.append({
            "Ratio": "LCR",
            "Valeur Baseline (2024)": f"{lcr_baseline:.2f}%",
            **{f"Valeur Baseline Projeté Année {2024+i+1}": f"{resultats_horizon[2024+i+1]['LCR']*100:.2f}%" 
            for i in range(horizon) if 2024+i+1 in resultats_horizon},
            "Conformité": "Conforme" if lcr_baseline >= 100 else "Non conforme"
        })

        result_data.append({
            "Ratio": "NSFR",
            "Valeur Baseline (2024)": f"{nsfr_baseline:.2f}%",
            **{f"Valeur Baseline Projeté Année {2024+i+1}": f"{resultats_horizon[2024+i+1]['NSFR']:.2f}%" 
            for i in range(horizon) if 2024+i+1 in resultats_horizon},
            "Conformité": "Conforme" if nsfr_baseline >= 100 else "Non conforme"
        })

        # Use real calculated values for Levier and Solvabilité
        # Get the levier baseline value for 2024
        levier_baseline = resultats_levier["2024"]["ratio"] if "2024" in resultats_levier else 0
        result_data.append({
            "Ratio": "Levier",
            "Valeur Baseline (2024)": f"{levier_baseline:.2f}%",
            **{f"Valeur Baseline Projeté Année {2024+i+1}": f"{resultats_levier.get(str(2024+i+1), {}).get('ratio', 0):.2f}%" 
            for i in range(horizon) if str(2024+i+1) in resultats_levier},
            "Conformité": "Conforme" if levier_baseline >= 3 else "Non conforme"  # 3% is typical minimum requirement
        })

        # Get the solvabilité baseline value for 2024
        solva_baseline = resultats_solva["2024"]["ratio"] if "2024" in resultats_solva else 0
        result_data.append({
            "Ratio": "Solvabilité",
            "Valeur Baseline (2024)": f"{solva_baseline:.2f}%",
            **{f"Valeur Baseline Projeté Année {2024+i+1}": f"{resultats_solva.get(str(2024+i+1), {}).get('ratio', 0):.2f}%" 
            for i in range(horizon) if str(2024+i+1) in resultats_solva},
            "Conformité": "Conforme" if solva_baseline >= 8 else "Non conforme"  # 8% is typical minimum requirement
        })

        result_df = pd.DataFrame(result_data)

        # Fonction pour appliquer la couleur à la colonne conformité
        def apply_color(val):
            color = 'background-color:#175C2C; color: white;' if val == "Conforme" else 'background-color: #E0301E; color: white;'
            return color

        # Appliquer la couleur et convertir en HTML
        styled_df = result_df.style.applymap(apply_color, subset=["Conformité"])

        # Utiliser st.markdown pour afficher la table avec le format HTML
        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    if st.button("Procéder aux choix du scénario"):
        st.session_state.selected_page = "Choix du Scénario"
        st.rerun()
