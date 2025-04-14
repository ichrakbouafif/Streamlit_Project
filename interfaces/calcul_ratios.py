import streamlit as st
import pandas as pd

def show():
    st.title("Calcul des Ratios Baseline")

    # ====================== BILAN DE RÉFÉRENCE ======================
    st.subheader("Bilan de Référence")
    st.markdown('<style>table{width: 100% !important;}</style>', unsafe_allow_html=True)

    data = {
        "Catégorie": [
            '<span style="color: #175C2C;"><b>ACTIFS</b></span>',
            "Caisse et avoirs auprès de la BCT, CCP et TGT",
            "Créances sur les établissements bancaires et financiers",
            "Créances sur la clientèle",
            "Portefeuille-titres commercial",
            "Portefeuille d'investissement",
            "Titres mis en équivalence",
            "Valeurs immobilisées",
            "Ecart d'acquisition net (GoodWill)",
            "Autres actifs",
            '<span style="background-color: #175C2C; color: white; padding: 7px;"><b>Total des actifs</b></span>',
            '<span style="color: #175C2C;"><b>PASSIFS</b></span>',
            "Banque Centrale et CCP",
            "Dépôts et avoirs des établissements bancaires et financiers",
            "Dépôts et avoirs de la clientèle",
            "Emprunts et ressources spéciales",
            "Autres passifs",
            '<span style="background-color: #175C2C; color: white; padding: 7px;"><b>Total des passifs</b></span>',
            '<span style="color: #175C2C;"><b>INTERETS MINORITAIRES</b></span>',
            "Part des minoritaires dans les réserves consolidées",
            "Part des minoritaires dans le résultat consolidé",
            '<span style="background-color: #175C2C; color: white; padding: 7px;"><b>Total des intérêts minoritaires</b></span>',
            '<span style="color: #175C2C;"><b>CAPITAUX PROPRES</b></span>',
            "Capital",
            "Réserves consolidées",
            "Autres capitaux propres",
            "Résultat consolidé de l'exercice",
            '<span style="background-color: #175C2C; color: white; padding: 7px;"><b>Total des capitaux propres</b></span>',
            '<span style="background-color: #175C2C; color: white; padding: 7px;"><b>Total des passifs et des capitaux propres</b></span>'
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

    # ====================== HORIZON DE STRESS TEST ======================
    st.subheader("Horizon de Stress Test")
    horizon = st.number_input("Durée de l'horizon de stress test (en années)", min_value=1, max_value=10, value=3)

    # ====================== RATIOS DICTIONARY ======================
    ratios = {
        "LCR": {
            "definition": """Le ratio de liquidité à court terme mesure la capacité de la banque à faire face à ses sorties de trésorerie à 30 jours.""",
            "formule": r"LCR = \frac{\text{Actifs liquides de haute qualité}}{\text{Sorties nettes de trésorerie sur 30 jours}}",
            "composants": [
                "Actifs liquides de haute qualité (par exemple : bons du Trésor, obligations d'État)",
                "Sorties nettes de trésorerie sur 30 jours (composées de remboursements de prêts, de retraits de dépôts, etc.)"
            ],
            "column": ["Actifs liquides de haute qualité", "Sorties nettes de trésorerie sur 30 jours"],
            "interpretation": """Un LCR supérieur à 100 % signifie que la banque dispose d'une réserve suffisante d'actifs liquides pour faire face à ses obligations à court terme.""",
            "baseline_value": 120,
            "projected_values": [115, 110, 105, 130, 150],
            "numerator": [150, 145, 140, 200, 320],
            "denominator": [130, 132, 135, 140, 160]
        },
        "NSFR": {
            "definition": """Le ratio de financement stable à long terme évalue si les ressources stables de la banque couvrent ses besoins stables à long terme.""",
            "formule": r"NSFR = \frac{\text{Financements stables disponibles}}{\text{Besoins en financements stables}}",
            "composants": [
                "Financements stables disponibles (par exemple : dépôts à long terme, fonds propres)",
                "Besoins en financements stables (correspond aux besoins de la banque pour financer ses actifs à long terme)"
            ],
            "column": ["Financements stables disponibles", "Besoins en financements stables"],
            "interpretation": """Un NSFR supérieur à 100 % indique que la banque dispose de ressources financières stables suffisantes pour soutenir ses activités à long terme.""",
            "baseline_value": 105,
            "projected_values": [102, 100, 98, 70, 40],
            "numerator": [200, 190, 180, 140, 150],
            "denominator": [190, 188, 185, 145, 180]
        },
        "Levier": {
            "definition": """Le ratio de levier mesure le niveau d'endettement de la banque en comparant ses fonds propres au total de ses expositions.""",
            "formule": r"Levier = \frac{\text{Fonds propres de base}}{\text{Total des expositions}}",
            "composants": [
                "Fonds propres de base (par exemple : capital social, réserves consolidées)",
                "Total des expositions (y compris les prêts, titres, dérivés, engagements)"
            ],
            "column": ["Fonds propres de base", "Total des expositions"],
            "interpretation": """Un ratio de levier élevé indique une banque plus robuste, avec une plus grande capacité à absorber les pertes.""",
            "baseline_value": 0.1,
            "projected_values": [0.11, 0.13, 0.16, 0.12, 0.17],
            "numerator": [10, 12, 14, 17, 19],
            "denominator": [100, 92, 88, 97, 99]
        },
        "Solvabilité": {
            "definition": """Le ratio de solvabilité mesure la capacité d'une banque à absorber les pertes par rapport à ses actifs pondérés par le risque.""",
            "formule": r"Solvabilité = \frac{\text{Fonds propres réglementaires}}{\text{Risques pondérés}}",
            "composants": [
                "Fonds propres réglementaires (capital de base et réserves)",
                "Risques pondérés (actifs ajustés en fonction de leur risque, comme les prêts à faible ou à haut risque)"
            ],
            "column": ["Fonds propres réglementaires", "Risques pondérés"],
            "interpretation": """Un ratio de solvabilité élevé montre que la banque a suffisamment de capital pour couvrir ses risques.""",
            "baseline_value": 12,
            "projected_values": [11.8, 11.5, 11.2, 15.5, 13],
            "numerator": [120, 118, 115, 150, 120],
            "denominator": [1000, 1025, 1030, 1200, 1450]
        }
    }

    # ====================== MAIN CALCULATION LOGIC ======================
    if 'show_ratios' not in st.session_state:
        st.session_state.show_ratios = False

    if st.button("Calculer les Ratios"):
        st.session_state.show_ratios = not st.session_state.show_ratios

    if st.session_state.show_ratios:
        st.subheader("Ratios Réglementaires")
        
        for ratio, details in ratios.items():
            # Use expander for ratio details (no help button needed)
            with st.expander(f"Ratio {ratio}", expanded=False):
                st.write(f"**Définition:** {details['definition']}")
                st.latex(details["formule"])
                st.write("**Composants:**")
                for comp in details["composants"]:
                    st.write(f"- {comp}")
                st.write(f"**Interprétation:** {details['interpretation']}")
            
            # Show ratio table
            ratio_table = pd.DataFrame({
                "Valeur": ["Valeur de base"] + [f"Valeur projetée Année {i+1}" for i in range(horizon)],
                "Valeurs": [details["baseline_value"]] + details["projected_values"][:horizon],
                details["column"][0]: [details["numerator"][0]] + details["numerator"][:horizon],
                details["column"][1]: [details["denominator"][0]] + details["denominator"][:horizon]
            })
            st.table(ratio_table)
        
        # Tableau récapitulatif (original version)
        st.subheader("Résumé des Résultats")
        result_data = []
        
        for ratio, details in ratios.items():
            baseline_value = details["baseline_value"]
            projected_values = details["projected_values"]
            
            if ratio in ["LCR", "NSFR"]:
                compliance = "Conforme" if baseline_value >= 100 else "Non conforme"
            else:  # Levier et Solvabilité
                compliance = "Conforme" if baseline_value <= 1 else "Non conforme"
            
            result_data.append({
                "Ratio": ratio,
                "Valeur de base": baseline_value,
                **{f"Projeté Année {i+1}": projected_values[i] for i in range(horizon)},
                "Conformité": compliance
            })
        
        result_df = pd.DataFrame(result_data)
        
        # Fonction pour appliquer la couleur à la colonne conformité
        def apply_color(val):
            color = 'background-color:#175C2C; color: white;' if val == "Conforme" else 'background-color: #E0301E; color: white;'
            return color
        
        # Appliquer la couleur et convertir en HTML
        styled_df = result_df.style.applymap(apply_color, subset=["Conformité"])
        
        # Utiliser st.markdown pour afficher la table avec le format HTML
        st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    if st.button("Procéder aux choix du scénario"):
        st.session_state.selected_page = "Choix du Scénario"