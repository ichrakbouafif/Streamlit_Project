import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import format_large_number
from backend.stress_test import event1 as bst
from backend.ratios_baseline.ratios_baseline import calcul_ratios_sur_horizon
from backend.ratios_baseline.ratios_baseline import charger_bilan



# Couleurs PwC
PWC_ORANGE = "#f47721"
PWC_DARK_GRAY = "#3d3d3d"
PWC_LIGHT_BEIGE = "#f5f0e6"
PWC_BROWN = "#6e4c1e"
PWC_SOFT_BLACK = "#2c2c2c"
PWC_DARK_ORANGE = "#d04a02"
PWC_LIGHT_BLUE = "#FFCDA8"
PWC_LIGHT_GRAY = "#f5f0e6"
PWC_LIGHT_BROWN = "#a65e2e"

def get_scenario_names():
    """Get proper scenario names based on session state"""
    # Get the scenario type selected in phase 1
    scenario_type_phase1 = st.session_state.get('scenario_type', 'idiosyncratique')
    
    # Determine names for each phase
    if scenario_type_phase1 == 'idiosyncratique':
        phase1_name = "Scénario Idiosyncratique"
        phase2_name = "Scénario Macroéconomique"
    else:
        phase1_name = "Scénario Macroéconomique"
        phase2_name = "Scénario Idiosyncratique"
    
    return {
        "baseline": "Scénario Baseline",
        "phase1": phase1_name,
        "phase2": phase2_name,
        "phase3": "Scénario Combiné"
    }

def format_millions(value):
    """Format numbers in millions with M suffix"""
    if pd.isna(value) or value is None:
        return "N/A"
    if value == 0:
        return "0.00 M€"
    return f"{value / 1_000_000:.2f} M€"


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
    """Stylise un tableau avec les couleurs PwC et formate les nombres."""
    
    # Make a copy to avoid modifying original DataFrame
    df = df.copy()
    
    # Format numbers and convert to string
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].apply(format_large_number)
    
    # Reset index to avoid displaying it
    df = df.reset_index(drop=True)
    
    # Define table styles (updated to account for no index column)
    table_styles = [
        {"selector": "thead th", 
         "props": f"background-color: {PWC_LIGHT_BLUE}; color: black; font-weight: bold; text-align: center; padding: 8px;"},
        {"selector": "tbody td", 
         "props": "padding: 6px; text-align: right;"},
        {"selector": "tbody tr:nth-child(odd) td", 
         "props": f"background-color: {PWC_LIGHT_BEIGE};"},
        {"selector": "tbody td:first-child", 
         "props": "text-align: left; font-weight: bold;"},
        {"selector": "table", 
         "props": "width: 100%; border-collapse: collapse; font-size: 14px;"},
        {"selector": "th, td", 
         "props": "border: 1px solid #ddd;"}
    ]
    
    styled_df = df.style.set_table_styles(table_styles)

    if highlight_columns:
        for col in highlight_columns:
            if col in df.columns:
                styled_df = styled_df.set_properties(**{
                    'font-weight': 'bold',
                    'color': PWC_ORANGE
                }, subset=[col])

    return styled_df

def format_number(x):
    """Format numbers without thousands separator and with 2 decimals"""
    if pd.isna(x) or x is None:
        return "N/A"
    return f"{x:,.2f}".replace(",", " ")

# Fonctions pour les ratios de liquidité
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
        
        # Formatage des montants monétaires en millions
        hqla_value = year_data.get("HQLA")
        outflows_value = year_data.get("OUTFLOWS")
        inflows_value = year_data.get("INFLOWS")
        lcr_value = year_data.get("LCR", 0)
        
        data[annee] = [
            format_millions(hqla_value),
            format_millions(outflows_value),
            format_millions(inflows_value),
            f"{lcr_value:.2f}%" if lcr_value else "0.00%"
        ]
    
    return pd.DataFrame(data)

# Fonction modifiée pour créer le tableau NSFR avec formatage en millions
def create_nsfr_table(resultats, horizon):
    annees = [str(2024 + i) for i in range(horizon + 1)]
    data = {
        " ": ["ASF", "RSF", "NSFR (%)"]
    }
    
    for annee in annees:
        year_data = resultats.get(int(annee), {})
        
        # Formatage des montants monétaires en millions
        asf_value = year_data.get("ASF")
        rsf_value = year_data.get("RSF")
        nsfr_value = year_data.get("NSFR", 0)
        
        data[annee] = [
            format_millions(asf_value),
            format_millions(rsf_value),
            f"{nsfr_value:.2f}%" if nsfr_value else "0.00%"
        ]
    
    return pd.DataFrame(data)

def create_comparison_data(proj, sim1, sim2, sim3, horizon, metric):
    """Create dataframe for comparison charts with proper scenario names"""
    scenario_names = get_scenario_names()
    years = list(range(2024, 2024 + horizon + 1))
    data = []
    
    for year in years:
        data.append({
            "Year": year,
            "Scenario": scenario_names["baseline"],
            "Value": proj.get(year, {}).get(metric, 0)
        })
        data.append({
            "Year": year,
            "Scenario": scenario_names["phase1"],
            "Value": sim1.get(year, {}).get(metric, 0)
        })
        data.append({
            "Year": year,
            "Scenario": scenario_names["phase2"],
            "Value": sim2.get(year, {}).get(metric, 0)
        })
        data.append({
            "Year": year,
            "Scenario": scenario_names["phase3"],
            "Value": sim3.get(year, {}).get(metric, 0)
        })
    
    return pd.DataFrame(data)

def plot_metric_comparison(df, title, threshold=None):
    """Create interactive comparison plot with PwC colors and proper scenario names"""
    scenario_names = get_scenario_names()
    scenario_colors = {
        scenario_names["baseline"]: PWC_DARK_GRAY,
        scenario_names["phase1"]: PWC_ORANGE,
        scenario_names["phase2"]: PWC_DARK_ORANGE,
        scenario_names["phase3"]: PWC_BROWN
    }
    
    fig = go.Figure()
    
    for scenario in df["Scenario"].unique():
        scenario_df = df[df["Scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=scenario_df["Year"],
            y=scenario_df["Value"],
            name=scenario,
            line=dict(color=scenario_colors.get(scenario, PWC_DARK_GRAY), width=3),
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

def plot_components_comparison(proj, sim1, sim2, sim3, horizon, components, title):
    """Plot comparison of LCR/NSFR components with proper scenario names"""
    scenario_names = get_scenario_names()
    years = list(range(2025, 2025 + horizon))
    scenarios = [scenario_names["baseline"], scenario_names["phase1"], 
                scenario_names["phase2"], scenario_names["phase3"]]
    scenario_colors = {
        scenario_names["baseline"]: PWC_DARK_ORANGE,
        scenario_names["phase1"]: PWC_ORANGE,
        scenario_names["phase2"]: PWC_LIGHT_BLUE,
        scenario_names["phase3"]: PWC_LIGHT_BROWN
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
                    "Valeur": year_data.get(component, 0)
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

def display_liquidity_tab_content(resultats, horizon, tab, scenario_name):
    if not resultats:
        tab.warning("Aucune donnée disponible")
        return

    with tab:
        # Display key metrics at the top
        col1, col2 = st.columns(2)
        with col1:
            last_year = str(2025)
            lcr_value = resultats.get(int(last_year), {}).get("LCR", 0)
            st.markdown(
                f"""
                <div style="background-color:{PWC_LIGHT_BEIGE}; padding:20px; border-radius:15px;
                            box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {PWC_ORANGE}">
                    <h4 style="color:{PWC_SOFT_BLACK}; margin-bottom:10px;">LCR ({last_year})</h4>
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
                    <h4 style="color:{PWC_SOFT_BLACK}; margin-bottom:10px;">NSFR ({last_year})</h4>
                    <p style="font-size:26px; font-weight:bold; color:{PWC_ORANGE}; margin:0;">
                        {nsfr_value:.2f}%
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.subheader(f"Évolution des ratios LCR et NSFR - {scenario_name}")

        # Prepare data for combined chart
        years = list(range(2024, 2024 + horizon + 1))
        lcr_values = [resultats.get(year, {}).get("LCR", 0) for year in years]
        nsfr_values = [resultats.get(year, {}).get("NSFR", 0) for year in years]

        # Create combined bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=years, y=lcr_values, name='LCR',
            marker_color=PWC_LIGHT_BLUE
        ))
        fig.add_trace(go.Bar(
            x=years, y=nsfr_values, name='NSFR',
            marker_color=PWC_ORANGE
        ))
        fig.add_hline(y=100, line_dash="dot", line_color="red",
                    annotation_text="Seuil minimum 100%", annotation_position="top left")
        fig.update_layout(
            barmode='group',
            xaxis_title="Année",
            yaxis_title="Ratio (%)",
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=350
        )

        st.plotly_chart(fig, use_container_width=True, key=f"lcr_nsfr_chart_{scenario_name}")

                
        st.subheader(f"Ratio LCR - {scenario_name}")
        lcr_table = create_lcr_table(resultats, horizon)
        if not lcr_table.empty:            
            lcr_df = style_table(lcr_table, highlight_columns=[" "])
            st.markdown(lcr_df.to_html(index=False), unsafe_allow_html=True)
            
        else:
            st.warning("Aucune donnée LCR disponible")

        st.subheader(f"Ratio NSFR - {scenario_name}")
        nsfr_table = create_nsfr_table(resultats, horizon)
        if not nsfr_table.empty:
            nsfr_df = style_table(nsfr_table, highlight_columns=[" "])
            st.markdown(nsfr_df.to_html(index=False), unsafe_allow_html=True)
        else:
            st.warning("Aucune donnée NSFR disponible")

####################
def style_table_with_preformatted(df, highlight_columns=None):
    """Stylise un tableau avec les couleurs PwC sans re-formater les nombres déjà formatés."""
    
    # Make a copy to avoid modifying original DataFrame
    df = df.copy()
    
    # Reset index to avoid displaying it
    df = df.reset_index(drop=True)
    
    # Define table styles
    table_styles = [
        {"selector": "thead th", 
         "props": f"background-color: {PWC_LIGHT_BLUE}; color: black; font-weight: bold; text-align: center; padding: 8px;"},
        {"selector": "tbody td", 
         "props": "padding: 6px; text-align: right;"},
        {"selector": "tbody tr:nth-child(odd) td", 
         "props": f"background-color: {PWC_LIGHT_BEIGE};"},
        {"selector": "tbody td:first-child", 
         "props": "text-align: left; font-weight: bold;"},
        {"selector": "table", 
         "props": "width: 100%; border-collapse: collapse; font-size: 14px;"},
        {"selector": "th, td", 
         "props": "border: 1px solid #ddd;"}
    ]
    
    styled_df = df.style.set_table_styles(table_styles)

    if highlight_columns:
        for col in highlight_columns:
            if col in df.columns:
                styled_df = styled_df.set_properties(**{
                    'font-weight': 'bold',
                    'color': PWC_ORANGE
                }, subset=[col])

    return styled_df

# Fonction modifiée display_liquidity_tab_content pour utiliser le nouveau formatage
def display_liquidity_tab_content_formatted(resultats, horizon, tab, scenario_name):
    if not resultats:
        tab.warning("Aucune donnée disponible")
        return

    with tab:
        # Display key metrics at the top
        col1, col2 = st.columns(2)
        with col1:
            last_year = str(2025)
            lcr_value = resultats.get(int(last_year), {}).get("LCR", 0)
            st.markdown(
                f"""
                <div style="background-color:{PWC_LIGHT_BEIGE}; padding:20px; border-radius:15px;
                            box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center; border-left: 8px solid {PWC_ORANGE}">
                    <h4 style="color:{PWC_SOFT_BLACK}; margin-bottom:10px;">LCR ({last_year})</h4>
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
                    <h4 style="color:{PWC_SOFT_BLACK}; margin-bottom:10px;">NSFR ({last_year})</h4>
                    <p style="font-size:26px; font-weight:bold; color:{PWC_ORANGE}; margin:0;">
                        {nsfr_value:.2f}%
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.subheader(f"Évolution des ratios LCR et NSFR - {scenario_name}")

        # Prepare data for combined chart (values in millions for display)
        years = list(range(2024, 2024 + horizon + 1))
        lcr_values = [resultats.get(year, {}).get("LCR", 0) for year in years]
        nsfr_values = [resultats.get(year, {}).get("NSFR", 0) for year in years]

        # Create combined bar chart
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=years, y=lcr_values, name='LCR',
            marker_color=PWC_LIGHT_BLUE
        ))
        fig.add_trace(go.Bar(
            x=years, y=nsfr_values, name='NSFR',
            marker_color=PWC_ORANGE
        ))
        fig.add_hline(y=100, line_dash="dot", line_color="red",
                    annotation_text="Seuil minimum 100%", annotation_position="top left")
        fig.update_layout(
            barmode='group',
            xaxis_title="Année",
            yaxis_title="Ratio (%)",
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=350
        )

        st.plotly_chart(fig, use_container_width=True, key=f"lcr_nsfr_chart_{scenario_name}")

        # Tableaux avec formatage en millions        
        st.subheader(f"Ratio LCR - {scenario_name}")
        lcr_table = create_lcr_table(resultats, horizon)
        if not lcr_table.empty:            
            lcr_df = style_table_with_preformatted(lcr_table, highlight_columns=[" "])
            st.markdown(lcr_df.to_html(index=False), unsafe_allow_html=True)
        else:
            st.warning("Aucune donnée LCR disponible")

        st.subheader(f"Ratio NSFR - {scenario_name}")
        nsfr_table = create_nsfr_table(resultats, horizon)
        if not nsfr_table.empty:
            nsfr_df = style_table_with_preformatted(nsfr_table, highlight_columns=[" "])
            st.markdown(nsfr_df.to_html(index=False), unsafe_allow_html=True)
        else:
            st.warning("Aucune donnée NSFR disponible")
            ###################
            # 
            #             
# Fonctions pour les ratios de capital
def create_solva_table_capital(resultats, horizon):
    """CORRECTION : Utilisation des bonnes clés pour solvabilité"""
    annees = [str(2024 + i) for i in range(horizon + 1)]
    data = {
        " ": [
            "Fonds propres réglementaires",
            "RWA (actifs pondérés)",
            "Ratio de solvabilité (%)"
        ]
    }

    for annee in annees:
        #annee_int = int(annee)
        year_data = resultats.get(annee, {})

        # CORRECTION : Vérifiez que ces clés correspondent à vos données
        data[annee] = [
            format_millions(year_data.get("fonds_propres", 0)),  # ou "fonds_propres"
            format_millions(year_data.get("rwa", 0)),            # ou "rwa" 
            year_data.get("ratio", 0)   # ou "ratio"
        ]

    return pd.DataFrame(data)
def create_levier_table_capital(resultats, horizon):
    annees = [str(2024 + i) for i in range(horizon + 1)]
    data = {
        " ": [
            "Fonds propres Tier 1",
            "Exposition au levier",
            "Ratio de levier (%)"
        ]
    }

    for annee in annees:
        #annee_int = int(annee)
        year_data = resultats.get(annee, {})
        data[annee] = [
            format_millions(year_data.get("tier1")),
            format_millions(year_data.get("total_exposure")),
            year_data.get("ratio", 0)
        ]

    return pd.DataFrame(data)

def create_comparison_data_capital(proj, sim1, sim2, sim3, horizon, ratio_type):
    """
    CORRECTION : Fonction spécialisée par type de ratio
    ratio_type: "Solvabilité" ou "Levier"
    """
    years = list(range(2024, 2024 + horizon + 1))
    data = []

    for year in years:
        # Utilisation des bonnes clés selon le type de ratio
        data.append({"Year": year, "Scenario": "Scénario Baseline", "Value": proj.get(year, {}).get(ratio_type, 0)})
        data.append({"Year": year, "Scenario": "Scénario Idiosyncratique", "Value": sim1.get(year, {}).get(ratio_type, 0)})
        data.append({"Year": year, "Scenario": "Scénario Macroéconomique", "Value": sim2.get(year, {}).get(ratio_type, 0)})
        data.append({"Year": year, "Scenario": "Scénario Combiné", "Value": sim3.get(year, {}).get(ratio_type, 0)})

    return pd.DataFrame(data)
def plot_components_comparison_capital(proj, sim1, sim2, sim3, horizon, components, title):
    """Affiche un graphique en barres groupées pour les composantes des ratios de capital"""
    years = list(range(2024, 2024 + horizon + 1))
    scenarios = ["Scénario Baseline", "Scénario Idiosyncratique", "Scénario Macroéconomique", "Scénario Combiné"]
    scenario_colors = {
        "Scénario Baseline": PWC_LIGHT_GRAY,
        "Scénario Idiosyncratique": PWC_ORANGE,
        "Scénario Macroéconomique": PWC_DARK_ORANGE,
        "Scénario Combiné": PWC_LIGHT_BROWN
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
                    "Valeur": year_data.get(component, 0)
                })

    df = pd.DataFrame(data)

    fig = px.bar(
        df, 
        x="Année", 
        y="Valeur", 
        color="Scénario",
        facet_col="Composant",
        title=title,
        template="plotly_white",
        color_discrete_map=scenario_colors,
        barmode="group"
    )

    fig.update_layout(
        height=400,
        showlegend=True,
        xaxis_title="Année",
        yaxis_title="Valeur"
    )

    return fig

def display_capital_tab_content(resultats_solva, resultats_levier, horizon, tab, scenario_name):
    if not resultats_solva or not resultats_levier:
        tab.warning("Aucune donnée disponible")
        return

    with tab:
        st.subheader(f"Ratios réglementaires - {scenario_name}")
        col1, col2 = st.columns(2)

        # --- Cartes Résumé ---
        last_year = 2024 + horizon
        # CORRECTION : Utilisation cohérente des clés
        solva_value = resultats_solva.get(last_year, {}).get("ratio", 0)
        levier_value = resultats_levier.get(last_year, {}).get("ratio", 0)

        # DEBUG : Ajout de logs pour diagnostiquer
        st.write(f"DEBUG - {scenario_name} - Année {last_year}")
        st.write(f"DEBUG - Données solvabilité: {resultats_solva.get(last_year, {})}")
        st.write(f"DEBUG - Données levier: {resultats_levier.get(last_year, {})}")
        st.write(f"DEBUG - Valeur solvabilité: {solva_value}")
        st.write(f"DEBUG - Valeur levier: {levier_value}")

        with col1:
            st.markdown(f"""
            <div style="background-color:#f5f0e6; padding:20px; border-radius:15px;
                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center;
                        border-left: 8px solid #f47721">
                <h4 style="color:#2c2c2c; margin-bottom:10px;">Ratio de Solvabilité ({last_year})</h4>
                <p style="font-size:26px; font-weight:bold; color:#f47721; margin:0;">
                    {solva_value:.2f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="background-color:#f5f0e6; padding:20px; border-radius:15px;
                        box-shadow:0 4px 8px rgba(0,0,0,0.1); text-align:center;
                        border-left: 8px solid #f47721">
                <h4 style="color:#2c2c2c; margin-bottom:10px;">Ratio de Levier ({last_year})</h4>
                <p style="font-size:26px; font-weight:bold; color:#f47721; margin:0;">
                    {levier_value:.2f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        # --- Graphe combiné ---
        st.subheader(f"Évolution des ratios - {scenario_name}")
        annees = list(range(2024, 2024 + horizon + 1))
        solva_vals = [resultats_solva.get(a, {}).get("ratio", 0) for a in annees]
        levier_vals = [resultats_levier.get(a, {}).get("ratio", 0) for a in annees]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=annees, y=solva_vals, mode='lines+markers', name='Solvabilité',
            line=dict(color=PWC_ORANGE, width=3)
        ))
        fig.add_trace(go.Scatter(
            x=annees, y=levier_vals, mode='lines+markers', name='Levier',
            line=dict(color=PWC_DARK_GRAY, width=3)
        ))
        fig.add_hline(y=8, line_dash="dot", line_color="red",
                      annotation_text="Seuil Solvabilité: 8%", annotation_position="top left")
        fig.add_hline(y=3, line_dash="dot", line_color="red",
                      annotation_text="Seuil Levier: 3%", annotation_position="bottom right")
        fig.update_layout(
            height=350,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis_title="Année",
            yaxis_title="Ratio (%)"
        )
        st.plotly_chart(fig, use_container_width=True, key=f"combined_chart_capital_{scenario_name}")

        # --- Tableau Solvabilité ---
        st.subheader(f"Composantes du ratio de solvabilité - {scenario_name}")
        df_solva = create_solva_table_capital(resultats_solva, horizon)
        st.markdown(style_table(df_solva, highlight_columns=[" "]).to_html(index=False), unsafe_allow_html=True)

        # --- Tableau Levier ---
        st.subheader(f"Composantes du ratio de levier - {scenario_name}")
        df_levier = create_levier_table_capital(resultats_levier, horizon)
        st.markdown(style_table(df_levier, highlight_columns=[" "]).to_html(index=False), unsafe_allow_html=True)

def calculate_projected_ratios(horizon):
    """Recalculate projected liquidity ratios"""
    bilan = charger_bilan()
    df_72, df_73, df_74 = bst.charger_lcr()
    df_80, df_81 = bst.charger_nsfr()
    return calcul_ratios_sur_horizon(horizon, bilan, df_72, df_73, df_74, df_80, df_81)

def show():
    apply_custom_styles()
    
    # Get scenario names
    scenario_names = get_scenario_names()
    
    # Récupération des résultats
    horizon = st.session_state.get('horizon_global', 3)
    proj_liquidity = calculate_projected_ratios(horizon)
    
    # Ratios de liquidité
    sim1_liquidity = st.session_state.get('resultats_phase1', {})
    sim2_liquidity = st.session_state.get('resultats_phase2', {})
    sim3_liquidity = st.session_state.get('resultats_phase3', {})
    
    # Ratios de capital
    proj_solva = st.session_state.get("resultats_solva", {})
    proj_levier = st.session_state.get("resultats_levier", {})
    sim1_solva = st.session_state.get("resultats_sim1_capital", {})
    sim1_levier = st.session_state.get("resultats_sim1_levier", {})
    sim2_solva = st.session_state.get("resultats_sim2_capital", {})
    sim2_levier = st.session_state.get("resultats_sim2_levier", {})
    sim3_solva = st.session_state.get("resultats_sim3_capital", {})
    sim3_levier = st.session_state.get("resultats_sim3_levier", {})

    st.title("Résultats et Graphiques")
    st.write("Visualisez les résultats du stress test et les graphiques comparatifs.")

    # Création des onglets
    tab_liquidity, tab_capital = st.tabs(["Ratios de Liquidité", "Ratios de Capital"])

    with tab_liquidity:
        # Onglets pour les scénarios de liquidité avec noms appropriés
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Récapitulatif",
            scenario_names["baseline"],
            scenario_names["phase1"],
            scenario_names["phase2"],
            scenario_names["phase3"]
        ])

        # TAB 1 — Récapitulatif
        with tab1:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Comparaison des ratios LCR (%)")
                annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
                lcr_data = {
                    "Scenario": [scenario_names["baseline"], scenario_names["phase1"], 
                               scenario_names["phase2"], scenario_names["phase3"]]
                }

                for annee in annees:
                    lcr_data[annee] = [
                        f"{proj_liquidity.get(int(annee), {}).get('LCR', 0):.2f}%" if proj_liquidity.get(int(annee), {}).get('LCR') is not None else "N/A",
                        f"{sim1_liquidity.get(int(annee), {}).get('LCR', 0):.2f}%" if sim1_liquidity.get(int(annee), {}).get('LCR') is not None else "N/A",
                        f"{sim2_liquidity.get(int(annee), {}).get('LCR', 0):.2f}%" if sim2_liquidity.get(int(annee), {}).get('LCR') is not None else "N/A",
                        f"{sim3_liquidity.get(int(annee), {}).get('LCR', 0):.2f}%" if sim3_liquidity.get(int(annee), {}).get('LCR') is not None else "N/A"
                    ]
                
                lcr_df = pd.DataFrame(lcr_data)
                lcr_df = style_table(lcr_df, highlight_columns=["Scenario"])
                st.markdown(lcr_df.to_html(index=False), unsafe_allow_html=True)

            with col2:
                st.subheader("Comparaison des ratios NSFR (%)")
                annees = [str(annee) for annee in range(2024, 2024 + horizon + 1)]
                nsfr_data = {
                    "Scenario": [scenario_names["baseline"], scenario_names["phase1"], 
                               scenario_names["phase2"], scenario_names["phase3"]]
                }
                for annee in annees:
                    nsfr_data[annee] = [
                        f"{proj_liquidity.get(int(annee), {}).get('NSFR', 0):.2f}%" if proj_liquidity.get(int(annee), {}).get('NSFR') is not None else "N/A",
                        f"{sim1_liquidity.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim1_liquidity.get(int(annee), {}).get('NSFR') is not None else "N/A",
                        f"{sim2_liquidity.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim2_liquidity.get(int(annee), {}).get('NSFR') is not None else "N/A",
                        f"{sim3_liquidity.get(int(annee), {}).get('NSFR', 0):.2f}%" if sim3_liquidity.get(int(annee), {}).get('NSFR') is not None else "N/A"
                    ]
                
                nsfr_df = pd.DataFrame(nsfr_data)
                nsfr_df = style_table(nsfr_df, highlight_columns=["Scenario"])
                st.markdown(nsfr_df.to_html(index=False), unsafe_allow_html=True)
            
            # Components Analysis
            st.subheader("Analyse des composantes")
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(plot_components_comparison(
                    proj_liquidity, sim1_liquidity, sim2_liquidity, sim3_liquidity, horizon,
                    ["HQLA", "OUTFLOWS", "INFLOWS"],
                    "Composantes du LCR par scénario"
                ), use_container_width=True)
            
            with col2:
                st.plotly_chart(plot_components_comparison(
                    proj_liquidity, sim1_liquidity, sim2_liquidity, sim3_liquidity, horizon,
                    ["ASF", "RSF"],
                    "Composantes du NSFR par scénario"
                ), use_container_width=True)

        # Other tabs for liquidity with proper names
        display_liquidity_tab_content(proj_liquidity, horizon, tab2, scenario_names["baseline"])
        display_liquidity_tab_content(sim1_liquidity, horizon, tab3, scenario_names["phase1"])
        display_liquidity_tab_content(sim2_liquidity, horizon, tab4, scenario_names["phase2"])
        display_liquidity_tab_content(sim3_liquidity, horizon, tab5, scenario_names["phase3"])

    with tab_capital:
        # Onglets pour les scénarios de capital avec noms appropriés
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Récapitulatif",
            scenario_names["baseline"],
            scenario_names["phase1"],
            scenario_names["phase2"],
            scenario_names["phase3"]
        ])

        with tab1:
            st.markdown("### Comparaison des ratios de capital (%)", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            # --- Solvabilité ---
            with col1:
                st.markdown("### Ratios de Solvabilité")

                mapping_solva = {
                    scenario_names["baseline"]: "df_solva_projete",
                    scenario_names["phase1"]: "df_solva_phase1",
                    scenario_names["phase2"]: "df_solva_phase2",
                    scenario_names["phase3"]: "df_solva_phase3"
                }

                for nom, key in mapping_solva.items():
                    df = st.session_state.get(key)
                    if df is not None:
                        st.markdown(f"**{nom}**")
                        st.markdown(df.to_html(index=False), unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{nom}** – Pas de données disponibles")

            # --- Levier ---
            with col2:
                st.markdown("### Ratios de Levier")

                mapping_levier = {
                    scenario_names["baseline"]: "df_levier_projete",
                    scenario_names["phase1"]: "df_levier_phase1",
                    scenario_names["phase2"]: "df_levier_phase2",
                    scenario_names["phase3"]: "df_levier_phase3"
                }

                for nom, key in mapping_levier.items():
                    df = st.session_state.get(key)
                    if df is not None:
                        st.markdown(f"**{nom}**")
                        st.markdown(df.to_html(index=False), unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{nom}** – Pas de données disponibles")

                # Onglet TAB 2 — Projeté
    with tab2:
            #st.subheader("Ratios projetés – Solvabilité et Levier")

            df_proj_solva, df_proj_levier = afficher_ratios_solva_levier_projete(proj_solva, proj_levier, horizon)
            st.session_state["df_solva_projete"] = df_proj_solva
            st.session_state["df_levier_projete"] = df_proj_levier

        
    with tab3:
            st.subheader("Résultats du ratio de solvabilité ")

            # Mapping des événements à leurs résultats
            recap_key_map = {
                "Retrait massif des dépôts": "resultats_solvabilite_phase1",
                "Tirage PNU": "resultats_solva_pnu_phase1"
            }

            recap_levier_key_map = {
                "Retrait massif des dépôts": "resultats_levier_phase1"
                # Ajoute d'autres événements si nécessaire
            }

            for event in st.session_state.get("selected_events_phase1", []):
                key_solva = recap_key_map.get(event)
                key_levier = recap_levier_key_map.get(event)

                if key_solva and key_solva in st.session_state:
                    recap = st.session_state[key_solva]
                    df1 = afficher_tableau_recapitulatif(recap, ratio_type="Solvabilité",    drop_combined=True
)
                    st.session_state["df_solva_phase1"] = df1

                        # 2) Histogramme à partir de la liste `recap`
# 2) Histogramme Solvabilité – Idiosyncratique
                    if recap:
                        df_temp = pd.DataFrame(recap).set_index("Année")
                        # Cherche dynamiquement la colonne RWA
                        rwa_col = next((c for c in ("RWA total", "RWA Retrait", "RWA total PNU") if c in df_temp), None)
                        if rwa_col:
                            # Prépare les séries en M€
                            fonds = df_temp["Fonds propres"].astype(float).div(1e6)
                            rwas  = df_temp[rwa_col].astype(float).div(1e6)

                            # Deux colonnes pour afficher côte-à-côte
                            col1, col2 = st.columns(2)

                            with col1:
                                fig1 = px.bar(
                                    x=fonds.index,
                                    y=fonds.values,
                                    labels={"x":"Année", "y":"Fonds Propres (M€)"},
                                    title="Fonds Propres – Idiosyncratique",
                                    color_discrete_sequence=[PWC_ORANGE]
                                )
                                st.plotly_chart(fig1, use_container_width=True)

                            with col2:
                                fig2 = px.bar(
                                    x=rwas.index,
                                    y=rwas.values,
                                    labels={"x":"Année", "y":"RWA (M€)"},
                                    title="RWA – Idiosyncratique",
                                    color_discrete_sequence=[PWC_LIGHT_BLUE]
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                        else:
                            st.warning("Impossible de trouver la colonne RWA pour l'histogramme.")
                    else:
                        st.warning("Pas de données de solvabilité à tracer.")
                if key_levier and key_levier in st.session_state:
                    recap_levier = st.session_state[key_levier]
                    df1_lev = afficher_tableau_recapitulatif_levier(recap_levier)
                    st.session_state["df_levier_phase1"] = df1_lev

    with tab4:
        # --- Solvabilité ---
        recap_solva_phase2 = st.session_state.get("resultats_solvabilite_phase2", [])
        if recap_solva_phase2:
            st.markdown("### Ratio de Solvabilité – Scénario Macroéconomique")
            df2 = afficher_tableau_recapitulatif(
                recap_solva_phase2,
                ratio_type="Solvabilité",
                drop_combined=True
            )
            st.session_state["df_solva_phase2"] = df2

            # ─── Histogrammes Solvabilité Macro ───
            df_temp = pd.DataFrame(recap_solva_phase2).set_index("Année")
            rwa_col = next((c for c in ("RWA total", "RWA Retrait", "RWA total PNU") if c in df_temp), None)
            if rwa_col:
                fonds2 = df_temp["Fonds propres"].astype(float).div(1e6)
                rwas2  = df_temp[rwa_col].astype(float).div(1e6)
                y_max = max(fonds2.max(), rwas2.max())

                col1, col2 = st.columns(2)
                with col1:
                    fig_fp2 = px.bar(
                        x=fonds2.index, y=fonds2.values,
                        labels={"x": "Année", "y": "Fonds Propres (M€)"},
                        title="Fonds Propres – Macroéconomique",
                        color_discrete_sequence=[PWC_ORANGE],
                        range_y=[0, y_max]
                    )
                    st.plotly_chart(fig_fp2, use_container_width=True)
                with col2:
                    fig_rwa2 = px.bar(
                        x=rwas2.index, y=rwas2.values,
                        labels={"x": "Année", "y": "RWA (M€)"},
                        title="RWA – Macroéconomique",
                        color_discrete_sequence=[PWC_LIGHT_BLUE],
                        range_y=[0, y_max]
                    )
                    st.plotly_chart(fig_rwa2, use_container_width=True)
            else:
                st.warning("Colonne RWA introuvable pour l'histogramme de solvabilité Macro.")
        else:
            st.info("Aucun résultat de solvabilité disponible pour la phase 2.")

        st.markdown("---")

        # --- Levier ---
        recap_levier_phase2 = st.session_state.get("resultats_levier_phase2", [])
        if recap_levier_phase2:
            st.markdown("### Ratio de Levier – Scénario Macroéconomique")
            df2_lev = afficher_tableau_recapitulatif_levier(recap_levier_phase2)
            st.session_state["df_levier_phase2"] = df2_lev

            # ─── Histogrammes Levier Macro ───
            df_temp2 = pd.DataFrame(recap_levier_phase2).set_index("Année")
            if {"Fonds propres", "Exposition totale"}.issubset(df_temp2.columns):
                tier2 = df_temp2["Fonds propres"].astype(float).div(1e6)
                expo2 = df_temp2["Exposition totale"].astype(float).div(1e6)
                y_max2 = max(tier2.max(), expo2.max())

                col1, col2 = st.columns(2)
                with col1:
                    fig_tier2 = px.bar(
                        x=tier2.index, y=tier2.values,
                        labels={"x": "Année", "y": "Tier 1 (M€)"},
                        title="Tier 1 – Macroéconomique",
                        color_discrete_sequence=[PWC_ORANGE],
                        range_y=[0, y_max2]
                    )
                    st.plotly_chart(fig_tier2, use_container_width=True)
                with col2:
                    fig_expo2 = px.bar(
                        x=expo2.index, y=expo2.values,
                        labels={"x": "Année", "y": "Exposition (M€)"},
                        title="Exposition – Macroéconomique",
                        color_discrete_sequence=[PWC_LIGHT_BLUE],
                        range_y=[0, y_max2]
                    )
                    st.plotly_chart(fig_expo2, use_container_width=True)
            else:
                st.warning("Colonnes Fonds propres/Exposition manquantes pour l'histogramme Levier Macro.")
        else:
            st.info("Aucun résultat de levier disponible pour la phase 2.")

    with tab5:
            #st.subheader("Résultats – (Simulation combinée)")

            # --- Solvabilité combinée ---
            recap_solva_phase3 = st.session_state.get("resultats_solvabilite_phase3", [])
            if recap_solva_phase3:
                st.markdown("### Ratio de Solvabilité – Scénario Combiné")
                df3 = afficher_tableau_recapitulatif(recap_solva_phase3, ratio_type="Solvabilité")
                st.session_state["df_solva_phase3"] = df3

            else:
                st.info("Aucun résultat de solvabilité combiné disponible pour Scénario Combiné.")

            st.markdown("---")

            # --- Levier combiné ---
            recap_levier_phase3 = st.session_state.get("resultats_levier_phase3", [])
            if recap_levier_phase3:
                st.markdown("### Ratio de Levier – Scénario Combiné")
                df3_lev = afficher_tableau_recapitulatif_levier(recap_levier_phase3)
                st.session_state["df_levier_phase3"] = df3_lev

            else:
                st.info("Aucun résultat de levier combiné disponible pour Scénario Combiné.")

####new 
def afficher_ratios_solva_levier_projete(resultats_solva, resultats_levier, horizon):

    annees = [str(2024 + i) for i in range(horizon + 1)]

    # -------- TABLEAU SOLVABILITÉ --------
    st.markdown("### Ratio Solvabilité – Scénario Baseline")

    data_solva = {
        "Année": [],
        "Fonds Propres": [],
        "RWA": [],
        "Solvabilité (%)": []
    }

    for annee in annees:
        resultat = resultats_solva.get(annee, {})
        data_solva["Année"].append(annee)
        data_solva["Fonds Propres"].append(format_millions(resultat.get("fonds_propres", 0)))
        data_solva["RWA"].append(format_millions(resultat.get("rwa", 0)))
        data_solva["Solvabilité (%)"].append(round(resultat.get("ratio", 0), 2))

    df_solva = pd.DataFrame(data_solva)
    #st.dataframe(df_solva, use_container_width=True)
    df_solva= style_table(df_solva, highlight_columns=[" "])
    st.markdown(df_solva.to_html(), unsafe_allow_html=True)
    # --- Histogramme Solvabilité ---
# Reconstruire un DF numérique pour le graphique
# —– Graphique Composantes Solvabilité —–
# Reconstruction d’un mini-DF numérique
    solva_chart = pd.DataFrame({
        "Année": data_solva["Année"],
        "Fonds Propres (M€)": [resultats_solva.get(a, {}).get("fonds_propres",0)/1e6 for a in data_solva["Année"]],
        "RWA (M€)":            [resultats_solva.get(a, {}).get("rwa",0)/1e6           for a in data_solva["Année"]],
    })
    # Bar chart groupé avec orange fluo et orange clair
    fig_solva = px.bar(
        solva_chart,
        x="Année",
        y=["Fonds Propres (M€)", "RWA (M€)"],
        barmode="group",
        color_discrete_sequence=[PWC_ORANGE, PWC_LIGHT_BLUE],
        title="Composantes du Ratio de Solvabilité (en M€)"
    )
    st.plotly_chart(fig_solva, use_container_width=True)


    # -------- TABLEAU LEVIER --------
    st.markdown("### Ratio Levier – Scénario Baseline")

    data_levier = {
        "Année": [],
        "Tier 1": [],
        "Exposition Totale": [],
        "Levier (%)": []
    }

    for annee in annees:
        resultat = resultats_levier.get(annee, {})
        data_levier["Année"].append(annee)
        data_levier["Tier 1"].append(format_millions(resultat.get("tier1", 0)))
        data_levier["Exposition Totale"].append(format_millions(resultat.get("total_exposure", 0)))
        data_levier["Levier (%)"].append(round(resultat.get("ratio", 0), 2))

    df_levier = pd.DataFrame(data_levier)
    df_levier= style_table(df_levier, highlight_columns=[" "])
    st.markdown(df_levier.to_html(index=False), unsafe_allow_html=True)
    # —– Graphique Composantes Levier —–
    levier_chart = pd.DataFrame({
        "Année": data_levier["Année"],
        "Tier 1 (M€)":     [resultats_levier.get(a, {}).get("tier1",0)/1e6         for a in data_levier["Année"]],
        "Exposition (M€)": [resultats_levier.get(a, {}).get("total_exposure",0)/1e6 for a in data_levier["Année"]],
    })
    fig_levier = px.bar(
        levier_chart,
        x="Année",
        y=["Tier 1 (M€)", "Exposition (M€)"],
        barmode="group",
        color_discrete_sequence=[PWC_ORANGE, PWC_LIGHT_BLUE],
        title="Composantes du Ratio de Levier (en M€)"
    )
    st.plotly_chart(fig_levier, use_container_width=True)

    st.session_state["df_solva_projete"] = df_solva
    st.session_state["df_levier_projete"] = df_levier
    return df_solva, df_levier

def afficher_tableau_recapitulatif(recap_data, ratio_type, drop_combined=False):
    if not isinstance(recap_data, list) or not all(isinstance(x, dict) for x in recap_data):
        st.error("Les données de récapitulatif ne sont pas au bon format.")
        return
    
    df = pd.DataFrame([{
        "Année": x.get("Année"),
        "Fonds propres": format_millions(x.get('Fonds propres', 0)),
        "RWA total": format_millions(
            x.get('RWA total') or x.get('RWA Retrait') or x.get('RWA total PNU') or 0
        ) if x.get("RWA total") or x.get("RWA Retrait") or x.get("RWA total PNU") else "",
        "RWA combiné": format_millions(x.get('RWA combiné') or 0) if x.get("RWA combiné") else "",
        "Ratio (%)": f"{x.get('Ratio Retrait (%)') or x.get('Ratio PNU (%)') or 0:.2f}%",
        "Ratio combiné (%)": f"{x.get('Ratio combiné (%)', 0):.2f}%" if x.get("Ratio combiné (%)") is not None else ""
    } for x in recap_data])
 # si on est en idiosyncratique, on enlève les deux colonnes combinées
    if drop_combined:
       df = df.drop(columns=["RWA combiné", "Ratio combiné (%)"], errors="ignore")

    df= style_table(df, highlight_columns=[" "])
    st.markdown(df.to_html(index=False), unsafe_allow_html=True)
    return df  # Ajout pour réutilisation

def afficher_tableau_recapitulatif_levier(recap_data):
    if not recap_data:
        st.warning("Aucune donnée disponible pour le ratio de levier.")
        return

    df_affiche = pd.DataFrame([{
        "Année": r["Année"],
        "Fonds propres": format_millions(r["Fonds propres"]),
        "Exposition totale": format_millions(r["Exposition totale"]),
        "Ratio de levier (%)": f"{r['Ratio de levier (%)']:.2f}%"
    } for r in recap_data])

    df_affiche= style_table(df_affiche, highlight_columns=[" "])
    st.markdown(df_affiche.to_html(index=False), unsafe_allow_html=True)
    return df_affiche
def generer_tableau_comparatif_ratios(resultats_dict: dict, cle_possibles: list) -> pd.DataFrame:
    annees = ["2024", "2025", "2026", "2027"]
    tableau = []

    for scenario, resultats in resultats_dict.items():
        ligne = {"Scénario": scenario}
        for annee in annees:
            valeur = "N/A"
            for r in resultats:
                if str(r.get("Année")) == annee:
                    for cle in cle_possibles:
                        if cle in r:
                            ratio = r[cle]
                            if pd.isna(ratio):
                                valeur = "N/A"
                            else:
                                valeur = f"{float(ratio):.2f}%"
                            break
                    break
            ligne[annee] = valeur
        tableau.append(ligne)

    return pd.DataFrame(tableau)