import streamlit as st
import config
import numpy as np
import pandas as pd
from backend.stress_test import event1 as bst
from backend.lcr.utils import affiche_LB_lcr, affiche_outflow_lcr, affiche_inflow_lcr
from backend.lcr.feuille_72 import calcul_HQLA
from backend.lcr.feuille_73 import calcul_outflow
from backend.lcr.feuille_74 import calcul_inflow
from backend.lcr.utils import Calcul_LCR
from backend.nsfr.utils import Calcul_NSFR, affiche_RSF, affiche_ASF
from backend.nsfr.feuille_80 import calcul_RSF
from backend.nsfr.feuille_81 import calcul_ASF
# Import additional modules for leverage and solvency
from backend.levier.calcul_ratio_levier import charger_donnees_levier, calculer_ratio_levier_double_etape
from backend.solvabilite.calcul_ratios_capital_stressé import charger_donnees, calculer_ratios_solva_double_etape

def show():
    st.title("Choix des scénarios")

    if "scenario_type" not in st.session_state:
        st.session_state.scenario_type = None
    if "selected_events" not in st.session_state:
        st.session_state.selected_events = []

    st.subheader("Phase 1 : Sélection du premier scénario")

    scenario_type = st.radio(
        "Type de scénario à calibrer",
        ["Scénario Idiosyncratique", "Scénario Macroéconomique"],
        key="scenario_type_radio"
    )

    scenario_type_key = "idiosyncratique" if "Idiosyncratique" in scenario_type else "macroéconomique"
    st.session_state.scenario_type = scenario_type_key

    available_events = list(config.scenarios[scenario_type_key].keys())

    selected_events = st.multiselect(
        "Événements disponibles",
        available_events,
        key="events_multiselect"
    )

    st.session_state.selected_events = selected_events

    if selected_events:
        afficher_configuration_evenements(selected_events, scenario_type_key)

    if st.button("Valider ce scénario"):
        if not selected_events:
            st.warning("Veuillez sélectionner au moins un événement.")
        else:
            st.success("Scénario validé avec succès!")
def format_large_number(num):
    """Format large numbers with M/B suffixes"""
    if pd.isna(num) or num == 0:
        return "0"
    abs_num = abs(num)
    if abs_num >= 1_000_000_000:
        return f"{num/1_000_000_000:.2f}B"
    elif abs_num >= 1_000_000:
        return f"{num/1_000_000:.2f}M"
    else:
        return f"{num:,.2f}"
    
def afficher_configuration_evenements(selected_events, scenario_type):
    events_dict = config.scenarios[scenario_type]

    for event in selected_events:
        st.markdown(f"### Configuration pour: {event}")

        if event == "Retrait massif des dépôts":
            executer_retrait_depots()
        else:
            st.warning("Cette fonctionnalité n'est pas encore implémentée.")
            st.info("Seul l'événement 'Retrait massif des dépôts' est actuellement disponible.")

def afficher_parametres_retrait_depots():
    st.subheader("Paramètres du retrait massif des dépôts")


    pourcentage = st.slider("Pourcentage de diminution des dépôts (%)", 0, 100, 15, 5) / 100.0
    horizon = st.slider("Horizon d'absorption du choc (années)", 1, 5, 1, 1)

    
        

    st.subheader("Répartition de l'impact")
    st.markdown("Répartition de l'impact du retrait des dépôts:")

    poids_portefeuille = st.slider("Portefeuille (%)", 0, 100, 50, 5) / 100.0
    poids_creances = st.slider("Créances bancaires (%)", 0, 100, 50, 5) / 100.0

    total_poids = poids_portefeuille + poids_creances
    if not np.isclose(total_poids, 1.0):
        st.warning(f"La somme des pourcentages doit être égale à 100%. Actuellement: {total_poids*100:.0f}%")
        st.info("Ajustement automatique appliqué.")
        poids_portefeuille = poids_portefeuille / total_poids
        poids_creances = poids_creances / total_poids

    return {
        'pourcentage': pourcentage,
        'horizon': horizon,
        'poids_portefeuille': poids_portefeuille,
        'poids_creances': poids_creances
    }

def executer_retrait_depots():
    bilan = bst.charger_bilan()
    st.write("Bilan actuel:")
    st.dataframe(bilan, use_container_width=True)
    params = afficher_parametres_retrait_depots()

    if st.button("Exécuter le stress test", key="executer_stress_test", use_container_width=True):
        with st.spinner("Exécution du stress test en cours..."):
            try:
                # Store original in session state
                st.session_state.bilan_original = bilan.copy()
                
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
                st.session_state.bilan_stresse = bilan_stresse
                st.success("Stress test exécuté avec succès!")
                afficher_resultats_retrait_depots(bilan_stresse, params)
                
            except Exception as e:
                st.error(f"Erreur lors de l'exécution du stress test: {str(e)}")


def afficher_resultats_retrait_depots(bilan_stresse, params):
    st.subheader("Impact sur le bilan")
    postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
    bilan_filtre = bst.afficher_postes_concernes(bilan_stresse, postes_concernes)
    st.dataframe(bilan_filtre)

    # Section LCR
    st.subheader("Impact sur la liquidité (LCR)")
    afficher_resultats_lcr(bilan_stresse, postes_concernes)
    
    # Section NSFR
    st.subheader("Impact sur le ratio NSFR")
    afficher_resultats_nsfr(bilan_stresse, postes_concernes)
    
    # Section Ratio de Solvabilité
    st.subheader("Impact sur le ratio de solvabilité")
    afficher_resultats_solva(bilan_stresse, postes_concernes, params)
    
    # Section Ratio de Levier
    st.subheader("Impact sur le ratio de levier")
    afficher_resultats_levier(bilan_stresse, postes_concernes, params)

def afficher_resultats_lcr(bilan_stresse, postes_concernes):
    try:
        df_72, df_73, df_74 = bst.charger_lcr()
        annees = ["2024", "2025", "2026", "2027"]
        recap_data = []
        
        for annee in annees:
            df_72_annee, df_73_annee, df_74_annee = df_72.copy(), df_73.copy(), df_74.copy()
            
            for poste in postes_concernes:
                delta = bst.get_delta_bilan(st.session_state.bilan_original, bilan_stresse, poste, annee)
                if delta != 0:
                    df_72_annee, df_73_annee, df_74_annee = bst.propager_delta_vers_COREP_LCR(
                        poste, delta, df_72_annee, df_73_annee, df_74_annee
                    )
            
            HQLA = calcul_HQLA(df_72_annee)
            outflow = calcul_outflow(df_73_annee)
            inflow = calcul_inflow(df_74_annee)
            LCR = Calcul_LCR(inflow, outflow, HQLA)
            
            recap_data.append({
                "Année": annee,
                "HQLA": HQLA,
                "Inflows": inflow,
                "Outflows": outflow,
                "LCR (%)": LCR*100,
                "df_72": df_72_annee,
                "df_73": df_73_annee,
                "df_74": df_74_annee
            })
        
        # Afficher le tableau récapitulatif LCR
        afficher_tableau_recapitulatif(recap_data, "LCR")
        
    except Exception as e:
        st.error(f"Erreur lors du calcul du LCR: {e}")

def afficher_resultats_nsfr(bilan_stresse, postes_concernes):
    try:
        df_80, df_81 = bst.charger_nsfr()
        annees = ["2024", "2025", "2026", "2027"]
        recap_data = []
        
        for annee in annees:
            df_80_annee, df_81_annee = df_80.copy(), df_81.copy()
            
            for poste in postes_concernes:
                delta = bst.get_delta_bilan(st.session_state.bilan_original, bilan_stresse, poste, annee)
                if delta != 0:
                    df_80_annee, df_81_annee = bst.propager_delta_vers_COREP_NSFR(
                        poste, delta, df_80_annee, df_81_annee
                    )
            
            ASF = calcul_ASF(df_81_annee)
            RSF = calcul_RSF(df_80_annee)
            NSFR = Calcul_NSFR(ASF, RSF)
            
            recap_data.append({
                "Année": annee,
                "ASF": ASF,
                "RSF": RSF,
                "NSFR (%)": NSFR,
                "df_80": df_80_annee,
                "df_81": df_81_annee
            })
        
        # Afficher le tableau récapitulatif NSFR
        afficher_tableau_recapitulatif(recap_data, "NSFR")
        
    except Exception as e:
        st.error(f"Erreur lors du calcul du NSFR: {e}")

def afficher_resultats_solva(bilan_stresse, postes_concernes, params):
    try:
        # Charger les données nécessaires pour le calcul de solvabilité
        bilan, df_c01, df_c02, df_bloc = charger_donnees()
        annees = ["2024", "2025", "2026", "2027"]
        recap_data = []
        
        # Pour chaque poste concerné, calculer l'impact sur le ratio de solvabilité
        for poste in postes_concernes:
            # On utilise le paramètre de stress défini par l'utilisateur
            stress_pct = params['pourcentage'] * 100  # Convertir en pourcentage
            horizon = params['horizon']
            
            # Stocker le paramètre de stress dans session_state pour référence future
            stress_key = f"Retrait massif des dépôts_Dépôts et avoirs de la clientèle_{poste}"
            st.session_state[stress_key] = stress_pct
            
            # Calculer les ratios de solvabilité pour chaque année
            df_resultats = calculer_ratios_solva_double_etape(
                bilan=bilan_stresse,
                poste_cible=poste,
                stress_pct=stress_pct,
                horizon=horizon,
                df_bloc_base=df_bloc,
                df_c01=df_c01,
                df_c02=df_c02
            )
            
            # Ajouter les résultats pour chaque année
            for _, row in df_resultats.iterrows():
                annee = row["Année"]
                recap_data.append({
                    "Année": annee,
                    "Fonds propres": row["Fonds propres"],
                    "RWA total": row["RWA total"],
                    "Ratio de solvabilité (%)": row["Ratio de solvabilité"],
                    "Poste": poste
                })
        
        # Créer le dataframe récapitulatif
        if recap_data:
            # Garder seulement une entrée par année (éviter les doublons)
            unique_recap = []
            for annee in annees:
                annee_data = [d for d in recap_data if d["Année"] == annee]
                if annee_data:
                    unique_recap.append(annee_data[0])
            
            # Afficher le tableau récapitulatif
            afficher_tableau_recapitulatif(unique_recap, "Solvabilité")
        else:
            st.warning("Aucune donnée de solvabilité disponible.")
        
    except Exception as e:
        st.error(f"Erreur lors du calcul de la solvabilité: {e}")
        import traceback
        st.error(traceback.format_exc())

def afficher_resultats_levier(bilan_stresse, postes_concernes, params):
    try:
        # Charger les données nécessaires pour le calcul du ratio de levier
        bilan, df_c01, df_c4700 = charger_donnees_levier()
        annees = ["2024", "2025", "2026", "2027"]
        recap_data = []
        
        # Pour chaque poste concerné, calculer l'impact sur le ratio de levier
        for poste in postes_concernes:
            # On utilise le paramètre de stress défini par l'utilisateur
            stress_pct = params['pourcentage'] * 100  # Convertir en pourcentage
            horizon = params['horizon']
            
            # Stocker le paramètre de stress dans session_state pour référence future
            stress_key = f"Retrait massif des dépôts_Dépôts et avoirs de la clientèle_{poste}"
            st.session_state[stress_key] = stress_pct
            
            # Calculer les ratios de levier pour chaque année
            df_resultats = calculer_ratio_levier_double_etape(
                bilan=bilan_stresse,
                postes_cibles=[poste],
                stress_pct=stress_pct,
                horizon=horizon,
                df_c4700=df_c4700,
                df_c01=df_c01
            )
            
            # Ajouter les résultats au tableau récapitulatif
            for _, row in df_resultats.iterrows():
                annee = row["Année"]
                recap_data.append({
                    "Année": annee,
                    "Fonds propres": row["Fonds propres"],
                    "Exposition totale": row["Exposition totale"],
                    "Ratio de levier (%)": row["Ratio de levier"],
                    "Poste": poste
                })
        
        # Créer le dataframe récapitulatif
        if recap_data:
            # Garder seulement une entrée par année (éviter les doublons)
            unique_recap = []
            for annee in annees:
                annee_data = [d for d in recap_data if d["Année"] == annee]
                if annee_data:
                    unique_recap.append(annee_data[0])
            
            # Afficher le tableau récapitulatif
            afficher_tableau_recapitulatif(unique_recap, "Levier")
        else:
            st.warning("Aucune donnée de ratio de levier disponible.")
        
    except Exception as e:
        st.error(f"Erreur lors du calcul du ratio de levier: {e}")
        import traceback
        st.error(traceback.format_exc())

def afficher_tableau_recapitulatif(recap_data, ratio_type):
    # Créer le dataframe récapitulatif selon le type de ratio
    if ratio_type == "LCR":
        recap_df = pd.DataFrame([{
            "Année": x["Année"],
            "HQLA": f"{x['HQLA']:,.2f}",
            "Inflows": f"{x['Inflows']:,.2f}",
            "Outflows": f"{x['Outflows']:,.2f}",
            f"{ratio_type} (%)": f"{x[f'{ratio_type} (%)']:.2f}%"
        } for x in recap_data])
    elif ratio_type == "NSFR":
        recap_df = pd.DataFrame([{
            "Année": x["Année"],
            "ASF": f"{x['ASF']:,.2f}",
            "RSF": f"{x['RSF']:,.2f}",
            f"{ratio_type} (%)": f"{x[f'{ratio_type} (%)']:.2f}%"
        } for x in recap_data])
    elif ratio_type == "Solvabilité":
        recap_df = pd.DataFrame([{
            "Année": x["Année"],
            "Fonds propres": f"{x['Fonds propres']:,.2f}",
            "RWA total": f"{x['RWA total']:,.2f}",
            f"Ratio de {ratio_type} (%)": f"{x['Ratio de solvabilité (%)']:.2f}%"
        } for x in recap_data])
    elif ratio_type == "Levier":
        recap_df = pd.DataFrame([{
            "Année": x["Année"],
            "Fonds propres": f"{x['Fonds propres']:,.2f}",
            "Exposition totale": f"{x['Exposition totale']:,.2f}",
            f"Ratio de {ratio_type} (%)": f"{x['Ratio de levier (%)']:.2f}%"
        } for x in recap_data])
    
    st.dataframe(recap_df, use_container_width=True)
    
    # Ajouter les dropdowns pour les détails par année
    for annee_data in recap_data:
        with st.expander(f"Détails de calcul {ratio_type} pour {annee_data['Année']}"):
            st.markdown(f"#### Année {annee_data['Année']}")
            
            if ratio_type == "LCR":
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("LCR", f"{annee_data['LCR (%)']:.2f}%")
                with col2:
                    st.metric("HQLA", format_large_number(annee_data['HQLA']))
                with col3:
                    st.metric("Outflows", format_large_number(annee_data['Outflows']))
                with col4:
                    st.metric("Inflows", format_large_number(annee_data['Inflows']))
                
                st.markdown("**Actifs liquides de haute qualité (HQLA)**")
                st.dataframe(affiche_LB_lcr(annee_data['df_72']), use_container_width=True)
                
                st.markdown("**Sorties de liquidités (Outflows)**")
                st.dataframe(affiche_outflow_lcr(annee_data['df_73']), use_container_width=True)
                
                st.markdown("**Entrées de liquidités (Inflows)**")
                st.dataframe(affiche_inflow_lcr(annee_data['df_74']), use_container_width=True)
            elif ratio_type == "NSFR":
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("NSFR", f"{annee_data['NSFR (%)']:.2f}%")
                with col2:
                    st.metric("ASF", format_large_number(annee_data['ASF']))
                with col3:
                    st.metric("RSF", format_large_number(annee_data['RSF']))
                
                st.markdown("**Available Stable Funding (ASF)**")
                st.dataframe(affiche_ASF(annee_data['df_81']), use_container_width=True)
                
                st.markdown("**Required Stable Funding (RSF)**")
                st.dataframe(affiche_RSF(annee_data['df_80']), use_container_width=True)
            elif ratio_type == "Solvabilité":
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ratio de Solvabilité", f"{annee_data['Ratio de solvabilité (%)']:.2f}%")
                with col2:
                    st.metric("Fonds propres", format_large_number(annee_data['Fonds propres']))
                with col3:
                    st.metric("RWA total", format_large_number(annee_data['RWA total']))
                
                # Vous pouvez ajouter des détails supplémentaires si disponibles
                st.markdown("**Note**: Pour plus de détails sur le calcul de solvabilité, consultez les logs d'exécution.")
            elif ratio_type == "Levier":
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Ratio de Levier", f"{annee_data['Ratio de levier (%)']:.2f}%")
                with col2:
                    st.metric("Fonds propres", format_large_number(annee_data['Fonds propres']))
                with col3:
                    st.metric("Exposition totale", format_large_number(annee_data['Exposition totale']))
                
                # Vous pouvez ajouter des détails supplémentaires si disponibles
                st.markdown("**Note**: Pour plus de détails sur le calcul du ratio de levier, consultez les logs d'exécution.")