import streamlit as st
import pandas as pd

# Fonction principale pour afficher l'interface de calcul des ratios baseline
def show():
    st.title("Calcul des Ratios Baseline")

    # Affichage du bilan de référence sous forme de tableau
    st.subheader("Bilan de Référence")
    st.markdown('<style>table{width: 100% !important;}</style>', unsafe_allow_html=True)

    data = {
        "Catégorie": [
            '<span style="color: #00A1E4;"><b>ACTIFS</b></span>',
            "Caisse et avoirs auprès de la BCT, CCP et TGT",
            "Créances sur les établissements bancaires et financiers",
            "Créances sur la clientèle",
            "Portefeuille-titres commercial",
            "Portefeuille d'investissement",
            "Titres mis en équivalence",
            "Valeurs immobilisées",
            "Ecart d'acquisition net (GoodWill)",
            "Autres actifs",
            '<span style="background-color: #002244; color: white; padding: 7px;"><b>Total des actifs</b></span>',
            '<span style="color: #00A1E4;"><b>PASSIFS</b></span>',
            "Banque Centrale et CCP",
            "Dépôts et avoirs des établissements bancaires et financiers",
            "Dépôts et avoirs de la clientèle",
            "Emprunts et ressources spéciales",
            "Autres passifs",
            '<span style="background-color: #002244; color: white; padding: 7px;"><b>Total des passifs</b></span>',
            '<span style="color: #00A1E4;"><b>INTERETS MINORITAIRES</b></span>',
            "Part des minoritaires dans les réserves consolidées",
            "Part des minoritaires dans le résultat consolidé",
            '<span style="background-color: #002244; color: white; padding: 7px;"><b>Total des intérêts minoritaires</b></span>',
            '<span style="color: #00A1E4;"><b>CAPITAUX PROPRES</b></span>',
            "Capital",
            "Réserves consolidées",
            "Autres capitaux propres",
            "Résultat consolidé de l'exercice",
            '<span style="background-color: #002244; color: white; padding: 7px;"><b>Total des capitaux propres</b></span>',
            '<span style="background-color: #002244; color: white; padding: 7px;"><b>Total des passifs et des capitaux propres</b></span>'
        ],
        "Montant (TND)": [
            "", 332882, 4634310, 12354692, 1040106, 3895501, 10428, 694439, 44199, 656627, 23663184,
            "", 3951, 605858, 18069080, 561865, 1392496, 20633250,
            "", 823988, 47191, 871179,
            "", 178500, 1621661, 3, 358591, 2158755, 23663184
        ]
    }
    df = pd.DataFrame(data)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Sélection des ratios à calculer
    st.subheader("Sélection des Ratios à Calculer")
    ratios = {
        "LCR": {
            "definition": "Le ratio de liquidité à court terme mesure la capacité de la banque à faire face à ses sorties de trésorerie à 30 jours.",
            "formule": r"LCR = \frac{\text{Actifs liquides de haute qualité}}{\text{Sorties nettes de trésorerie sur 30 jours}}"
        },
        "NSFR": {
            "definition": "Le ratio de financement stable à long terme évalue si les ressources stables couvrent les besoins stables.",
            "formule": r"NSFR = \frac{\text{Financements stables disponibles}}{\text{Besoins en financements stables}}"
        },
        "Levier": {
            "definition": "Ce ratio mesure le niveau d'endettement de la banque en comparant ses fonds propres au total de ses expositions.",
            "formule": r"Levier = \frac{\text{Fonds propres de base}}{\text{Total des expositions}}"
        },
        "Solvabilité": {
            "definition": "Il évalue la capacité de la banque à absorber les pertes par rapport à ses risques pondérés.",
            "formule": r"Solvabilité = \frac{\text{Fonds propres réglementaires}}{\text{Risques pondérés}}"
        }
    }

    selected_ratios = st.multiselect("Choisissez les ratios à calculer :", list(ratios.keys()))

    for ratio in selected_ratios:
        st.write(f"### {ratio}")
        st.write(f"**Définition :** {ratios[ratio]['definition']}")
        st.latex(ratios[ratio]['formule'])

        if st.button(f"Calculer {ratio}", key=ratio):
            # Simuler un calcul avec des valeurs arbitraires pour démonstration
            resultat = round(100 * (0.8 if ratio == "LCR" else 0.9), 2)  # Exemple de valeurs calculées
            interpretation = "Satisfaisant" if resultat >= 100 else "Insuffisant"

            st.write(f"**Résultat :** {resultat} %")
            st.write(f"**Interprétation :** {interpretation}")

    # Bouton pour passer aux scénarios de stress test
    if st.button("Procéder aux choix des scénarios de stress test"):
        st.session_state.selected_page = "Choix du Scénario"
