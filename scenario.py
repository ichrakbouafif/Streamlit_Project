import streamlit as st
import config
import numpy as np
import backend_stress_test as bst

def show():
    st.title("Choix des scénarios")
    
    # Initialize session state if not already done
    if "scenario_type" not in st.session_state:
        st.session_state.scenario_type = None
    if "selected_events" not in st.session_state:
        st.session_state.selected_events = []
    
    # Phase 1: Scenario type selection
    st.subheader("Phase 1 : Sélection du premier scénario")
    
    # Scenario type radio buttons
    scenario_type = st.radio(
        "Type de scénario à calibrer",
        ["Scénario Idiosyncratique", "Scénario Macroéconomique"],
        key="scenario_type_radio"
    )
    
    # Determine the internal scenario type
    scenario_type_key = "idiosyncratique" if "Idiosyncratique" in scenario_type else "macroéconomique"
    st.session_state.scenario_type = scenario_type_key
    
    # Get available events for the selected scenario type
    available_events = list(config.scenarios[scenario_type_key].keys())
    
    # Event selection multiselect
    selected_events = st.multiselect(
        "Événements disponibles",
        available_events,
        key="events_multiselect"
    )
    
    # Store selected events in session state
    st.session_state.selected_events = selected_events
    
    # If events are selected, show their configuration
    if selected_events:
        afficher_configuration_evenements(selected_events, scenario_type_key)
    
    # Validation button
    if st.button("Valider ce scénario"):
        if not selected_events:
            st.warning("Veuillez sélectionner au moins un événement.")
        else:
            st.success("Scénario validé avec succès!")

def afficher_configuration_evenements(selected_events, scenario_type):
    """Show configuration for selected events"""
    events_dict = config.scenarios[scenario_type]
    
    for event in selected_events:
        st.markdown(f"### Configuration pour: {event}")
        
        if event == "Retrait massif des dépôts":
            # Special handling for deposit withdrawal event
            executer_retrait_depots()
        else:
            # For other events, show not implemented message
            st.warning("Cette fonctionnalité n'est pas encore implémentée.")
            st.info("Seul l'événement 'Retrait massif des dépôts' est actuellement disponible.")

def afficher_parametres_retrait_depots():
    """Affiche les paramètres spécifiques pour l'événement de retrait massif des dépôts"""
    st.subheader("Paramètres du retrait massif des dépôts")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Paramètre p1: pourcentage de diminution des dépôts
        p1 = st.slider(
            "Pourcentage de diminution des dépôts (%)",
            min_value=5,
            max_value=50,
            value=15,
            step=5
        ) / 100.0  # Conversion en décimal
        
        # Paramètre p2: horizon d'absorption du choc
        p2 = st.slider(
            "Horizon d'absorption du choc (années)",
            min_value=1,
            max_value=5,
            value=1,
            step=1
        )
        
    with col2:
        # Paramètre p3: mode d'écoulement (uniquement si p2 > 1)
        p3 = 'equitable'
        if p2 > 1:
            p3_options = {'Équitable': 'equitable', 'Première année seulement': 'premiere_annee'}
            p3 = st.radio(
                "Mode d'écoulement du choc",
                options=list(p3_options.keys()))
            p3 = p3_options[p3]

        # Paramètre année de départ
        annee_depart = st.selectbox(
            "Année de départ",
            options=["2024", "2025", "2026", "2027"],
            index=1  # 2025 par défaut
        )
    
    # Paramètres de contrepartie
    st.subheader("Répartition de l'impact")
    st.markdown("Répartition de l'impact du retrait des dépôts:")
    
    poids_portefeuille = st.slider(
        "Portefeuille (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5
    ) / 100.0

    poids_creances = st.slider(
        "Créances bancaires (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5
    ) / 100.0

    # Vérification de la somme des poids
    total_poids = poids_portefeuille + poids_creances
    if not np.isclose(total_poids, 1.0):
        st.warning(f"La somme des pourcentages doit être égale à 100%. Actuellement: {total_poids*100:.0f}%")
        st.info("Ajustement automatique appliqué.")
        # Normalisation
        poids_portefeuille = poids_portefeuille / total_poids
        poids_creances = poids_creances / total_poids
    
    return {
        'p1': p1,
        'p2': p2,
        'p3': p3,
        'annee_depart': annee_depart,
        'poids_portefeuille': poids_portefeuille,
        'poids_creances': poids_creances
    }

def executer_retrait_depots():
    """Exécute et affiche les résultats du stress test de retrait des dépôts"""
    bilan = bst.charger_bilan()
    
    
    # Afficher les paramètres et les récupérer
    params = afficher_parametres_retrait_depots()
    
    if st.button("Exécuter le stress test", key="executer_stress_test", use_container_width=True):
        with st.spinner("Exécution du stress test en cours..."):
            resultats = bst.appliquer_stress_retrait_depots(                
                bilan_df=bilan,
                p1=params['p1'],
                p2=params['p2'],
                p3=params['p3'],
                annee=params['annee_depart'],
                poids_portefeuille=params['poids_portefeuille'],
                poids_creances=params['poids_creances']

            )
            if "erreur" in resultats:
                st.error(f"Erreur: {resultats['erreur']}")
            else:
                st.session_state.resultats_stress_test = resultats
                st.success("Stress test exécuté avec succès!")
                
                # Afficher les résultats
                afficher_resultats_retrait_depots(resultats)
    #st.dataframe(resultats, use_container_width=True)

def afficher_resultats_retrait_depots(resultats):
    """Affiche les résultats détaillés du stress test de retrait des dépôts"""
    bilan_stresse = resultats
    
    # 1. Afficher les postes concernés
    st.subheader("Impact sur le bilan")
    poste = "Depots clients (passif)"
    postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
    bilan_filtre = bst.afficher_postes_concernes(resultats, postes_concernes)
    st.dataframe(bilan_filtre)
    
    # 2. Calculer et afficher le LCR stressé
    st.subheader("Impact sur la liquidité (LCR)")
    
    # Charger les données COREP initiales
    df_72, df_73, df_74 = bst.charger_lcr()
    
    # Appliquer les deltas pour chaque poste concerné
    for poste in postes_concernes:
        delta = bst.get_delta_bilan(bst.charger_bilan(), bilan_stresse, poste, "2025")
        if delta != 0:
            # Ponderations pour la propagation vers COREP
            ponderations = [0.5, 0.3, 0.2]
            df_72, df_73, df_74 = bst.propager_delta_vers_corep(poste, delta, df_72, df_73, df_74)
    
    # Calculer les indicateurs de liquidité
    try:
        from backend.lcr.utils import affiche_LB_lcr, affiche_outflow_lcr, affiche_inflow_lcr
        from backend.lcr.feuille_72 import calcul_HQLA
        from backend.lcr.feuille_73 import calcul_outflow
        from backend.lcr.feuille_74 import calcul_inflow
        from backend.lcr.utils import Calcul_LCR
        
        # Afficher les tableaux détaillés
        LB = affiche_LB_lcr(df_72)
        IN = affiche_inflow_lcr(df_74)
        OUT = affiche_outflow_lcr(df_73)
        
        if not LB.empty:
            st.markdown("**Actifs liquides de haute qualité (HQLA)**")
            st.dataframe(LB, use_container_width=True)
            
            st.markdown("**Entrées de liquidités (Inflows)**")
            st.dataframe(IN, use_container_width=True)
            
            st.markdown("**Sorties de liquidités (Outflows)**")
            st.dataframe(OUT, use_container_width=True)
        
        # Calculer et afficher les ratios
        HQLA = calcul_HQLA(df_72)
        
        OUTFLOWS = calcul_outflow(df_73)
        inflow = calcul_inflow(df_74)
        LCR = Calcul_LCR(inflow, OUTFLOWS, HQLA)
        
        # Afficher les résultats sous forme de métriques
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("LCR stressé", f"{LCR:.2%}")
        with col2:
            st.metric("HQLA", f"{HQLA:,.2f}")
        with col3:
            st.metric("Outflows", f"{OUTFLOWS:,.2f}")
        with col4:
            st.metric("Inflows", f"{inflow:,.2f}")
            
    except ImportError as e:
        st.error(f"Erreur lors du chargement des modules de calcul LCR: {e}")
    except Exception as e:
        st.error(f"Erreur lors du calcul du LCR: {e}")

if __name__ == "__main__": 
    show()