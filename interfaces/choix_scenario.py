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
    "Portefeuille-titres commercial": "Actif",
    "Valeurs immobilisées": "Actif",
    "Portefeuille d’investissement immobilier": "Actif",
    "Portefeuille d’investissement": "Actif",
    "Provisions pour pertes sur titres": "Capitaux propres",
    "Réserves consolidées": "Capitaux propres",
    "Créances sur les établissements bancaires et financiers": "Actif",
    "Autres passifs": "Passif"
}

def show():
    st.title("Choix des scénarios")

     # Initialisation de l'horizon d'impact (fixé une seule fois)
    if "horizon_impact" not in st.session_state:
        st.session_state.horizon_impact = st.number_input(
            "Horizon d'impact (en années)", min_value=1, max_value=36, value=3, step=1
        )
    else:
        st.markdown(f"**Horizon d'impact choisi :** {st.session_state.horizon_impact} années")


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
            st.success("Simulation 1 complète. Vous pouvez passer à l’étape suivante.")
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
        st.error(f"La somme des contreparties ({total}%) doit être égale à l’ajustement principal ({ajustement}%).")
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
                "Type COREP": "Solvabilité (C01)",
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

