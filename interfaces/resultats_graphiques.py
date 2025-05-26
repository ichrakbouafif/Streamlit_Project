import streamlit as st
import pandas as pd

def formater_tableau(resultats):
    lignes = []
    annees = list(resultats.keys())

    for annee in annees:
        data = resultats[annee]
        ligne = {
            "Année": annee,
            "Liquidity Buffer": data.get("liquidity_buffer", 0),
            "Total Outflows": data.get("total_outflows", 0),
            "Inflows (75% cap)": data.get("inflows_cap", 0),
            "Net Liquidity Outflows": data.get("net_liquidity_outflows", 0),
            "LCR": data.get("lcr_ratio", 0),
            "ASF": data.get("asf", 0),
            "RSF": data.get("rsf", 0),
            "NSFR": data.get("nsfr_ratio", 0)
        }
        lignes.append(ligne)

    return pd.DataFrame(lignes).set_index("Année")


def show():
    st.title("Résultats et Graphiques")
    st.write("Visualisez les résultats du test de stress et les graphiques comparatifs.")

    if st.button("Générer les graphiques"):
        st.success("Graphiques générés avec succès.")

    # Récupération des résultats depuis le session_state
    proj = st.session_state.get('resultats_ratios_liquidité_projete')
    sim1 = st.session_state.get('resultats_horizon', proj)
    sim2 = st.session_state.get('resultats_horizon', proj)
    sim3 = st.session_state.get('resultats_horizon', proj)

    if proj is None:
        st.warning("Les résultats projetés ne sont pas encore disponibles.")
        return

    # Création des onglets
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Ratios projetés",
        "Phase 1 (Sim1)",
        "Phase 2 (Sim2)",
        "Phase 3 (Sim3)",
        "Récapitulatif"
    ])

    with tab1:
        st.subheader("Résultats des ratios projetés")
        st.dataframe(formater_tableau(proj), use_container_width=True)

    with tab2:
        st.subheader("Résultats Phase 1 (Sim1)")
        st.dataframe(formater_tableau(sim1), use_container_width=True)

    with tab3:
        st.subheader("Résultats Phase 2 (Sim2)")
        st.dataframe(formater_tableau(sim2), use_container_width=True)

    with tab4:
        st.subheader("Résultats Phase 3 (Sim3)")
        st.dataframe(formater_tableau(sim3), use_container_width=True)

    with tab5:
        st.subheader("Comparaison des ratios LCR & NSFR")

        recap_data = []
        annees = list(proj.keys())
        for annee in annees:
            recap_data.append({
                "Année": annee,
                "LCR Projeté": proj[annee].get("lcr_ratio", 0),
                "LCR Sim1": sim1[annee].get("lcr_ratio", 0),
                "LCR Sim2": sim2[annee].get("lcr_ratio", 0),
                "LCR Sim3": sim3[annee].get("lcr_ratio", 0),
                "NSFR Projeté": proj[annee].get("nsfr_ratio", 0),
                "NSFR Sim1": sim1[annee].get("nsfr_ratio", 0),
                "NSFR Sim2": sim2[annee].get("nsfr_ratio", 0),
                "NSFR Sim3": sim3[annee].get("nsfr_ratio", 0),
            })

        df_recap = pd.DataFrame(recap_data).set_index("Année")
        st.dataframe(df_recap, use_container_width=True)
