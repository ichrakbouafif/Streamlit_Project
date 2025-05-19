import streamlit as st
from interfaces import homepage, importation_donnees, calcul_ratios, choix_scenario, resultats_graphiques
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

st.set_page_config(page_title="Application de Stress Testing Bancaire", layout="wide")

# Couleurs
LIGHT_BG = "#F8F9FA"
ROSE = "#E88D14"
FONT_FAMILY = "Roboto, sans-serif"

# CSS pour styliser l'application
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Tinos&family=Roboto:wght@400;500;700&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Roboto', sans-serif;
            background-color: {LIGHT_BG};
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Tinos', serif !important;
            color: {ROSE} !important;
        }}

        [data-testid=stSidebar] {{
            background-color: {LIGHT_BG} !important; 
            border-right: 2px solid {ROSE}; 
            font-family: {FONT_FAMILY};
        }}

        .sidebar-title {{
            color: {ROSE}; 
            font-size: 22px;
            margin-bottom: 25px;
            font-weight: bold;
            text-align: center;
        }}

        .sidebar-footer {{
            color: {ROSE}; 
            font-size: 12px;
            text-align: center;
        }}

        .sidebar-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        /* Boutons actifs et cliquables */
        div.stButton > button {{
            width: 250px; 
            text-align: center;
            padding: 12px;
            margin: 8px auto;
            color: {ROSE}; 
            font-size: 16px;
            font-weight: 500;
            border: 2px solid {ROSE}; 
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            background-color: {LIGHT_BG}; 
            display: block;
        }}

        div.stButton > button:hover {{
            background-color: {ROSE}; 
            color: #FFFFFF !important;
        }}

        /* Bouton actif (page sélectionnée) */
        div.stButton > button.active {{
            background-color: {ROSE}; 
            color: white !important;
        }}

        /* Boutons désactivés */
        .disabled-btn {{
            width: 250px;
            text-align: center;
            padding: 12px;
            margin: 8px auto;
            font-size: 16px;
            font-weight: 500;
            border: 2px solid #CCCCCC;
            border-radius: 8px;
            background-color: #E0E0E0;
            color: #888;
            cursor: not-allowed;
            pointer-events: none;
        }}
    </style>
""", unsafe_allow_html=True)

# Dictionnaire des pages
pages = {
    "Accueil": homepage,
    "Importation des Données": importation_donnees,
    "Calcul des Ratios Baseline": calcul_ratios,
    "Choix du Scénario": choix_scenario,
    "Résultats & Graphiques": resultats_graphiques,
}

# Logique des pages accessibles
disabled_rules = {
    "Accueil": ["Importation des Données","Calcul des Ratios Baseline", "Choix du Scénario", "Résultats & Graphiques"],
    "Importation des Données": ["Calcul des Ratios Baseline", "Choix du Scénario", "Résultats & Graphiques"],
    "Calcul des Ratios Baseline": ["Importation des Données", "Choix du Scénario", "Résultats & Graphiques"],
    "Choix du Scénario": ["Importation des Données", "Calcul des Ratios Baseline", "Résultats & Graphiques"],
    "Résultats & Graphiques": ["Importation des Données","Calcul des Ratios Baseline", "Choix du Scénario"]
}

# Initialisation
if "selected_page" not in st.session_state:
    st.session_state.selected_page = "Accueil"

# Barre latérale
with st.sidebar:
    st.markdown('<h1 class="sidebar-title">Menu de Navigation</h1>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-container">', unsafe_allow_html=True)

    for page_name in pages:
        is_active = page_name == st.session_state.selected_page
        is_disabled = page_name in disabled_rules.get(st.session_state.selected_page, [])

        if is_disabled:
            st.markdown(
                f'<div class="disabled-btn" title="Veuillez terminer l\'étape précédente">{page_name}</div>',
                unsafe_allow_html=True
            )
        else:
            if st.button(page_name, key=page_name):
                st.session_state.selected_page = page_name
                st.rerun()

            if is_active:
                st.markdown(f"""
                    <script>
                        const buttons = parent.document.querySelectorAll('button[kind="secondary"]');
                        buttons.forEach(btn => {{
                            if (btn.innerText === "{page_name}") {{
                                btn.classList.add("active");
                            }}
                        }});
                    </script>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<p class="sidebar-footer">© 2025 Stress Testing Bancaire</p>', unsafe_allow_html=True)

# Affichage de la page sélectionnée
pages[st.session_state.selected_page].show()
