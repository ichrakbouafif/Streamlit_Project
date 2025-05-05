from backend.solvabilite.calcul_ratios_capital_stressé import calculer_ratios_solva_double_etape, charger_donnees
from backend.levier.calcul_ratio_levier import charger_donnees_levier, calculer_ratio_levier_double_etape

import streamlit as st
import config
import pandas as pd

# --- Mapping du type de variable ---
type_variables = {
    "Dépôts et avoirs de la clientèle": "Passif",
    "Créances sur la clientèle": "Actif",
    "Provisions pour pertes sur prêts": "Capitaux propres",
    "Résultat consolidé": "Capitaux propres",
    "Capital social": "Capitaux propres",
    "Emprunts et ressources spéciales": "Passif",
    "Valeurs immobilisées": "Actif",
    "Portefeuille": "Actif",
    "Provisions pour pertes sur titres": "Capitaux propres",
    "Réserves consolidées": "Capitaux propres",
    "Créances banques autres": "Actif",
    "Autres passifs": "Passif"
}

def show():
   
    if "scenario_phase" not in st.session_state:
        st.session_state.scenario_phase = "initial"
        st.session_state.scenario_type_1 = None
        st.session_state.scenario_type_2 = None
        st.session_state.events_type_1 = []
        st.session_state.events_type_2 = []
        st.session_state.validation_autorisee = True

    phase = st.session_state.scenario_phase

    if phase == "initial":
        st.subheader("Phase 1 : Sélection du premier scénario")
        type_scenario = st.radio("Type de scénario à calibrer", ["Scénario Idiosyncratique", "Scénario Macroéconomique"])
        scenario_type = "idiosyncratique" if "Idiosyncratique" in type_scenario else "macroéconomique"
        st.session_state.scenario_type_1 = scenario_type
        st.session_state.scenario_type_2 = "macroéconomique" if scenario_type == "idiosyncratique" else "idiosyncratique"

    elif phase == "secondaire":
        scenario_type = st.session_state.scenario_type_2
        st.subheader(f"Phase 2 : Scénario complémentaire ({scenario_type.capitalize()})")

    else:
        scenario_type = "combiné"
        st.subheader("Phase finale : Scénario combiné")
        st.markdown("### Événements combinés sélectionnés :")
        events = st.session_state.get("events_type_1", []) + st.session_state.get("events_type_2", [])
        for e in events:
            st.markdown(f"- {e}")
        events_dict = {}
        for e in events:
            for t in ["idiosyncratique", "macroéconomique"]:
                if e in config.scenarios.get(t, {}):
                    events_dict[e] = config.scenarios[t][e]
                    break
        evenements_choisis = events

    if scenario_type != "combiné":
        events = list(config.scenarios[scenario_type].keys())
        events_dict = config.scenarios[scenario_type]
        evenements_choisis = st.multiselect("Événements disponibles", events, key=f"events_{scenario_type}")
        if not evenements_choisis:
            st.info("Veuillez sélectionner au moins un événement.")
            return

    st.markdown("---")
    afficher_calibrage_evenements(events_dict, evenements_choisis, scenario_type, phase)

    if st.button("Valider ce scénario"):
        if not st.session_state.get("validation_autorisee", True):
            st.warning("Impossible de valider tant que toutes les contreparties ne sont pas correctement équilibrées.")
            return

        if phase == "initial":
            st.session_state.events_type_1 = evenements_choisis
            st.session_state.scenario_phase = "secondaire"
            st.rerun()
        elif phase == "secondaire":
            st.session_state.events_type_2 = evenements_choisis
            st.session_state.scenario_phase = "combine"
            st.rerun()
        else:
            st.success("Simulation 1 complète. Vous pouvez passer à l'étape suivante.")
            # Set session state to navigate to the "Résultats & Graphiques" page
            st.session_state.selected_page = "Résultats & Graphiques"

def afficher_ajustement_variable(var, evenement):
    st.number_input(
        f"Stress appliqué à cette variable (%)",
        min_value=-100,
        max_value=100,
        value=0,
        step=1,
        key=f"{evenement}_{var}"
    )

def afficher_contreparties(var, evenement):
    st.markdown("Contreparties impactées :")
    contreparties = config.contreparties[var]

    total = 0
    ajustement = st.session_state.get(f"{evenement}_{var}", 0)
    valide = True

    for cp in contreparties:
        type_cp = type_variables.get(cp, "Inconnu")
        st.markdown(f"**{type_cp.upper()} – {cp} (%)**")

        val = st.number_input(
            label="",
            min_value=-100,
            max_value=100,
            value=0,
            step=1,
            key=f"{evenement}_{var}_{cp}"
        )
        total += val

    if total != ajustement:
        st.error(f"La somme des contreparties ({total}%) doit être égale à l'ajustement principal ({ajustement}%).")
        valide = False

    return valide

def afficher_corep_separe(var, source="Variable principale"):
    corep_cap = config.corep_capital_mapping.get(var, {})
    corep_liq = config.corep_liquidite_mapping.get(var, {})

    lignes_capital = []
    lignes_liquidite = []

    if "Solvabilité" in corep_cap:
        for rubrique in corep_cap["Solvabilité"]:
            lignes_capital.append({
                "Type COREP": "Solvabilité (C0100)",
                "Rubrique": rubrique,
                "Source": source
            })
    if "Levier" in corep_cap:
        for rubrique in corep_cap["Levier"]:
            lignes_capital.append({
                "Type COREP": "Levier (C43)",
                "Rubrique": rubrique,
                "Source": source
            })

    if "LCR" in corep_liq:
        for rubrique in corep_liq["LCR"]:
            lignes_liquidite.append({
                "Type COREP": "LCR (C72)",
                "Rubrique": rubrique,
                "Source": source
            })
    if "NSFR" in corep_liq:
        for rubrique in corep_liq["NSFR"]:
            lignes_liquidite.append({
                "Type COREP": "NSFR (C73)",
                "Rubrique": rubrique,
                "Source": source
            })

    if lignes_capital:
        st.markdown(f"<div style='font-weight:bold; font-size:16px; color:#003366;'>Rubriques COREP – Capital liées à : {var}</div>", unsafe_allow_html=True)
        st.table(pd.DataFrame(lignes_capital))

    if lignes_liquidite:
        st.markdown(f"<div style='font-weight:bold; font-size:16px; color:#005050;'>Rubriques COREP – Liquidité liées à : {var}</div>", unsafe_allow_html=True)
        st.table(pd.DataFrame(lignes_liquidite))

def afficher_calibrage_evenements(events_dict, evenements_choisis, scenario_type, phase):
    global_valide = True

    for evenement in evenements_choisis:
        st.markdown(f"### Événement : {evenement}")
        variables = events_dict[evenement]

        # ✅ Horizon par événement
        st.number_input(
            "Horizon d'impact pour cet événement (en années)",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            key=f"{evenement}_horizon"
        )

        for var in variables:
            type_var = type_variables.get(var, "Inconnu")
            st.markdown(f"**{type_var.upper()} – {var} (% du bilan de référence)**")

            afficher_ajustement_variable(var, evenement)
            contreparties_valides = afficher_contreparties(var, evenement)
            afficher_corep_separe(var, source="Variable principale")

            for cp in config.contreparties.get(var, []):
                type_cp = type_variables.get(cp, "Inconnu")
                afficher_corep_separe(cp, source=f"Contrepartie ({type_cp.upper()})")

            if not contreparties_valides:
                global_valide = False

            st.markdown("---")

    st.session_state["validation_autorisee"] = global_valide

    # ✅ Affichage automatique pour "Retrait massif des dépôts"
    for evenement in evenements_choisis:
        if evenement == "Retrait massif des dépôts":
            variable_principale = "Dépôts et avoirs de la clientèle"
            postes_cibles = ["Créances banques autres", "Portefeuille"]
            stress_pct = st.session_state.get(f"{evenement}_{variable_principale}", 0)
            horizon = st.session_state.get(f"{evenement}_horizon", 3)

            # Récupérer les stress appliqués à chaque contrepartie
            stress_values = {}
            for poste in postes_cibles:
                stress_values[poste] = st.session_state.get(f"{evenement}_{variable_principale}_{poste}", 0)
           
            stress_total = sum(stress_values.values())
           
            if stress_total != 0 and global_valide:
                st.markdown(f"### 📌 Stress appliqué : <span style='color:green;'>{stress_total}%</span> | Horizon : <span style='color:green;'>{horizon}</span>", unsafe_allow_html=True)
               
                # Détail des stress par poste
                for poste, valeur in stress_values.items():
                    if valeur != 0:
                        st.markdown(f"- {poste}: <span style='color:blue;'>{valeur}%</span>", unsafe_allow_html=True)

                try:
                    # === CALCUL DU RATIO DE SOLVABILITÉ ===
                    st.markdown("## Ratio de Solvabilité")
                    try:
                        bilan, df_c01, df_c02, df_bloc = charger_donnees()
                       
                        # Afficher les valeurs clés pour le débogage
                        #with st.expander("Valeurs de débogage - Solvabilité"):
                         #   st.markdown(f"- **Fonds propres (C0100, ligne 20):** {df_c01.loc[df_c01['row'] == 20, '0010'].values[0]:,.0f}")
                          #  st.markdown(f"- **RWA Total initial (C0200, ligne 10):** {df_c02.loc[df_c02['row'] == 10, '0010'].values[0]:,.0f}")
                           # st.markdown(f"- **RWA Bloc initial (C0700):** {df_bloc[df_bloc['row'].isin([70.0, 80.0, 110.0])]['0220'].sum():,.0f}")
                           
                            # Afficher les valeurs de la ligne 70 du bloc institutionnel avant stress
                            #ligne_70 = df_bloc[df_bloc['row'] == 70.0]
                            #if not ligne_70.empty:
                             #  st.markdown(f"- **Ligne 70.0 (on-balance) valeur initiale:** {ligne_70['0010'].values[0]:,.0f}")
                              #  st.markdown(f"- **Ligne 70.0 RWA initial:** {ligne_70['0220'].values[0]:,.0f}")
                       
                        # Pour chaque contrepartie impactée, calculer l'effet sur le ratio de solvabilité
                        # Pour simplifier, nous allons seulement considérer le poste "Créances banques autres"
                        poste_cible = "Créances banques autres"
                        stress_pct_solva = stress_values.get(poste_cible, 0)
                       
                        df_ratios = calculer_ratios_solva_double_etape(
                            bilan=bilan,
                            poste_cible=poste_cible,
                            stress_pct=stress_pct_solva,
                            horizon=horizon,
                            df_bloc_base=df_bloc,
                            df_c01=df_c01,
                            df_c02=df_c02
                        )
                       
                        st.markdown("### Ratio de solvabilité simulé")
                        st.dataframe(df_ratios.style.format({
                            "Fonds propres": "{:,.0f}",
                            "RWA total": "{:,.0f}",
                            "Ratio de solvabilité": "{:.4f} %"
                        }))
                    except Exception as e:
                        st.error(f"❌ Erreur dans le calcul du ratio de solvabilité : {e}")
                        import traceback
                        st.code(traceback.format_exc(), language="python")
               
                    # === CALCUL DU RATIO DE LEVIER ===
                    st.markdown("## Ratio de Levier")
                    try:
                        # Charger les données pour le ratio de levier
                        bilan_levier, df_c01_levier, df_c4700 = charger_donnees_levier()
                       
                        # Afficher les valeurs clés pour le débogage
                        #with st.expander("Valeurs de débogage - Levier"):
                         #   st.markdown(f"- **Fonds propres (C0100, ligne 20):** {df_c01_levier.loc[df_c01_levier['row'] == 20, '0010'].values[0]:,.0f}")
                          #  st.markdown(f"- **Exposition totale initiale:** {df_c4700['Amount'].sum():,.0f}")
                            # Trouver la ligne 'Other assets' (ligne 190)
                        #ligne_190 = df_c4700[df_c4700['Row'] == 190]
                        #if not ligne_190.empty:
                                #st.markdown(f"- **Ligne 190 (Other assets) valeur initiale:** {ligne_190['Amount'].values[0]:,.0f}")
                           
                            # Valeurs initiales des postes cibles dans le bilan
                        #for poste in postes_cibles:
                         #       indice_poste = bilan_levier[bilan_levier["Poste du Bilan"] == poste].index
                          #      if not indice_poste.empty:
                           #         valeur = bilan_levier.loc[indice_poste[0], "2024"]
                            #        st.markdown(f"- **Valeur initiale '{poste}':** {valeur:,.0f}")
                       
                        # Utiliser la fonction corrigée pour calculer le ratio de levier
                        df_levier = calculer_ratio_levier_double_etape(
                            bilan=bilan_levier,
                            postes_cibles=postes_cibles,  # Liste des postes à stresser
                            stress_pct=stress_pct,  # Stress total (pour référence seulement)
                            horizon=horizon,
                            df_c4700=df_c4700,
                            df_c01=df_c01_levier
                        )
                       
                        st.markdown("### Ratio de levier simulé")
                        st.dataframe(df_levier.style.format({
                            "Fonds propres": "{:,.0f}",
                            "Exposition totale": "{:,.0f}",
                            "Ratio de levier": "{:.4f} %"
                        }))
                    except Exception as e:
                        st.error(f"❌ Erreur dans le calcul du ratio de levier : {e}")
                        import traceback
                        st.code(traceback.format_exc(), language="python")
               
                except Exception as e:
                   st.error(f"❌ Erreur capturée pendant le test : {e}")
                   import traceback
                   st.code(traceback.format_exc(), language="python")