import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import format_large_number
from backend.stress_test import event1 as bst
from backend.ratios_baseline.ratios_baseline import calcul_ratios_sur_horizon
from backend.ratios_baseline.ratios_baseline import charger_bilan

# PwC Color Palette
PWC_ORANGE = "#f47721"
PWC_DARK_GRAY = "#3d3d3d"
PWC_LIGHT_BEIGE = "#f5f0e6"
PWC_BROWN = "#6e4c1e"
PWC_SOFT_BLACK = "#2c2c2c"
PWC_DARK_ORANGE = "#d04a02"
PWC_LIGHT_BLUE = "#FFCDA8"
PWC_LIGHT_GRAY = "#f5f0e6"

# Custom styling
def apply_custom_styles():
    st.markdown(f"""
    <style>
        /* Table styling */
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            font-family: Arial, sans-serif;
        }}
        
        td {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            text-align: right;
        }}
        /* Metric cards */
        .metric-card {{
            background-color: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid {PWC_ORANGE};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab"] {{
            background: white;
            color: {PWC_DARK_GRAY};
            border: 1px solid #ddd;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            padding: 8px 16px;
            margin-right: 5px;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {PWC_ORANGE} !important;
            color: white !important;
            border-color: {PWC_ORANGE};
        }}
        
        /* Button styling */
        .stButton button {{
            background-color: {PWC_ORANGE};
            color: white;
            border-radius: 4px;
            border: none;
            padding: 8px 16px;
            transition: background-color 0.3s;
        }}
        
        .stButton button:hover {{
            background-color: {PWC_DARK_ORANGE};
            color: white;
        }}
        
        /* Slider styling */
        .stSlider {{
            width: 100%;
        }}
        
        .stSlider [data-baseweb="slider"] {{
            padding: 10px 0;
        }}
    </style>
    """, unsafe_allow_html=True)

def style_table(df, highlight_columns=None):
    """
    Stylise un tableau avec les couleurs PwC et formate les nombres.
    """
    # Couleurs PwC
    pwc_orange = "#d04a02"
    pwc_dark_blue = "#FFCDA8"
    pwc_light_gray = "#f5f0e6"

    # Appliquer le format à toutes les colonnes numériques
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].apply(format_large_number)

    # Convertir tout en string (utile pour la sécurité de l'affichage HTML)
    df = df.astype(str)

    # Style de base du tableau
    table_styles = [
        {"selector": "thead th", "props": f"background-color: {pwc_dark_blue}; color: black; font-weight: bold; text-align: center; padding: 8px;"},
        {"selector": "tbody td", "props": "padding: 6px; text-align: right;"},
        {"selector": "tbody tr:nth-child(odd) td", "props": f"background-color: {pwc_light_gray};"},
        {"selector": "tbody td:first-child", "props": "text-align: center; font-weight: bold;"},
        {"selector": "tbody td:nth-child(2)", "props": "text-align: left;"},
        {"selector": "table", "props": "width: 100%; border-collapse: collapse; font-size: 14px;"},
        {"selector": "th, td", "props": "border: 1px solid #ddd;"}
    ]

    # Appliquer les styles
    styled_df = df.style.set_table_styles(table_styles)

    # Mettre en évidence les colonnes spécifiées
    if highlight_columns:
        for col in highlight_columns:
            if col in df.columns:
                styled_df = styled_df.set_properties(**{
                    'font-weight': 'bold',
                    'color': pwc_orange
                }, subset=[col])

    return styled_df


def format_number(x):
    """Format numbers without thousands separator and with 2 decimals"""
    if pd.isna(x) or x is None:
        return "N/A"
    return f"{x:,.2f}".replace(",", " ")


def create_lcr_table(resultats, horizon):
    annees = [str(2024 + i) for i in range(horizon + 1)]
    data = {
        " ": [
            "Liquidity Buffer (HQLA)",
            "Total Outflows",
            "Total Inflows",
            "LCR (%)"
        ]
    }
    
    for annee in annees:
        year_data = resultats.get(int(annee), {})
        data[annee] = [
            year_data.get("HQLA"),
            year_data.get("OUTFLOWS"),
            year_data.get("INFLOWS"),
            year_data.get("LCR", 0)
        ]
    
    return pd.DataFrame(data)

def create_nsfr_table(resultats, horizon):
    annees = [str(2024 + i) for i in range(horizon + 1)]
    data = {
        " ": ["ASF", "RSF", "NSFR (%)"]
    }
    
    for annee in annees:
        year_data = resultats.get(int(annee), {})
        data[annee] = [
            year_data.get("ASF"),
            year_data.get("RSF"),
            year_data.get("NSFR", 0)
        ]
    
    return pd.DataFrame(data)

def create_comparison_data(proj, sim1, sim2, sim3, horizon, metric):
    """Create dataframe for comparison charts"""
    years = list(range(2024, 2024 + horizon + 1))
    data = []
    
    for year in years:
        data.append({
            "Year": year,
            "Scenario": "Projeté",
            "Value": proj.get(year, {}).get(metric, 0)
        })
        data.append({
            "Year": year,
            "Scenario": "Phase 1",
            "Value": sim1.get(year, {}).get(metric, 0)
        })
        data.append({
            "Year": year,
            "Scenario": "Phase 2",
            "Value": sim2.get(year, {}).get(metric, 0)
        })
        data.append({
            "Year": year,
            "Scenario": "Phase 3",
            "Value": sim3.get(year, {}).get(metric, 0)
        })
    
    return pd.DataFrame(data)

def plot_metric_comparison(df, title, threshold=None):
    """Create interactive comparison plot with PwC colors"""
    scenario_colors = {
        "Projeté": PWC_DARK_GRAY,
        "Phase 1": PWC_ORANGE,
        "Phase 2": PWC_DARK_ORANGE,
        "Phase 3": PWC_BROWN
    }
    
    fig = go.Figure()
    
    for scenario in df["Scenario"].unique():
        scenario_df = df[df["Scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=scenario_df["Year"],
            y=scenario_df["Value"],
            name=scenario,
            line=dict(color=scenario_colors[scenario], width=3),
            mode='lines+markers',
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', 
                  font=dict(size=16, color=PWC_DARK_GRAY)),
        xaxis=dict(title="Année", gridcolor="#f0f0f0"),
        yaxis=dict(title="Valeur (%)", gridcolor="#f0f0f0"),
        plot_bgcolor='white',
        paper_bgcolor='white',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=400
    )
    
    if threshold:
        fig.add_hline(y=threshold, line_dash="dot", 
                     annotation_text=f"Seuil minimum: {threshold}%", 
                     line_color="red")
    
    return fig

# Couleurs PwC alternatives
PWC_ORANGE = "#f47721"
PWC_DARK_ORANGE = "#c74b0e"
PWC_LIGHT_GRAY = "#bfbfbf"      # Remplace le dark gray
PWC_LIGHT_BROWN = "#a65e2e"     # Remplace le brown

def plot_components_comparison(proj, sim1, sim2, sim3, horizon, components, title):
    """Plot comparison of LCR/NSFR components with improved PwC colors"""
    years = list(range(2025, 2025 + horizon))
    scenarios = ["Projeté", "Phase 1", "Phase 2", "Phase 3"]
    scenario_colors = {
        "Projeté": PWC_LIGHT_GRAY,
        "Phase 1": PWC_ORANGE,
        "Phase 2": PWC_DARK_ORANGE,
        "Phase 3": PWC_LIGHT_BROWN
    }
    
    data = []
    
    for scenario, results in zip(scenarios, [proj, sim1, sim2, sim3]):
        for year in years:
            year_data = results.get(year, {})
            for component in components:
                data.append({
                    "Année": year,
                    "Scénario": scenario,
                    "Composant": component,
                    "Valeur": year_data.get(component, 0),
                    "Couleur": scenario_colors[scenario]
                })
    
    df = pd.DataFrame(data)

    fig = px.bar(df, x="Année", y="Valeur", color="Scénario",
                 facet_col="Composant",
                 title=title,
                 template="plotly_white",
                 color_discrete_map=scenario_colors,
                 barmode="group")
    
    fig.update_layout(
        height=400,
        showlegend=True,
        xaxis_title="Année",
        yaxis_title="Valeur"
    )
    
    return fig



def display_tab_content(resultats, horizon, tab, scenario_name):
    if not resultats:
        tab.warning("Aucune donnée disponible")
        return

    with tab:
        # Display key metrics at the top
        col1, col2 = st.columns(2)
        with col1:
            last_year = str(2024 + horizon)
            lcr_value = resultats.get(int(last_year), {}).get("LCR", 0)
            st.markdown(
                                f"""
                                <div style="background-color:{PWC_LIGHT_BEIGE}; padding:20px; border-radius:15px;
                                            box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {PWC_ORANGE}">
                                    <h4 style="color:{PWC_SOFT_BLACK}; margin-bottom:10px;">LCR Final ({last_year})</h4>
                                    <p style="font-size:26px; font-weight:bold; color:{PWC_ORANGE}; margin:0;">
                                        {lcr_value:.2f}%
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        
        with col2:
            nsfr_value = resultats.get(int(last_year), {}).get("NSFR", 0)
            st.markdown(
                                f"""
                                <div style="background-color:{PWC_LIGHT_BEIGE}; padding:20px; border-radius:15px;
                                            box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {PWC_ORANGE}">
                                    <h4 style="color:{PWC_SOFT_BLACK}; margin-bottom:10px;">NSFR Final ({last_year})</h4>
                                    <p style="font-size:26px; font-weight:bold; color:{PWC_ORANGE}; margin:0;">
                                        {nsfr_value:.2f}%
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        st.subheader(f"  ")
        st.subheader(f"Évolution des ratios LCR et NSFR - {scenario_name}")

        # Prepare data for combined chart
        years = list(range(2024, 2024 + horizon + 1))
        lcr_values = [resultats.get(year, {}).get("LCR", 0) for year in years]
        nsfr_values = [resultats.get(year, {}).get("NSFR", 0) for year in years]

        # Create combined line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=lcr_values, mode='lines+markers', name='LCR',
            line=dict(color=PWC_ORANGE, width=3)
        ))
        fig.add_trace(go.Scatter(
            x=years, y=nsfr_values, mode='lines+markers', name='NSFR',
            line=dict(color=PWC_DARK_GRAY, width=3)
        ))
        fig.add_hline(y=100, line_dash="dot", line_color="red",
                      annotation_text="Seuil minimum 100%", annotation_position="top left")
        fig.update_layout(
            xaxis_title="Année",
            yaxis_title="Ratio (%)",
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader(f"Ratio LCR - {scenario_name}")
        lcr_table = create_lcr_table(resultats, horizon)
        if not lcr_table.empty:            
            # Display styled LCR table
            lcr_df = style_table(lcr_table, highlight_columns=[" "])
            st.markdown(lcr_df.to_html(), unsafe_allow_html=True)
        else:
            st.warning("Aucune donnée LCR disponible")

        st.subheader(f"Ratio NSFR - {scenario_name}")
        nsfr_table = create_nsfr_table(resultats, horizon)
        if not nsfr_table.empty:
            # Display styled NSFR table
            nsfr_df = style_table(nsfr_table, highlight_columns=[" "])
            st.markdown(nsfr_df.to_html(index=False), unsafe_allow_html=True)
        else:
            st.warning("Aucune donnée NSFR disponible")



def calculate_projected_ratios(horizon):
    """Recalculate projected liquidity ratios"""
    bilan = charger_bilan()
    df_72, df_73, df_74 = bst.charger_lcr()
    df_80, df_81 = bst.charger_nsfr()
    return calcul_ratios_sur_horizon(horizon, bilan, df_72, df_73, df_74, df_80, df_81)

def show():



    apply_custom_styles()
    st.title("Résultats et Graphiques")
    st.write("Visualisez les résultats du test de stress et les graphiques comparatifs.")

    horizon = st.session_state.get('horizon_global', 3)
    
    # Recalculate projected ratios if not available or invalid
    st.session_state['resultats_ratios_liquidite_projete'] = calculate_projected_ratios(horizon)
    
    # Get all results
    proj = st.session_state.get('resultats_ratios_liquidite_projete', {})
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

    # TAB 5 — Récapitulatif
    with tab5:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Comparaison des ratios LCR (%)")
            annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
            lcr_data = {
                "Scenario": ["Projeté", "Phase 1", "Phase 2", "Phase 3"]
            }

            for annee in annees:
                lcr_data[annee] = [
                    f"{proj.get(int(annee), {}).get('LCR', 0):.2f}%" if proj.get(int(annee), {}).get('LCR') is not None else "N/A",
                    f"{sim1.get(int(annee), {}).get('LCR', 0):.2f}%" if sim1.get(int(annee), {}).get('LCR') is not None else "N/A",
                    f"{sim2.get(int(annee), {}).get('LCR', 0):.2f}%" if sim2.get(int(annee), {}).get('LCR') is not None else "N/A",
                    f"{sim3.get(int(annee), {}).get('LCR', 0):.2f}%" if sim3.get(int(annee), {}).get('LCR') is not None else "N/A"
                ]
            
            lcr_df = pd.DataFrame(lcr_data)
            lcr_df = style_table(lcr_df, highlight_columns=["Scenario"])
            st.markdown(lcr_df.to_html(), unsafe_allow_html=True)

        with col2:
            st.subheader("Comparaison des ratios NSFR (%)")
            annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
            nsfr_data = {
                "Scenario": ["Projeté", "Phase 1", "Phase 2", "Phase 3"]
            }
            for annee in annees:
                nsfr_data[annee] = [
                    f"{proj.get(int(annee), {}).get('NSFR', 0):.2f}%" if proj.get(int(annee), {}).get('NSFR') is not None else "N/A",
                    f"{sim1.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim1.get(int(annee), {}).get('NSFR') is not None else "N/A",
                    f"{sim2.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim2.get(int(annee), {}).get('NSFR') is not None else "N/A",
                    f"{sim3.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim3.get(int(annee), {}).get('NSFR') is not None else "N/A"
                ]
            
            nsfr_df = pd.DataFrame(nsfr_data)
            nsfr_df = style_table(nsfr_df, highlight_columns=["Scenario"])
            st.markdown(nsfr_df.to_html(), unsafe_allow_html=True)


        st.subheader("Comparaison visuelle des scénarios")
        col1, col2 = st.columns(2)
        with col1:
            # LCR Comparison
            lcr_df = create_comparison_data(proj, sim1, sim2, sim3, horizon, "LCR")
            st.plotly_chart(plot_metric_comparison(lcr_df, "Comparaison des ratios LCR par scénario", 100),
                      use_container_width=True)
        with col2:
        # NSFR Comparison
            nsfr_df = create_comparison_data(proj, sim1, sim2, sim3, horizon, "NSFR")
            st.plotly_chart(plot_metric_comparison(nsfr_df, "Comparaison des ratios NSFR par scénario", 100),
                        use_container_width=True)
        
        # Components Analysis
        st.subheader("Analyse des composantes")
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_components_comparison(
                proj, sim1, sim2, sim3, horizon,
                ["HQLA", "OUTFLOWS", "INFLOWS"],
                "Composantes du LCR par scénario"
            ), use_container_width=True)
        
        with col2:
            st.plotly_chart(plot_components_comparison(
                proj, sim1, sim2, sim3, horizon,
                ["ASF", "RSF"],
                "Composantes du NSFR par scénario"
            ), use_container_width=True)

    # Other tabs
    display_tab_content(proj, horizon, tab1, "Scénario Projeté")
    display_tab_content(sim1, horizon, tab2, "Phase 1")
    display_tab_content(sim2, horizon, tab3, "Phase 2")
    display_tab_content(sim3, horizon, tab4, "Phase 3")