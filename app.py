import streamlit as st
from interfaces import homepage, importation_donnees, calcul_ratios, choix_scenario, resultats_graphiques

st.set_page_config(page_title="Application de Stress Testing Bancaire", layout="wide")

# Définir la palette de couleurs
LIGHT_BG = "#F8F9FA"  # Light background
NAVY_BLUE = "#002244"  # Navy blue for text, border, and hover
WHITE = "#FFFFFF"  # White text for active button
FONT_FAMILY = "Roboto, sans-serif"  # Professional banking font

# CSS pour styliser l'application
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tinos&family=Roboto:wght@400;500;700&display=swap');

        /* Apply Tinos for headers and Roboto for body text */
        body {{
            font-family: 'Roboto', sans-serif;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Tinos', serif;
        }}

        [data-testid=stSidebar] {{
            background-color: {LIGHT_BG} !important; 
            border-right: 2px solid {NAVY_BLUE}; 
            font-family: {FONT_FAMILY};
            padding-top: 20px;
        }}
        .sidebar-title {{
            color: {NAVY_BLUE}; 
            font-size: 22px;
            margin-bottom: 25px;
            font-weight: bold;
            text-align: center;
        }}
        .sidebar-footer {{
            color: {NAVY_BLUE}; 
            font-size: 12px;
            margin-top: 30px;
            text-align: center;
        }}
        div.stButton > button {{
            width: 100%; 
            text-align: center;
            padding: 12px;
            margin: 8px 0;
            color: {NAVY_BLUE}; 
            font-size: 16px;
            font-weight: 500;
            border: 2px solid {NAVY_BLUE}; 
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            background-color: {LIGHT_BG}; 
        }}
        div.stButton > button:hover {{
            background-color: {NAVY_BLUE}; 
            color: {WHITE} !important;
        }}
    </style>
""", unsafe_allow_html=True)

# Define your pages
pages = {
    "Accueil": homepage,
    "Importation des Données": importation_donnees,
    "Calcul des Ratios Baseline": calcul_ratios,
    "Choix du Scénario": choix_scenario,
    "Résultats & Graphiques": resultats_graphiques,
}

# Sidebar navigation
with st.sidebar:
    st.markdown('<h1 class="sidebar-title">Menu de Navigation</h1>', unsafe_allow_html=True)

    # Initialize session state
    if "selected_page" not in st.session_state:
        st.session_state.selected_page = "Accueil"

    # Sidebar buttons for navigation
    for page_name in pages.keys():
        if st.button(page_name, key=page_name):
            st.session_state.selected_page = page_name
            st.rerun()  # Refresh to load the new page

    st.markdown("---")
    st.markdown('<p class="sidebar-footer">© 2025 Stress Testing Bancaire</p>', unsafe_allow_html=True)

# Load the selected page
page = pages[st.session_state.selected_page]

# Assuming each module has a function `show()` that renders the page, call it here.
page.show()
