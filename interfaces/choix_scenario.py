import streamlit as st
import config
import traceback
import os
import pandas as pd
from backend.stress_test import event1 as bst
from backend.stress_test import event2 as bst2
from config import format_large_number
from backend.solvabilite.calcul_ratios_capital_stressé import executer_stress_event1_bloc_institutionnel_pluriannuel
from backend.lcr.utils import affiche_LB_lcr, affiche_outflow_lcr, affiche_inflow_lcr
from backend.lcr.feuille_72 import calcul_HQLA
from backend.lcr.feuille_73 import calcul_outflow
from backend.lcr.feuille_74 import calcul_inflow
from backend.lcr.utils import Calcul_LCR
from backend.nsfr.utils import Calcul_NSFR, affiche_RSF, affiche_ASF
from backend.nsfr.feuille_80 import calcul_RSF
from backend.nsfr.feuille_81 import calcul_ASF
# Import additional modules for leverage and solvency
from backend.levier.calcul_ratio_levier import executer_stress_event1_levier_pluriannuel

from backend.stress_test.capital import executer_stress_pnu_capital_pluriannuel

""" def show():
    st.title("Choix des scénarios")

    if "scenario_type" not in st.session_state:
        st.session_state.scenario_type = None
    if "selected_events" not in st.session_state:
        st.session_state.selected_events = []

    st.subheader("Phase 1 : Sélection du premier scénario")

    scenario_type = st.radio(
        "Type de scénario à calibrer",
        ["Scénario idiosyncratique", "Scénario macroéconomique"],
        key="scenario_type_radio"
    )

    scenario_type_key = "idiosyncratique" if "idiosyncratique" in scenario_type else "macroéconomique"
    st.session_state.scenario_type = scenario_type_key

    available_events = list(config.scenarios[scenario_type_key].keys())

    selected_events = st.multiselect(
        "Événements disponibles",
        available_events,
        key="events_multiselect"
    )

    st.session_state.selected_events = selected_events

    if selected_events:
        afficher_configuration_evenements(selected_events, scenario_type_key) """

def show():
    st.title("Choix des scénarios")

    # Initialize session state variables for navigation
    if "current_phase" not in st.session_state:
        st.session_state.current_phase = 1
    if "scenario_type" not in st.session_state:
        st.session_state.scenario_type = None
    if "selected_events_phase1" not in st.session_state:
        st.session_state.selected_events_phase1 = []
    if "selected_events_phase2" not in st.session_state:
        st.session_state.selected_events_phase2 = []
    if "all_selected_events" not in st.session_state:
        st.session_state.all_selected_events = []

    # Phase 1: Select scenario type (macroeconomic or idiosyncratic)
    if st.session_state.current_phase == 1:
        show_phase1()
    
    # Phase 2: Select events from the other scenario type
    elif st.session_state.current_phase == 2:
        show_phase2()
    
    # Phase 3: Show all selected events and results
    elif st.session_state.current_phase == 3:
        show_phase3()

def show_phase1():
    st.subheader("Phase 1 : Sélection du type de scénario principal")

    scenario_type = st.radio(
        "Type de scénario à calibrer",
        ["Scénario idiosyncratique", "Scénario macroéconomique"],
        key="scenario_type_radio"
    )

    scenario_type_key = "idiosyncratique" if "idiosyncratique" in scenario_type else "macroéconomique"
    st.session_state.scenario_type = scenario_type_key

    available_events = list(config.scenarios[scenario_type_key].keys())

    selected_events = st.multiselect(
        "Événements disponibles",
        available_events,
        key="events_multiselect_phase1"
    )

    st.session_state.selected_events_phase1 = selected_events

    if selected_events:
        afficher_configuration_evenements(selected_events, scenario_type_key)

    if st.button("Valider la phase 1 et passer à la phase 2"):
        if not selected_events:
            st.warning("Veuillez sélectionner au moins un événement avant de continuer.")
        else:
            st.session_state.current_phase = 2
            st.rerun()

def show_phase2():
    st.subheader("Phase 2 : Sélection des événements complémentaires")
    
    # Determine the other scenario type (the one not selected in phase 1)
    other_scenario_type = "macroéconomique" if st.session_state.scenario_type == "idiosyncratique" else "idiosyncratique"
    
    available_events = list(config.scenarios[other_scenario_type].keys())
    
    selected_events = st.multiselect(
        "Événements disponibles",
        available_events,
        key="events_multiselect_phase2"
    )
    
    st.session_state.selected_events_phase2 = selected_events
    
    if selected_events:
        afficher_configuration_evenements(selected_events, other_scenario_type)
    

    if st.button("Valider la phase 2 et passer à la phase 3"):
        # Combine all selected events from both phases
        st.session_state.all_selected_events = (
            st.session_state.selected_events_phase1 + 
            st.session_state.selected_events_phase2
        )
        st.session_state.current_phase = 3
        st.rerun()

def show_phase3():
    st.subheader("Phase 3 : Synthèse des événements sélectionnés")
    
    # Display selected events from phase 1
    st.markdown("**Événements sélectionnés en phase 1:**")
    for event in st.session_state.selected_events_phase1:
        st.write(f"- {event}")
    
    # Display selected events from phase 2
    st.markdown("**Événements sélectionnés en phase 2:**")
    for event in st.session_state.selected_events_phase2:
        st.write(f"- {event}")
    
    # Show configuration for all events
    st.subheader("Configuration des événements")
    
    # First show phase 1 events
    if st.session_state.selected_events_phase1:
        st.markdown(f"**Configuration pour le scénario {st.session_state.scenario_type}:**")
        afficher_configuration_evenements(st.session_state.selected_events_phase1, st.session_state.scenario_type)
    
    # Then show phase 2 events
    if st.session_state.selected_events_phase2:
        other_scenario_type = "macroéconomique" if st.session_state.scenario_type == "idiosyncratique" else "idiosyncratique"
        st.markdown(f"**Configuration pour le scénario {other_scenario_type}:**")
        afficher_configuration_evenements(st.session_state.selected_events_phase2, other_scenario_type)
    

    if st.button("Valider tous les scénarios et voir les résultats"):
        st.session_state.selected_page = "Résultats & Graphiques"
        st.rerun()

def afficher_configuration_evenements(selected_events, scenario_type):
    #initialize bilan in session state
    if 'bilan' not in st.session_state:
        st.session_state.bilan = bst.charger_bilan()
    if 'bilan_original' not in st.session_state:
        st.session_state.bilan_original = bst.charger_bilan()

    events_dict = config.scenarios[scenario_type]

    for event in selected_events:
        st.markdown(f"### Configuration pour: {event}")

        if event == "Retrait massif des dépôts":
            executer_retrait_depots()
        elif event == "Tirage PNU":
            executer_tirage_pnu()
        else:
            st.warning("Cette fonctionnalité n'est pas encore implémentée.")

def afficher_parametres_retrait_depots():

    # Initialisation des états
    if "poids_portefeuille" not in st.session_state:
        st.session_state.poids_portefeuille = 15
    if "poids_creances" not in st.session_state:
        st.session_state.poids_creances = 85
    if "last_changed" not in st.session_state:
        st.session_state.last_changed = "portefeuille"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### <span style='font-size:18px;'>Paramètres du retrait massif des dépôts</span>", unsafe_allow_html=True)
        pourcentage = st.slider("Diminution des dépôts (%)", 0, 100, 15, 5) / 100.0
        horizon = st.slider("Horizon du choc (années)", 1, 10, 1, 1)
        horizon_global = st.session_state.get("horizon_global", 3)
        if horizon > horizon_global:
            st.error(f"L'horizon de l'événement ne peut pas dépasser l'horizon global du stress test ({horizon_global} ans). Veuillez choisir une valeur inférieure ou égale.")


    with col2:
        st.markdown("#### <span style='font-size:18px;'>Répartition de l’impact</span>", unsafe_allow_html=True)

        def on_change_portefeuille():
            st.session_state.last_changed = "portefeuille"
            st.session_state.poids_creances = 100 - st.session_state.poids_portefeuille

        def on_change_creances():
            st.session_state.last_changed = "creances"
            st.session_state.poids_portefeuille = 100 - st.session_state.poids_creances

        st.slider(
            "Portefeuille (%)",
            0, 100,
            key="poids_portefeuille",
            step=5,
            on_change=on_change_portefeuille
        )

        st.slider(
            "Créances bancaires (%)",
            0, 100,
            key="poids_creances",
            step=5,
            on_change=on_change_creances
        )

    # Conversion en décimales
    poids_portefeuille = st.session_state.poids_portefeuille / 100.0
    poids_creances = st.session_state.poids_creances / 100.0

    return {
        'pourcentage': pourcentage,
        'horizon': horizon,
        'poids_portefeuille': poids_portefeuille,
        'poids_creances': poids_creances
    }

def executer_retrait_depots():
    # Use the bilan from session state
    bilan = st.session_state.bilan
    params = afficher_parametres_retrait_depots()

    if st.button("Exécuter le stress test", key="executer_stress_test", use_container_width=True):
        with st.spinner("Exécution du stress test en cours..."):
            try:
                # Store original in session state
                #st.session_state.bilan_original = bilan.copy()
               
                # Apply stress
                bilan_stresse = bst.appliquer_stress_retrait_depots(
                    bilan_df=bilan,
                    pourcentage=params['pourcentage'],
                    horizon=params['horizon'],
                    annee="2025",
                    poids_portefeuille=params['poids_portefeuille'],
                    poids_creances=params['poids_creances']
                )
               
                # Store stressed version
                st.session_state.bilan = bilan_stresse
                st.session_state.bilan_stresse = bilan_stresse
                st.success("Stress test exécuté avec succès!")
                afficher_resultats_retrait_depots(bilan_stresse, params)

                # Set the stress test executed flag
                st.session_state.stress_test_executed = True
               
               
                return params
               
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du stress test: {str(e)}")
                st.session_state.stress_test_executed = False
                return None

    return None

def afficher_resultats_retrait_depots(bilan_stresse, params):
    st.subheader("Impact sur le bilan")
    postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
    bilan_filtre = bst.afficher_postes_concernes(bilan_stresse, postes_concernes, horizon=params['horizon'])
    st.dataframe(bilan_filtre)

    if "resultats_horizon" not in st.session_state:
            st.session_state["resultats_horizon"] = {}
    # Section LCR
    st.subheader("Impact sur la liquidité (LCR)")
    bst.show_hqla_tab()
    bst.show_outflow_tab_retrait_depots()
    bst. show_inflow_tab_retrait_depots()
    recap_data_lcr = afficher_resultats_lcr_retrait_depots(bilan_stresse, params, horizon=params['horizon'])
    if recap_data_lcr:
        for year_data in recap_data_lcr:
            year = year_data["Année"]
            if year not in st.session_state["resultats_horizon"]:
                st.session_state["resultats_horizon"][year] = {}
            st.session_state["resultats_horizon"][year].update({
                "df_72": year_data["df_72"],
                "df_73": year_data["df_73"],
                "df_74": year_data["df_74"],
                "lcr_data": {
                    "HQLA": year_data["HQLA"],
                    "Inflows": year_data["Inflows"],
                    "Outflows": year_data["Outflows"],
                    "LCR (%)": year_data["LCR (%)"]
                }
            })
        afficher_tableau_recapitulatif(recap_data_lcr, "LCR")
   

    # Section NSFR
    st.subheader("Impact sur le ratio NSFR")
    bst.show_asf_tab_v2()
    bst.show_asf_tab_financial_customers()
    recap_data_nsfr= afficher_resultats_nsfr_retrait_depots(bilan_stresse, params, horizon=params['horizon'])
    if recap_data_nsfr:
        for year_data in recap_data_nsfr:
            year = year_data["Année"]
            if year not in st.session_state["resultats_horizon"]:
                st.session_state["resultats_horizon"][year] = {}
            st.session_state["resultats_horizon"][year].update({
                "df_80": year_data["df_80"],
                "df_81": year_data["df_81"],
                "nsfr_data": {
                    "ASF": year_data["ASF"],
                    "RSF": year_data["RSF"],
                    "NSFR (%)": year_data["NSFR (%)"]
                }
            })
        afficher_tableau_recapitulatif(recap_data_nsfr, "NSFR")

    # Section Ratio de Solvabilité
    st.subheader("Impact sur le ratio de solvabilité")
    if "resultats_solva" in st.session_state:
        resultats_proj = st.session_state["resultats_solva"]
    else:
        # Calculer les résultats projetés si non disponibles
        from backend.ratios_baseline.capital_projete import simuler_solvabilite_pluriannuelle
        resultats_proj = simuler_solvabilite_pluriannuelle()
        st.session_state["resultats_solva"] = resultats_proj
       
    afficher_resultats_solva(bilan_stresse, params, resultats_proj)    
    # Section Ratio de Levier
    st.subheader("Impact sur le ratio de levier")
   # Charger les résultats projetés pour le levier depuis la session ou les calculer
    if "resultats_levier" in st.session_state:
        proj_levier = st.session_state["resultats_levier"]
    else:
        from backend.ratios_baseline.capital_projete import simuler_levier_pluriannuel
        bilan_path = "data/bilan.xlsx"
        df_c01_path = "data/solvabilite.xlsx"
        df_c4700_path = "data/levier.xlsx"

        if not all([os.path.exists(p) for p in [bilan_path, df_c01_path, df_c4700_path]]):
            st.error("❌ Fichiers COREP ou bilan manquants pour le calcul du levier.")
            return

        bilan = pd.read_excel(bilan_path).iloc[2:].reset_index(drop=True)
        df_c01 = pd.read_excel(df_c01_path, sheet_name="C0100")
        df_c4700 = pd.read_excel(df_c4700_path, sheet_name="C4700")

        proj_levier = simuler_levier_pluriannuel(bilan, df_c01, df_c4700, annees=["2025", "2026", "2027"])
        st.session_state["resultats_levier"] = proj_levier

    # Affichage
    afficher_resultats_levier(params, proj_levier)
def afficher_resultats_lcr_retrait_depots(bilan_stresse, params, horizon=1):
    try:
        if 'resultats_horizon' not in st.session_state:
            st.error("Les résultats de base ne sont pas disponibles dans la session.")
            return None

        resultats_horizon = st.session_state['resultats_horizon']

        if 2024 not in resultats_horizon:
            st.error("Les données de l'année 2024 ne sont pas disponibles.")
            return None

        recap_data = []
        pourcentage = params["pourcentage"]
        poids_portefeuille = params["poids_portefeuille"]
        poids_creances = params["poids_creances"]

        # 2024 - base year without stress
        df_72 = resultats_horizon[2024]['df_72'].copy()
        df_73 = resultats_horizon[2024]['df_73'].copy()
        df_74 = resultats_horizon[2024]['df_74'].copy()

        recap_data.append({
            "Année": 2024,
            "HQLA": calcul_HQLA(df_72),
            "Inflows": calcul_inflow(df_74),
            "Outflows": calcul_outflow(df_73),
            "LCR (%)": Calcul_LCR(calcul_inflow(df_74), calcul_outflow(df_73), calcul_HQLA(df_72)) * 100,
            "df_72": df_72,
            "df_73": df_73,
            "df_74": df_74
        })

        for annee in [2025 + i for i in range(horizon)]:
            if annee not in resultats_horizon:
                st.error(f"Données de base pour {annee} manquantes dans session state")
                return None

            df_72 = resultats_horizon[annee]['df_72'].copy()
            df_73 = resultats_horizon[annee]['df_73'].copy()
            df_74 = resultats_horizon[annee]['df_74'].copy()

            # Stress cumulé des années précédentes
           
            for prev_year in range(2025, annee):
                df_72 = bst.propager_retrait_depots_vers_df72(
                    df_72, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon,
                    poids_portefeuille=poids_portefeuille
                )
                df_74 = bst.propager_retrait_depots_vers_df74(
                    df_74, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon,
                    poids_portefeuille=poids_portefeuille,
                    impact_creances=poids_creances
                )
                df_73 = bst.propager_retrait_depots_vers_df73(
                    df_73, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon,
                )

            # Stress de l'année courante
            df_72 = bst.propager_retrait_depots_vers_df72(
                df_72, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon,
                poids_portefeuille=poids_portefeuille
            )
            df_74 = bst.propager_retrait_depots_vers_df74(
                df_74, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon,
                poids_portefeuille=poids_portefeuille,
                impact_creances=poids_creances
            )
            df_73 = bst.propager_retrait_depots_vers_df73(
                df_73, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon,
            )

            recap_data.append({
                "Année": annee,
                "HQLA": calcul_HQLA(df_72),
                "Inflows": calcul_inflow(df_74),
                "Outflows": calcul_outflow(df_73),
                "LCR (%)": Calcul_LCR(calcul_inflow(df_74), calcul_outflow(df_73), calcul_HQLA(df_72)) * 100,
                "df_72": df_72,
                "df_73": df_73,
                "df_74": df_74
            })

        return recap_data

    except Exception as e:
        st.error(f"Erreur lors du calcul du LCR après retrait des dépôts : {str(e)}")
        return None

def afficher_resultats_nsfr_retrait_depots(bilan_stresse, params, horizon=3):
    try:
        if 'resultats_horizon' not in st.session_state:
            st.error("Les résultats de base ne sont pas disponibles dans la session.")
            return None

        resultats_horizon = st.session_state['resultats_horizon']

        if 2024 not in resultats_horizon:
            st.error("Les données de l'année 2024 ne sont pas disponibles.")
            return None

        recap_data_nsfr = []
        pourcentage = params["pourcentage"]
        poids_portefeuille = params["poids_portefeuille"]
        poids_creances = params["poids_creances"]

        # 2024 - scénario de référence
        df_80 = resultats_horizon[2024]['df_80'].copy()
        df_81 = resultats_horizon[2024]['df_81'].copy()

        recap_data_nsfr.append({
            "Année": 2024,
            "ASF": calcul_ASF(df_81),
            "RSF": calcul_RSF(df_80),
            "NSFR (%)": Calcul_NSFR(calcul_ASF(df_81),calcul_RSF(df_80)),
            "df_80": df_80,
            "df_81": df_81
        })

        for annee in [2025, 2026, 2027][:horizon]:
            if annee not in resultats_horizon:
                st.error(f"Données de base pour {annee} manquantes dans session state")
                return None

            df_80 = resultats_horizon[annee]['df_80'].copy()
            df_81 = resultats_horizon[annee]['df_81'].copy()

            # Application cumulative des stress des années précédentes
            for prev_year in range(2025, annee+1):
                df_80 = bst.propager_retrait_depots_vers_df80(
                    df_80, bilan_stresse, pourcentage_retrait=pourcentage,
                    poids_creances=poids_creances,
                    annee=prev_year
                )
                df_81 = bst.propager_retrait_depots_vers_df81(
                    df_81, bilan_stresse, pourcentage_retrait=pourcentage,
                    annee=prev_year
                )

            # Application du stress pour l’année courante
            df_80 = bst.propager_retrait_depots_vers_df80(
                df_80, bilan_stresse, pourcentage_retrait=pourcentage,
                poids_creances=poids_creances,
                annee=annee
            )
            df_81 = bst.propager_retrait_depots_vers_df81(
                df_81, bilan_stresse, pourcentage_retrait=pourcentage,
                annee=annee
            )

            recap_data_nsfr.append({
                "Année": annee,
                "ASF": calcul_ASF(df_81),
                "RSF": calcul_RSF(df_80),
                "NSFR (%)": Calcul_NSFR(calcul_ASF(df_81), calcul_RSF(df_80)),
                "df_80": df_80,
                "df_81": df_81
            })

        return recap_data_nsfr

    except Exception as e:
        st.error(f"Erreur lors du calcul du NSFR après retrait dépôts : {str(e)}")
        st.error(f"Stack trace: {traceback.format_exc()}")
    return None



from backend.solvabilite.calcul_ratios_capital_stressé import (
    executer_stress_event1_bloc_institutionnel_pluriannuel,
    recuperer_corep_bloc_institutionnel
)

def afficher_resultats_solva(bilan_stresse, params, resultats_proj):
    try:
        import os
        horizon = params.get("horizon", 3)
        pourcentage = params.get("pourcentage", 0.10)
        poids_creances = params.get("poids_creances", 0.50)

        dossier = "data"
        bilan_path = os.path.join(dossier, "bilan.xlsx")

        if not os.path.exists(bilan_path):
            st.error(f"Fichier de bilan non trouvé : {bilan_path}")
            return None

        bilan = pd.read_excel(bilan_path).iloc[2:].reset_index(drop=True)
        if "Unnamed: 1" in bilan.columns:
            bilan = bilan.drop(columns=["Unnamed: 1"])
        for i, col in enumerate(bilan.columns):
            if str(col).startswith("Unnamed: 6"):
                bilan = bilan.iloc[:, :i]
                break

        bilan.columns.values[:5] = ["Poste du Bilan", "2024", "2025", "2026", "2027"]
        bilan = bilan.dropna(how="all").reset_index(drop=True)
        if 25 in bilan.index:
            bilan = bilan.drop(index=25).reset_index(drop=True)

        ligne_creances = bilan[bilan["Poste du Bilan"].str.contains("Créances banques autres", case=False, na=False)]
        if ligne_creances.empty:
            st.warning("❌ La ligne 'Créances sur les banques – autres' est introuvable dans le bilan.")
            return None

        valeur_reference = ligne_creances["2024"].values[0]
        montant_stress_total = valeur_reference * pourcentage * poids_creances

        resultats_stress = executer_stress_event1_bloc_institutionnel_pluriannuel(
            resultats_proj=resultats_proj,
            annee_debut="2025",
            montant_stress_total=montant_stress_total,
            horizon=horizon,
            debug=False
        )

        # ✅ Stocker delta RWA pour retrait
        st.session_state["delta_rwa_event1"] = {
            annee: resultat["delta_rwa_total"]
            for annee, resultat in resultats_stress.items()
        }

        # ✅ Lire delta RWA de PNU s’il existe
        delta_pnu = st.session_state.get("delta_rwa_pnu", {})

        recap_data = []
        for i in range(horizon):
            annee = str(2025 + i)
            resultat = resultats_stress.get(annee)
            if not resultat:
                continue

            fonds_propres = resultats_proj[annee].get("fonds_propres", 0)
            rwa_retrait = resultat["rwa_total_stresse"]
            delta_rwa_pnu = delta_pnu.get(annee, 0)
            rwa_combine = rwa_retrait + delta_rwa_pnu

            ratio_retrait = (fonds_propres / rwa_retrait) * 100 if rwa_retrait > 0 else 0
            ratio_combine = (fonds_propres / rwa_combine) * 100 if rwa_combine > 0 else 0

            recap_data.append({
                "Année": annee,
                "Fonds propres": fonds_propres,
                "RWA Retrait": rwa_retrait,
                "Δ RWA PNU": delta_rwa_pnu,
                "RWA combiné": rwa_combine,
                "Ratio Retrait (%)": ratio_retrait,
                "Ratio combiné (%)": ratio_combine,
                "df_bloc_stresse": resultat["df_bloc_stresse"]
            })

        if recap_data:
            st.markdown("## Tableau comparatif : Retrait seul vs Retrait + PNU")
            df_recap = pd.DataFrame([{
                "Année": r["Année"],
                "Fonds propres": format_large_number(r["Fonds propres"]),
                "RWA Retrait": format_large_number(r["RWA Retrait"]),
                "Δ RWA PNU": format_large_number(r["Δ RWA PNU"]),
                "RWA combiné": format_large_number(r["RWA combiné"]),
                "Ratio Retrait (%)": f"{r['Ratio Retrait (%)']:.2f}%",
                "Ratio combiné (%)": f"{r['Ratio combiné (%)']:.2f}%"
            } for r in recap_data])
            st.dataframe(df_recap, use_container_width=True)

        for r in recap_data:
            with st.expander(f"Détails pour l’année {r['Année']}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""<div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio Retrait</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                            {r['Ratio Retrait (%)']:.2f}%
                        </p></div>""", unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""<div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio combiné</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                            {r['Ratio combiné (%)']:.2f}%
                        </p></div>""", unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""<div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Fonds propres</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                            {format_large_number(r['Fonds propres'])}
                        </p></div>""", unsafe_allow_html=True)

                st.markdown("### Bloc institutionnel C0700_0007_1 recalculé")
                df_bloc_formate = r["df_bloc_stresse"].copy()
                for col in df_bloc_formate.select_dtypes(include=["float", "int"]).columns:
                    df_bloc_formate[col] = df_bloc_formate[col].apply(format_large_number)
                st.dataframe(df_bloc_formate, use_container_width=True)

        return recap_data

    except Exception as e:
        st.error(f"Erreur lors du calcul du stress retrait dépôts : {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

def afficher_resultats_levier(params, resultats_projete_levier, resultats_solva=None):
    try:
        resultats_solva = st.session_state.get("resultats_solva", {}) if resultats_solva is None else resultats_solva

        horizon = params.get("horizon", 3)
        pourc_portefeuille = params.get("pourcentage_portefeuille", 0)
        pourc_creances = params.get("pourcentage_creances", 0)

        # === Chargement du bilan ===
        bilan_path = os.path.join("data", "bilan.xlsx")
        if not os.path.exists(bilan_path):
            st.error(f"❌ Fichier de bilan introuvable : {bilan_path}")
            return None

        bilan = pd.read_excel(bilan_path).iloc[2:].reset_index(drop=True)

        # Nettoyage
        if "Unnamed: 1" in bilan.columns:
            bilan = bilan.drop(columns=["Unnamed: 1"])
        for i, col in enumerate(bilan.columns):
            if str(col).startswith("Unnamed: 6"):
                bilan = bilan.iloc[:, :i]
                break

        bilan.columns.values[0:5] = ["Poste du Bilan", "2024", "2025", "2026", "2027"]
        bilan = bilan.dropna(how="all").reset_index(drop=True)
        if 25 in bilan.index:
            bilan = bilan.drop(index=25).reset_index(drop=True)

        # Extraction des postes ciblés
        poste_1 = bilan[bilan["Poste du Bilan"].str.contains("Portefeuille", case=False, na=False)]
        poste_2 = bilan[bilan["Poste du Bilan"].str.contains("Créances banques autres", case=False, na=False)]

        valeur_1 = poste_1["2024"].values[0] if not poste_1.empty else 0
        valeur_2 = poste_2["2024"].values[0] if not poste_2.empty else 0

        if valeur_1 == 0 and valeur_2 == 0:
            st.warning("❌ Aucun poste cible n'a été trouvé dans le bilan.")
            return None

        # Calcul du stress
        stress_portefeuille = valeur_1 * pourc_portefeuille
        stress_creances = valeur_2 * pourc_creances
        montant_stress_total = stress_portefeuille + stress_creances

        if not resultats_projete_levier or "2025" not in resultats_projete_levier:
            st.error("❌ Données projetées manquantes ou incorrectes.")
            return None

        # Stress test
        resultats_stress = executer_stress_event1_levier_pluriannuel(
            resultats_proj=resultats_projete_levier,
            resultats_solva=resultats_solva,
            montant_stress_total=montant_stress_total,
            annee_debut="2025",
            horizon=horizon
        )

        recap_data = []
        for i in range(horizon):
            annee = str(2025 + i)
            resultat = resultats_stress.get(annee)
            if not resultat:
                continue

            fonds_propres = resultat["tier1"]
            exposition = resultat["total_exposure_stresse"]
            ratio = resultat["ratio_levier_stresse"]

            recap_data.append({
                "Année": annee,
                "Fonds propres": fonds_propres,
                "Exposition totale": exposition,
                "Ratio de levier (%)": ratio,
                "df_c4700_stresse": resultat["df_c4700_stresse"]
            })

        # Affichage synthétique
        if recap_data:
            df_recap = pd.DataFrame([{
                "Année": r["Année"],
                "Fonds propres": format_large_number(r["Fonds propres"]),
                "Exposition totale": format_large_number(r["Exposition totale"]),
                "Ratio de levier (%)": f"{r['Ratio de levier (%)']:.2f}%"
            } for r in recap_data])
            st.dataframe(df_recap, use_container_width=True)

        # === Étape 6 : Détail annuel stylisé + tableau surligné
        for r in recap_data:
            with st.expander(f"Détails pour l’année {r['Année']}"):

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio de levier</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                                {r['Ratio de levier (%)']:.2f}%
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Fonds propres</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                {format_large_number(r['Fonds propres'])}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Exposition totale</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                                {format_large_number(r['Exposition totale'])}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)

                st.markdown("### Bloc C47.00 après stress")

                df_affiche = r["df_c4700_stresse"].copy()

                if "Row" not in df_affiche.columns:
                    st.warning("❌ Colonne 'Row' manquante dans le tableau C47.00.")
                    continue

                couleur_pwc_orange = "#ff5f05"

                def highlight_row_190(row):
                    return ['background-color: {}'.format(couleur_pwc_orange) if row["Row"] == 190 else '' for _ in row]

                st.dataframe(
                    df_affiche.style.apply(highlight_row_190, axis=1),
                    use_container_width=True
                )

        return recap_data

    except Exception as e:
        st.error(f"Erreur lors de l'affichage du ratio de levier stressé : {e}")
        import traceback
        st.error(traceback.format_exc())
        return None


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
pwc_orange = "#f47721"
pwc_dark_gray = "#3d3d3d"
pwc_light_beige = "#f5f0e6"
pwc_brown = "#6e4c1e"
pwc_soft_black = "#2c2c2c"

def afficher_tableau_recapitulatif(recap_data, ratio_type):
    # Vérification de la structure des données
    if not isinstance(recap_data, list) or not all(isinstance(x, dict) for x in recap_data):
        st.error("Les données de récapitulatif ne sont pas au bon format.")
        return

    # Créer le dataframe récapitulatif selon le type de ratio
    if ratio_type == "LCR":
        recap_df = pd.DataFrame([{
            "Année": f"{x['Année']:,.0f}".replace(",", ""),
            "HQLA": f"{x['HQLA']:,.2f}".replace(",", " ").replace(".", "."),
            "Inflows": f"{x['Inflows']:,.2f}".replace(",", " ").replace(".", "."),
            "Outflows": f"{x['Outflows']:,.2f}".replace(",", " ").replace(".", "."),
            f"{ratio_type} (%)": f"{x[f'{ratio_type} (%)']:.2f}%"
        } for x in recap_data])
    elif ratio_type == "NSFR":
        recap_df = pd.DataFrame([{
            "Année": f"{x['Année']:,.0f}".replace(",", ""),
            "ASF": f"{x['ASF']:,.2f}".replace(",", " ").replace(".", "."),
            "RSF": f"{x['RSF']:,.2f}".replace(",", " ").replace(".", "."),
            f"{ratio_type} (%)": f"{x[f'{ratio_type} (%)']:.2f}%"
        } for x in recap_data])
    elif ratio_type == "Solvabilité":
        recap_df = pd.DataFrame([{
            "Année": x["Année"],
            "Fonds propres": f"{x['Fonds propres']:,.2f}".replace(",", " ").replace(".", "."),
            "RWA total": f"{x['RWA total']:,.2f}".replace(",", " ").replace(".", "."),
            f"Ratio de {ratio_type} (%)": f"{x['Ratio de solvabilité (%)']:.2f}%"
        } for x in recap_data])
    elif ratio_type == "Levier":
        recap_df = pd.DataFrame([{
            "Année": x["Année"],
            "Fonds propres": f"{x['Fonds propres']:,.2f}".replace(",", " ").replace(".", "."),
            "Exposition totale": f"{x['Exposition totale']:,.2f}".replace(",", " ").replace(".", "."),
            f"Ratio de {ratio_type} (%)": f"{x['Ratio de levier (%)']:.2f}%"
        } for x in recap_data])
    else:
        st.warning(f"Type de ratio inconnu : {ratio_type}")
        return

    st.dataframe(recap_df, use_container_width=True)

    # Affichage détaillé par année
    for annee_data in recap_data:
        with st.expander(f"Détails de calcul {ratio_type} pour {annee_data['Année']}"):
            st.markdown(f"#### Année {annee_data['Année']}")
           
            if ratio_type == "LCR":
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                        st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">LCR</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">{annee_data['LCR (%)']:.2f}%</p>
                        </div>
                        """, unsafe_allow_html=True)

                with col2:
                        st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">HQLA</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{format_large_number(annee_data['HQLA'])}</p>
                        </div>
                        """, unsafe_allow_html=True)

                with col3:
                        st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Outflows</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{format_large_number(annee_data['Outflows'])}</p>
                        </div>
                        """, unsafe_allow_html=True)

                with col4:
                        st.markdown(f"""
                        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Inflows</h4>
                            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{format_large_number(annee_data['Inflows'])}</p>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("**Actifs liquides de haute qualité (HQLA)**")
                st.dataframe(affiche_LB_lcr(annee_data['df_72']), use_container_width=True)

                st.markdown("**Sorties de liquidités (Outflows)**")
                st.dataframe(affiche_outflow_lcr(annee_data['df_73']), use_container_width=True)

                st.markdown("**Entrées de liquidités (Inflows)**")
                st.dataframe(affiche_inflow_lcr(annee_data['df_74']), use_container_width=True)

            elif ratio_type == "NSFR":
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">NSFR</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">{annee_data['NSFR (%)']:.2f}%</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">ASF</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{format_large_number(annee_data['ASF'])}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">RSF</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{format_large_number(annee_data['RSF'])}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("**Available Stable Funding (ASF)**")
                st.dataframe(affiche_ASF(annee_data['df_81']), use_container_width=True)

                st.markdown("**Required Stable Funding (RSF)**")
                st.dataframe(affiche_RSF(annee_data['df_80']), use_container_width=True)

            elif ratio_type == "Solvabilité":
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio de Solvabilité</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                            {annee_data['Ratio de solvabilité (%)']:.2f}%
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Fonds propres</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                            {format_large_number(annee_data['Fonds propres'])}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">RWA total</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                            {format_large_number(annee_data['RWA total'])}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                if annee_data["Année"] == "2024":
                    st.markdown("**COREP de référence (avant stress)**")
                    if "df_bloc_cap" in annee_data:
                        afficher_corep_detaille(annee_data["df_bloc_cap"])
                    else:
                        st.info("Données de COREP non disponibles pour cette année.")
                else:
                    if "df_bloc_cap" in annee_data:
                        st.markdown("** COREP après Capital Planning**")
                        afficher_corep_detaille(annee_data["df_bloc_cap"])
                    if "df_bloc_stresse" in annee_data:
                        st.markdown("** COREP après application du stress**")
                        afficher_corep_detaille(annee_data["df_bloc_stresse"])

                if annee_data["Année"] == "2027":
                    st.markdown("### Seuils réglementaires")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Seuil minimum CET1", "4.5%")
                    with col2:
                        st.metric("Seuil minimum Tier 1", "6.0%")
                    with col3:
                        st.metric("Seuil minimum Total Capital", "8.0%")

                    st.subheader("Analyse de l'impact du stress test")
                    ratio_initial = recap_data[0]["Ratio de solvabilité (%)"]
                    ratio_final = recap_data[-1]["Ratio de solvabilité (%)"]
                    delta_ratio = ratio_final - ratio_initial

                    if delta_ratio < 0:
                        st.warning(f"Le ratio de solvabilité diminue de {abs(delta_ratio):.2f} points de pourcentage sur la période.")
                        if ratio_final < 8.0:
                            st.error("⚠️ Le ratio final est inférieur au seuil réglementaire minimum de 8% !")
                    else:
                        st.success(f"Le ratio de solvabilité augmente de {delta_ratio:.2f} points de pourcentage sur la période.")

            elif ratio_type == "Levier":
                recap_df = pd.DataFrame([{
                    "Année": x["Année"],
                    "Fonds propres": f"{x['Fonds propres']:,.2f}",
                    "Exposition totale": f"{x['Exposition totale']:,.2f}",
                    f"Ratio de {ratio_type} (%)": f"{x['Ratio de levier (%)']:.2f}%"
                } for x in recap_data])
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio de Levier</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                            {annee_data['Ratio de levier (%)']:.2f}%
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                            st.markdown(f"""
    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Fonds propres</h4>
        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
            {format_large_number(annee_data['Fonds propres'])}
        </p>
    </div>
    """, unsafe_allow_html=True)

                with col3:
                           st.markdown(f"""
    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Exposition totale</h4>
        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
            {format_large_number(annee_data['Exposition totale'])}
        </p>
    </div>
    """, unsafe_allow_html=True)

                st.markdown("**Tableau COREP - Exposition au levier (C47.00)**")
                key_prefix = f"corep_levier_{annee_data['Année']}"

                if "df_c4700_stresse" in annee_data and isinstance(annee_data["df_c4700_stresse"], pd.DataFrame):
                    afficher_corep_levier_detaille(annee_data["df_c4700_stresse"], key_prefix=key_prefix)
                elif "df_c4700_cap" in annee_data and isinstance(annee_data["df_c4700_cap"], pd.DataFrame):
                    afficher_corep_levier_detaille(annee_data["df_c4700_cap"], key_prefix=key_prefix)
                elif "df_c4700" in annee_data and isinstance(annee_data["df_c4700"], pd.DataFrame):
                    afficher_corep_levier_detaille(annee_data["df_c4700"], key_prefix=key_prefix)
                else:
                    st.info("Aucun détail COREP levier valide disponible pour cette année.")

############################### Evenement 2 : Tirage PNU ###############################
def executer_tirage_pnu():
    bilan = st.session_state.bilan
    params = afficher_parametres_tirage_pnu()

    if st.button("Exécuter le stress test - Tirage PNU", key="executer_tirage_pnu", use_container_width=True):
        with st.spinner("Exécution du stress test Tirage PNU en cours..."):
            try:
                # Store original in session state
                #st.session_state.bilan_original = bilan.copy()
               
                # Apply stress
                bilan_stresse = bst2.appliquer_tirage_pnu(
                    bilan_df=bilan,
                    pourcentage=params["pourcentage"],
                    horizon=params["horizon"],
                    poids_portefeuille=params["impact_portefeuille"],
                    poids_dettes=params["impact_dettes"],
                    annee="2024"
                )
               
                # Store stressed version
                st.session_state.bilan = bilan_stresse
                st.session_state.bilan_stresse = bilan_stresse
                st.success("Stress test exécuté avec succès!")
                afficher_resultats_tirage_pnu(bilan_stresse, params)
                # Set the stress test executed flag
                st.session_state.stress_test_executed = True
               
                return params
               
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du stress test: {str(e)}")
                st.session_state.stress_test_executed = False
                return None

    return None

def afficher_parametres_tirage_pnu():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### <span style='font-size:18px;'>Paramètres du tirage PNU</span>", unsafe_allow_html=True)

        pourcentage = st.slider("Pourcentage de tirage PNU (%)", 0, 100, 10, 5) / 100.0
        horizon = st.slider("Horizon de stress (années)", 1, 10, 3, 1)
        horizon_global = st.session_state.get("horizon_global", 3)
        if horizon > horizon_global:
            st.error(f"L'horizon de l'événement ne peut pas dépasser l'horizon global du stress test ({horizon_global} ans). Veuillez choisir une valeur inférieure ou égale.")
        inclure_corpo = st.checkbox("Inclure segment Corporate", value=True)
        inclure_retail = st.checkbox("Inclure segment Retail", value=True)
        inclure_hypo = st.checkbox("Inclure prêts hypothécaires", value=True)

    with col2:
        st.markdown("#### <span style='font-size:18px;'>Répartition de l'impact</span>", unsafe_allow_html=True)

        if "impact_portefeuille" not in st.session_state:
            st.session_state.impact_portefeuille = 15
        if "impact_dettes" not in st.session_state:
            st.session_state.impact_dettes = 85
        if "last_changed_impact" not in st.session_state:
            st.session_state.last_changed_impact = "portefeuille"

        def on_change_portefeuille():
            st.session_state.last_changed_impact = "portefeuille"
            st.session_state.impact_dettes = 100 - st.session_state.impact_portefeuille

        def on_change_dettes():
            st.session_state.last_changed_impact = "dettes"
            st.session_state.impact_portefeuille = 100 - st.session_state.impact_dettes

        st.slider(
            "Portefeuille (%)",
            0, 100,
            key="impact_portefeuille",
            step=5,
            on_change=on_change_portefeuille
        )

        st.slider(
            "Dettes envers établissements de crédit (%)",
            0, 100,
            key="impact_dettes",
            step=5,
            on_change=on_change_dettes
        )

    # Conversion en décimales
    impact_portefeuille = st.session_state.impact_portefeuille / 100.0
    impact_dettes = st.session_state.impact_dettes / 100.0

    return {
        "pourcentage": pourcentage,
        "inclure_corpo": inclure_corpo,
        "inclure_retail": inclure_retail,
        "inclure_hypo": inclure_hypo,
        "impact_dettes": impact_dettes,
        "impact_portefeuille": impact_portefeuille,
        "horizon": horizon
    }

def afficher_resultats_tirage_pnu(bilan_stresse, params):
    st.subheader("Impact sur le bilan (Tirage PNU)")
    postes_concernes = ["Créances clientèle", "Portefeuille", "Dettes envers les établissements de crédit (passif)","Engagements de garantie donnés"]
    bilan_filtre = bst.afficher_postes_concernes(bilan_stresse, postes_concernes, horizon=params['horizon'])
    st.dataframe(bilan_filtre)

    if "resultats_horizon" not in st.session_state:
        st.session_state["resultats_horizon"] = {}
   
    # Section principale des résultats
    st.markdown("### Résultats du stress test")
   
    # Afficher les ratios dans des cartes
    afficher_ratios_tirage_pnu()
   
    # Section LCR - Correction de l'appel de fonction en passant params comme second argument
    st.subheader("Impact sur la liquidité (LCR)")
    # Correction ici: passage de params au lieu de postes_concernes
    recap_data_lcr = afficher_resultats_lcr_tirage_pnu(bilan_stresse, params, horizon=params['horizon'])
    if recap_data_lcr:
        for year_data in recap_data_lcr:
            year = year_data["Année"]
            if year not in st.session_state["resultats_horizon"]:
                st.session_state["resultats_horizon"][year] = {}
            st.session_state["resultats_horizon"][year].update({
                "df_72": year_data["df_72"],
                "df_73": year_data["df_73"],
                "df_74": year_data["df_74"],
                "lcr_data": {
                    "HQLA": year_data["HQLA"],
                    "Inflows": year_data["Inflows"],
                    "Outflows": year_data["Outflows"],
                    "LCR (%)": year_data["LCR (%)"]
                }
            })
        afficher_tableau_recapitulatif(recap_data_lcr, "LCR")
    # Section NSFR
    st.subheader("Impact sur le ratio NSFR")

    bst2.show_other_liabilities_tab()
    bst2.show_rsf_lines_tab()
    # Correction ici: passage de params au lieu de postes_concernes
    recap_data_nsfr = afficher_resultats_nsfr_tirage_pnu(bilan_stresse, params, horizon=params['horizon'])
    if recap_data_nsfr:
        for year_data in recap_data_nsfr:
            year = year_data["Année"]
            if year not in st.session_state["resultats_horizon"]:
                st.session_state["resultats_horizon"][year] = {}
            st.session_state["resultats_horizon"][year].update({
                "df_80": year_data["df_80"],
                "df_81": year_data["df_81"],
                "nsfr_data": {
                    "ASF": year_data["ASF"],
                    "RSF": year_data["RSF"],
                    "NSFR (%)": year_data["NSFR (%)"]
                }
            })
        afficher_tableau_recapitulatif(recap_data_nsfr, "NSFR")

    from backend.ratios_baseline.capital_projete import simuler_solvabilite_pluriannuelle
    # Section slova
    st.subheader("Impact sur le ratio de solvabilité")
    if "resultats_solva" in st.session_state:
        resultats_proj = st.session_state["resultats_solva"]
        # Use resultats as needed
    else:
        st.warning("Résultats de solvabilité non disponibles.")
    recap_data = afficher_resultats_solva_tirage_pnu(bilan_stresse, params, resultats_proj)


def afficher_ratios_tirage_pnu():
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Part Loans (Outflow)</h4>
            <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">{bst2.part_loans_mb_outflow()}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Part Crédits Clientèle (Inflow)</h4>
            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{bst2.part_credit_clientele_inflow()}%</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                    box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
            <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Part Dépôts (Inflow)</h4>
            <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">{bst2.part_depots_mb_inflow()}%</p>
        </div>
        """, unsafe_allow_html=True)

def afficher_resultats_lcr_tirage_pnu(bilan_stresse, params, horizon=3):
    try:
        if 'resultats_horizon' not in st.session_state:
            st.error("Les résultats de base ne sont pas disponibles dans la session.")
            return None

        resultats_horizon = st.session_state['resultats_horizon']
       
        # Verify base year exists
        if 2024 not in resultats_horizon:
            st.error("Les données de l'année 2024 ne sont pas disponibles.")
            return None

        recap_data = []
        pourcentage = params["pourcentage"]
        poids_portefeuille = params["impact_portefeuille"]
        poids_dettes = params["impact_dettes"]

        # 2024 - No stress
        df_72 = resultats_horizon[2024]['df_72'].copy()
        df_73 = resultats_horizon[2024]['df_73'].copy()
        df_74 = resultats_horizon[2024]['df_74'].copy()

        recap_data.append({
            "Année": 2024,
            "HQLA": calcul_HQLA(df_72),
            "Inflows": calcul_inflow(df_74),
            "Outflows": calcul_outflow(df_73),
            "LCR (%)": Calcul_LCR(calcul_inflow(df_74), calcul_outflow(df_73), calcul_HQLA(df_72)) * 100,
            "df_72": df_72,
            "df_73": df_73,
            "df_74": df_74
        })

        # Process subsequent years
        for annee in [2025, 2026, 2027][:horizon]:
            if annee not in resultats_horizon:
                st.error(f"Données de base pour {annee} manquantes dans session state")
                return None

            # Get base DF for current year from session state
            df_72 = resultats_horizon[annee]['df_72'].copy()
            df_73 = resultats_horizon[annee]['df_73'].copy()
            df_74 = resultats_horizon[annee]['df_74'].copy()

            # Apply cumulative stress from all previous years
            for prev_year in range(2025, annee):
                df_72 = bst2.propager_impact_portefeuille_vers_df72(
                    df_72, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon,
                    poids_portefeuille=poids_portefeuille
                )
               
                df_74 = bst2.propager_impact_vers_df74(
                    df_74, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon
                )
               
                df_73 = bst2.propager_impact_vers_df73(
                    df_73, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon,
                    poids_dettes=poids_dettes
                )

            # Apply current year's stress
            df_72 = bst2.propager_impact_portefeuille_vers_df72(
                df_72, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon,
                poids_portefeuille=poids_portefeuille
            )
           
            df_74 = bst2.propager_impact_vers_df74(
                df_74, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon
            )
           
            df_73 = bst2.propager_impact_vers_df73(
                df_73, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon,
                poids_dettes=poids_dettes
            )

            # Calculate metrics
            recap_data.append({
                "Année": annee,
                "HQLA": calcul_HQLA(df_72),
                "Inflows": calcul_inflow(df_74),
                "Outflows": calcul_outflow(df_73),
                "LCR (%)": Calcul_LCR(calcul_inflow(df_74), calcul_outflow(df_73), calcul_HQLA(df_72)) * 100,
                "df_72": df_72,
                "df_73": df_73,
                "df_74": df_74
            })

        return recap_data

    except Exception as e:
        st.error(f"Erreur lors du calcul du LCR après tirage PNU : {str(e)}")
        return None
   

def afficher_resultats_nsfr_tirage_pnu(bilan_stresse, params, horizon=3):
    try:
        if 'resultats_horizon' not in st.session_state:
            st.error("Les résultats de base ne sont pas disponibles dans la session.")
            return None

        resultats_horizon = st.session_state['resultats_horizon']
       
        # Verify base year exists
        if 2024 not in resultats_horizon:
            st.error("Les données de l'année 2024 ne sont pas disponibles.")
            return None

        recap_data = []
        pourcentage = params["pourcentage"]
        poids_portefeuille = params["impact_portefeuille"]
        poids_dettes = params["impact_dettes"]

        # 2024 - No stress
        df_80 = resultats_horizon[2024]['df_80'].copy()
        df_81 = resultats_horizon[2024]['df_81'].copy()

        recap_data.append({
            "Année": 2024,
            "ASF": calcul_ASF(df_81),
            "RSF": calcul_RSF(df_80),
            "NSFR (%)": Calcul_NSFR(calcul_ASF(df_81), calcul_RSF(df_80)),
            "df_80": df_80,
            "df_81": df_81
        })

        # Process subsequent years
        for annee in [2025, 2026, 2027][:horizon]:
            if annee not in resultats_horizon:
                st.error(f"Données de base pour {annee} manquantes dans session state")
                return None

            # Get base DF for current year from session state
            df_80 = resultats_horizon[annee]['df_80'].copy()
            df_81 = resultats_horizon[annee]['df_81'].copy()

            # Apply cumulative stress from all previous years
            for prev_year in range(2025, annee):
                df_80 = bst2.propager_impact_vers_df80(
                    df_80, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon
                )
               
                df_81 = bst2.propager_impact_vers_df81(
                    df_81, bilan_stresse, annee=prev_year,
                    pourcentage=pourcentage, horizon=horizon,
                    poids_dettes=poids_dettes
                )

            # Apply current year's stress
            df_80 = bst2.propager_impact_vers_df80(
                df_80, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon
            )
           
            df_81 = bst2.propager_impact_vers_df81(
                df_81, bilan_stresse, annee=annee,
                pourcentage=pourcentage, horizon=horizon,
                poids_dettes=poids_dettes
            )

            # Calculate metrics
            recap_data.append({
                "Année": annee,
                "ASF": calcul_ASF(df_81),
                "RSF": calcul_RSF(df_80),
                "NSFR (%)": Calcul_NSFR(calcul_ASF(df_81), calcul_RSF(df_80)),
                "df_80": df_80,
                "df_81": df_81
            })

        return recap_data

    except Exception as e:
        st.error(f"Erreur lors du calcul du NSFR après tirage PNU : {str(e)}")
        return None

def afficher_resultats_solva_tirage_pnu(bilan_stresse, params, resultats_proj):
    try:
        horizon = params.get("horizon", 3)
        pourcentage = params.get("pourcentage", 0.10)

            # === Étape 1 : Lecture du bilan
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

       
       
        # === Étape 2 : Initialisation des tirages par segment cochés
        tirage_par_segment = {}

        if params.get("inclure_corpo", False):
            ligne_corpo = bilan[bilan["Poste du Bilan"].str.contains("Dont Corpo", case=False, na=False)]
            if not ligne_corpo.empty:
                valeur_corpo = ligne_corpo["2024"].values[0]
                tirage_par_segment["C0700_0009_1"] = valeur_corpo * pourcentage

        if params.get("inclure_retail", False):
            ligne_retail = bilan[bilan["Poste du Bilan"].str.contains("Dont Retail", case=False, na=False)]
            if not ligne_retail.empty:
                valeur_retail = ligne_retail["2024"].values[0]
                tirage_par_segment["C0700_0008_1"] = valeur_retail * pourcentage

        if params.get("inclure_hypo", False):
            ligne_hypo = bilan[bilan["Poste du Bilan"].str.contains("Dont Hypo", case=False, na=False)]
            if not ligne_hypo.empty:
                valeur_hypo = ligne_hypo["2024"].values[0]
                tirage_par_segment["C0700_0010_1"] = valeur_hypo * pourcentage

        if not tirage_par_segment:
            st.warning(" Aucun segment sélectionné ou lignes 'Dont' manquantes dans le bilan.")
            return None

        # === Étape 3 : Exécution du stress pluriannuel
        resultats_stress = executer_stress_pnu_capital_pluriannuel(
            resultats_proj=resultats_proj,
            annee_debut="2025",
            tirages_par_segment=tirage_par_segment,
            horizon=horizon,
            debug=False
        )
        # ✅ Stocker les delta RWA de PNU pour combinaison future
        st.session_state["delta_rwa_pnu"] = {
            annee: resultat["delta_rwa_total"]
            for annee, resultat in resultats_stress.items()
        }

                # === Étape 4 : Construction du tableau récapitulatif pour affichage
        recap_data = []
        delta_retrait = st.session_state.get("delta_rwa_event1", {})  # Contient éventuellement le stress de l'autre événement

        for i in range(horizon):
            annee = str(2025 + i)
            resultat = resultats_stress.get(annee)
            if not resultat:
                continue

            fonds_propres = resultats_proj[annee]["fonds_propres"]
            rwa_pnu = resultat["rwa_total_stresse"]
            delta_rwa_event1 = delta_retrait.get(annee, 0)
            rwa_combine = rwa_pnu + delta_rwa_event1

            ratio_pnu = (fonds_propres / rwa_pnu) * 100 if rwa_pnu > 0 else 0
            ratio_combine = (fonds_propres / rwa_combine) * 100 if rwa_combine > 0 else 0

            recap_data.append({
                "Année": annee,
                "Fonds propres": fonds_propres,
                "RWA total PNU": rwa_pnu,
                "Δ RWA Retrait": delta_rwa_event1,
                "RWA combiné": rwa_combine,
                "Ratio PNU (%)": ratio_pnu,
                "Ratio combiné (%)": ratio_combine,
                "blocs_stresses": resultat["blocs_stresses"]
            })

        # === Étape 5 : Affichage du tableau récapitulatif formaté
        if recap_data:
            st.markdown("##  Tableau comparatif : PNU seul vs PNU + Retrait")

            df_affiche = pd.DataFrame([{
                "Année": r["Année"],
                "Fonds propres": format_large_number(r["Fonds propres"]),
                "RWA PNU": format_large_number(r["RWA total PNU"]),
                "Δ RWA Retrait": format_large_number(r["Δ RWA Retrait"]),
                "RWA combiné": format_large_number(r["RWA combiné"]),
                "Ratio PNU (%)": f"{r['Ratio PNU (%)']:.2f}%",
                "Ratio combiné (%)": f"{r['Ratio combiné (%)']:.2f}%"
            } for r in recap_data])

            st.dataframe(df_affiche, use_container_width=True)

        # === Étape 6 : Affichage détaillé (C0700 recalculés par bloc)
        for annee in resultats_stress:
            result = resultats_stress[annee]
            with st.expander(f" Détails de l'année {annee}"):
                fonds_propres = resultats_proj[annee]["fonds_propres"]
                rwa_stresse = result["rwa_total_stresse"]
                ratio = (fonds_propres / rwa_stresse) * 100 if rwa_stresse > 0 else 0

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_orange}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Ratio de Solvabilité</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_orange}; margin:0;">
                            {ratio:.2f}%
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_brown}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">Fonds Propres (Tier 1)</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                            {format_large_number(fonds_propres)}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                    <div style="background-color:{pwc_light_beige}; padding:20px; border-radius:15px;
                                box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {pwc_dark_gray}">
                        <h4 style="color:{pwc_soft_black}; margin-bottom:10px;">RWA total stressé</h4>
                        <p style="font-size:26px; font-weight:bold; color:{pwc_dark_gray}; margin:0;">
                            {format_large_number(rwa_stresse)}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("### Blocs C0700 recalculés")
                for nom_bloc, df in result["blocs_stresses"].items():
                    nom_affiche = {
                        "C0700_0008_1": "Retail",
                        "C0700_0009_1": "Corporate",
                        "C0700_0010_1": "Hypothécaire"
                    }.get(nom_bloc, nom_bloc)
                    st.markdown(f"**{nom_affiche}**")
                    st.dataframe(df)

        # Important: Return the recap_data for use in the main display function
        return recap_data

    except Exception as e:
        st.error(f"Erreur dans le stress PNU capital : {e}")
        import traceback
        st.error(traceback.format_exc())
        return None
