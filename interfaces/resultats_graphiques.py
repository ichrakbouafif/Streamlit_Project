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
            "LCR (%)"
        ]
    }
    
    for annee in annees:
        year_data = resultats.get(int(annee), {})
        data[annee] = [
            year_data.get("HQLA", None),
            year_data.get("Outflows", None),
            year_data.get("Inflows", None),
            year_data.get('LCR (%)', 0)
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
            year_data.get('NSFR (%)', 0)
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

    horizon = st.session_state.get('horizon_global', 3)
    proj = st.session_state.get('resultats_ratios_liquidité_projete', {})
    sim1 = st.session_state.get('resultats_phase1', {})
    sim2 = st.session_state.get('resultats_phase2', {})
    sim3 = st.session_state.get('resultats_phase3', {})  

    tab5, tab1, tab2, tab3, tab4 = st.tabs([
        "Récapitulatif",
        "Ratios projetés",
        "Phase 1",
        "Phase 2",
        "Phase 3"
    ])

    with tab5:
        st.subheader("Comparaison des ratios LCR (%)")
        annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
        lcr_data = {
            "Scenario": ["Projeté", "Phase 1", "Phase 2", "Phase 3"]
        }

        for annee in annees:
            lcr_data[annee] = [
                f"{proj.get(int(annee), {}).get('LCR (%)', 0):.2f}%" if proj.get(int(annee), {}).get('LCR (%)') is not None else "N/A",
                f"{sim1.get(int(annee), {}).get('LCR (%)', 0):.2f}%" if sim1.get(int(annee), {}).get('LCR (%)') is not None else "N/A",
                f"{sim2.get(int(annee), {}).get('LCR (%)', 0):.2f}%" if sim2.get(int(annee), {}).get('LCR (%)') is not None else "N/A",
                f"{sim3.get(int(annee), {}).get('LCR (%)', 0):.2f}%" if sim3.get(int(annee), {}).get('LCR (%)') is not None else "N/A"
            ]
        
        lcr_df = pd.DataFrame(lcr_data)
        st.dataframe(lcr_df, use_container_width=True)

    with tab1:
        display_tab_content(proj, horizon, tab1)

    with tab2:
        display_tab_content(sim1, horizon, tab2)

    with tab3:
        display_tab_content(sim2, horizon, tab3)

    with tab4:
        display_tab_content(sim3, horizon, tab4)
