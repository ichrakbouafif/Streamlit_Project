import streamlit as st
import pandas as pd

def format_number(x):
    """Format numbers without thousands separator and with 2 decimals"""
    if pd.isna(x) or x is None:
        return "N/A"
    return f"{x:,.2f}".replace(",", " ")

def create_lcr_table(resultats, horizon):
    annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
    data = {
        "Metric": [
            "Liquidity Buffer (HQLA)",
            "Total Outflows",
            "Total Inflows",
            "Net Liquidity Outflow",
            "LCR (%)"
        ]
    }
    
    for annee in annees:
        year_data = resultats.get(int(annee), {})
        data[annee] = [
            year_data.get("HQLA", None),
            year_data.get("OUTFLOWS", None),
            year_data.get("INFLOWS", None),
            year_data.get("OUTFLOWS", 0) - year_data.get("INFLOWS", 0) 
            if year_data.get("OUTFLOWS") is not None and year_data.get("INFLOWS") is not None 
            else None,
            f"{year_data.get('LCR', 0)*100:.2f}%" if year_data.get('LCR') is not None else "N/A"
        ]
    
    return pd.DataFrame(data)

def create_nsfr_table(resultats, horizon):
    annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
    data = {
        "Metric": [
            "ASF",
            "RSF",
            "NSFR (%)"
        ]
    }
    
    for annee in annees:
        year_data = resultats.get(int(annee), {})
        data[annee] = [
            year_data.get("ASF", None),
            year_data.get("RSF", None),
            f"{year_data.get('NSFR', 0):.2f}%" if year_data.get('NSFR') is not None else "N/A"
        ]
    
    return pd.DataFrame(data)

def display_tab_content(resultats, horizon, tab):
    if not resultats:
        tab.warning("Aucune donnée disponible")
        return
    
    
    st.subheader("Ratio LCR")
    lcr_table = create_lcr_table(resultats, horizon)
    if not lcr_table.empty:
    # Apply custom formatting to numeric columns
        formatted_table = lcr_table.copy()
        for col in formatted_table.columns[1:]:  # Skip first column (Metric)
                formatted_table[col] = formatted_table[col].apply(
                    lambda x: format_number(x) if not isinstance(x, str) and x != "N/A" else x
                )
        st.dataframe(
                formatted_table,
                use_container_width=True,
                hide_index=True
            )
    else:
            st.warning("Aucune donnée LCR disponible")
    

    st.subheader("Ratio NSFR")
    nsfr_table = create_nsfr_table(resultats, horizon)
    if not nsfr_table.empty:
            # Apply custom formatting to numeric columns
            formatted_table = nsfr_table.copy()
            for col in formatted_table.columns[1:]:  # Skip first column (Metric)
                formatted_table[col] = formatted_table[col].apply(
                    lambda x: format_number(x) if not isinstance(x, str) and x != "N/A" else x
                )
            st.dataframe(
                formatted_table,
                use_container_width=True,
                hide_index=True
            )
    else:
            st.warning("Aucune donnée NSFR disponible")

def show():
    st.title("Résultats et Graphiques")
    st.write("Visualisez les résultats du test de stress et les graphiques comparatifs.")

    # Récupération des résultats depuis le session_state
    horizon = st.session_state.get('horizon_global', 3)
    proj = st.session_state.get('resultats_ratios_liquidité_projete', {})
    sim1 = st.session_state.get('resultats_sim1', {})
    sim2 = st.session_state.get('resultats_sim2', {})
    sim3 = st.session_state.get('resultats_sim3', {})

    # Création des onglets - Récapitulatif en premier
    tab5, tab1, tab2, tab3, tab4 = st.tabs([
        "Récapitulatif",
        "Ratios projetés",
        "Phase 1 (Sim1)",
        "Phase 2 (Sim2)",
        "Phase 3 (Sim3)"
    ])

    with tab5:
        st.subheader("Comparaison des ratios")
        
        if not proj:
            st.warning("Aucune donnée disponible pour le récapitulatif")
            return

        annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
        
        # Tableau comparatif LCR - Années en colonnes
        st.markdown("**Comparaison des ratios LCR (%)**")
        lcr_data = {
            "Scenario": ["Projeté", "Sim1", "Sim2", "Sim3"]
        }
        
        for annee in annees:
            lcr_data[annee] = [
                f"{proj.get(int(annee), {}).get('LCR', 0)*100:.2f}%" if proj.get(int(annee), {}).get('LCR') is not None else "N/A",
                f"{sim1.get(int(annee), {}).get('LCR', 0)*100:.2f}%" if sim1.get(int(annee), {}).get('LCR') is not None else "N/A",
                f"{sim2.get(int(annee), {}).get('LCR', 0)*100:.2f}%" if sim2.get(int(annee), {}).get('LCR') is not None else "N/A",
                f"{sim3.get(int(annee), {}).get('LCR', 0)*100:.2f}%" if sim3.get(int(annee), {}).get('LCR') is not None else "N/A"
            ]
        
        lcr_df = pd.DataFrame(lcr_data)
        st.dataframe(lcr_df.set_index("Scenario"), use_container_width=True)
        
        # Tableau comparatif NSFR - Années en colonnes
        st.markdown("**Comparaison des ratios NSFR (%)**")
        nsfr_data = {
            "Scenario": ["Projeté", "Sim1", "Sim2", "Sim3"]
        }
        
        for annee in annees:
            nsfr_data[annee] = [
                f"{proj.get(int(annee), {}).get('NSFR', 0):.2f}%" if proj.get(int(annee), {}).get('NSFR') is not None else "N/A",
                f"{sim1.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim1.get(int(annee), {}).get('NSFR') is not None else "N/A",
                f"{sim2.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim2.get(int(annee), {}).get('NSFR') is not None else "N/A",
                f"{sim3.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim3.get(int(annee), {}).get('NSFR') is not None else "N/A"
            ]
        
        nsfr_df = pd.DataFrame(nsfr_data)
        st.dataframe(nsfr_df.set_index("Scenario"), use_container_width=True)

    with tab1:
        st.subheader("Résultats des ratios projetés")
        display_tab_content(proj, horizon, st)

    with tab2:
        st.subheader("Résultats Phase 1 (Sim1)")
        display_tab_content(sim1, horizon, st)

    with tab3:
        st.subheader("Résultats Phase 2 (Sim2)")
        display_tab_content(sim2, horizon, st)

    with tab4:
        st.subheader("Résultats Phase 3 (Sim3)")
        display_tab_content(sim3, horizon, st)