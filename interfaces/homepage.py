import streamlit as st
import os
import base64

def show():
    # --- HEADER ---
    col_logo, col_title, col_help = st.columns([1, 5, 0.5])

    with col_logo:
        st.image("assets/PwC_logo.jpg", width=100)
    
    with col_title:
        st.markdown('<h1 style="color:#E0301E;">Outil de Stress Test Bancaire</h1>', unsafe_allow_html=True)
    
    with col_help:
        if st.button("❓", help="Afficher le guide d’utilisation"):
            st.session_state["show_guide"] = not st.session_state.get("show_guide", False)

# --- GUIDE ---
    if st.session_state.get("show_guide", False):
        # Guide content
        st.markdown("### Guide d'utilisation")
        st.markdown("""
        **Étapes du processus** :
        
        1. Importation des fichiers Excel : Bilan, COREP, Capital Planning  
        
        2. Calcul des ratios réglementaires (Référence & Baseline)  
        
        3. Simulation 1 : scénario idiosyncratique ou macroéconomique  
        
        4. Simulation 2 : scénario complémentaire  
        
        5. Simulation combinée (automatique)
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # Get the absolute path of the image (move up one level)
    image_path = os.path.join(os.path.dirname(__file__), "../assets", "home_page.png")

    # Apply CSS styling for header and image
    st.markdown(
        """
        <style>
            /* Import Google fonts Tinos and Roboto */
            @import url('https://fonts.googleapis.com/css2?family=Tinos&family=Roboto&display=swap');

            /* Apply Tinos for headers and Roboto for body text */
            body {
                font-family: 'Roboto', sans-serif;
            }

            h1, h2, h3, h4, h5, h6 {
                font-family: 'Tinos', serif;
            }

            /* Container for the background image */
            .hero-image-container {
                position: relative;
                width: 100%;
                height: 400px;
                background-image: url('data:image/jpeg;base64,{}');
                background-size: cover;
                background-position: center;
                filter: blur(1.5px);  /* Apply blur effect to the image */
                border-radius: 8px;
                margin-bottom: 40px;  /* Added bottom margin */
            }

            /* Text overlay on top of the image */
            .hero-text {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: white;
                font-family: 'Tinos', serif;
                font-size: 36px;
                font-weight: 700;
                text-align: center;
                text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
            }

            /* Icon styling */
            .icon {
                font-size: 24px;
                margin-right: 10px;
                color: #002244;
            }
        </style>
    """,
    unsafe_allow_html=True)

    # Check if the image exists and encode it as base64 string for embedding
    if os.path.exists(image_path):
        # Read the image and encode it as base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()

        # Hero Image with Text Overlay (blurred image with bottom margin)
        st.markdown(f'<div class="hero-image-container" style="background-image: url(\'data:image/jpeg;base64,{encoded_image}\');"></div><div class="hero-text">Optimisez la Résilience de Votre Institution Financière avec l\'Outil de Stress Test</div>', unsafe_allow_html=True)
    else:
        st.error("L'image est introuvable. Assurez-vous qu'elle est bien placée au bon endroit.")

    # Explanation Section with professional icons
    st.write(
        """
        Bienvenue sur notre plateforme dédiée à l’évaluation de la résilience financière des banques. Développée pour répondre aux exigences réglementaires nationales et européennes, notre solution de stress testing vous permet d'analyser l'impact des scénarios macroéconomiques, idiosyncratiques et combinés sur vos **ratios réglementaires**.

        #### Ce que notre outil vous permet de faire :
        
        <ul>
            <li><strong>Simuler des scénarios de stress</strong>: Analysez la résistance de votre banque face à différents événements économiques et géopolitiques.</li>
            <li><strong>Évaluer la conformité réglementaire</strong>: Assurez-vous que vos résultats respectent les normes définies par la <strong>BCE</strong>.</li>
            <li><strong>Visualiser l'impact sur les ratios financiers</strong>: Interprétez facilement les effets des scénarios sur vos <strong>ratios de liquidité</strong> et autres indicateurs essentiels.</li>
            <li><strong>Tableau de bord interactif</strong>: Accédez à des graphiques détaillés pour mieux comprendre les résultats et ajuster vos stratégies financières.</li>
        </ul>
        """
    , unsafe_allow_html=True)

    
    # Call-to-action button to redirect to "Importation des Données"
    if st.button("Commencer l'Analyse"):
        # Set session state to navigate to the "Importation des Données" page
        st.session_state.selected_page = "Importation des Données"
