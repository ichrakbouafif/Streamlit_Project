import streamlit as st
import os
import base64

def show():
    # Get the absolute path of the image (move up one level)
    image_path = os.path.join(os.path.dirname(__file__), "..", "banking-ffinance.jpg")

    # Apply CSS styling
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

    # Check if the image exists and encode it as a base64 string for embedding
    if os.path.exists(image_path):
        # Read the image and encode it as base64
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()

        # Hero Image with Text Overlay (blurred image with bottom margin)
        st.markdown(f'<div class="hero-image-container" style="background-image: url(\'data:image/jpeg;base64,{encoded_image}\');"></div><div class="hero-text">Optimisez la Résilience de Votre Institution Financière avec notre Outil de Stress Testing Avancé</div>', unsafe_allow_html=True)
    else:
        st.error("L'image 'banking-ffinance.jpg' est introuvable. Assurez-vous qu'elle est bien placée au bon endroit.")

    # Explanation Section with professional icons
    st.write(
        """
        Bienvenue sur notre plateforme dédiée à l’évaluation de la résilience financière des banques. Développée pour répondre aux exigences réglementaires nationales et européennes, notre solution de stress testing vous permet d'analyser l'impact des scénarios macroéconomiques, idiosyncratiques et combinés sur vos **ratios réglementaires**.

        #### Ce que notre outil vous permet de faire :
        
        <ul>
            <li><span class="icon">📊</span><strong>Simuler des scénarios de stress</strong>: Analysez la résistance de votre banque face à différents événements économiques et géopolitiques.</li>
            <li><span class="icon">📜</span><strong>Évaluer la conformité réglementaire</strong>: Assurez-vous que vos résultats respectent les normes définies par la <strong>BCE</strong> et la <strong>BCT</strong>.</li>
            <li><span class="icon">📉</span><strong>Visualiser l'impact sur les ratios financiers</strong>: Interprétez facilement les effets des scénarios sur vos <strong>ratios de liquidité</strong> et autres indicateurs essentiels.</li>
            <li><span class="icon">📈</span><strong>Tableau de bord interactif</strong>: Accédez à des graphiques détaillés pour mieux comprendre les résultats et ajuster vos stratégies financières.</li>
        </ul>

        #### Pourquoi utiliser notre solution ?
        - **Conformité réglementaire** : Conformez-vous aux standards de la **Banque Centrale Européenne (BCE)** et de la **Banque Centrale de Tunisie (BCT)**.
        - **Prédiction des risques financiers** : Préparez-vous aux défis économiques imprévus grâce à une analyse précise et fiable.
        - **Interface utilisateur intuitive** : Utilisez une plateforme facile à naviguer, conçue pour les professionnels de la finance.
        
        ### Commencez à analyser la stabilité financière de votre institution dès aujourd'hui et préparez-vous pour l’avenir avec notre outil de stress testing avancé.
        """
    , unsafe_allow_html=True)

    # Call-to-action button to redirect to "Importation des Données"
    if st.button("Commencer l'Analyse"):
        # Set session state to navigate to the "Importation des Données" page
        st.session_state.selected_page = "Importation des Données"
        
