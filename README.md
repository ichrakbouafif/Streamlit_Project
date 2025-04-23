# Stress Testing App

Cette application Streamlit permet de simuler des tests de résistance bancaire conformément aux exigences réglementaires (BCE).

## 🌐 Fonctionnalités
- Importation de fichiers réglementaires (COREP, Bilan, Capital Planning)
- Calcul des ratios de liquidité
- Simulation de scénarios de stress (idiosyncratique, macroéconomique, combiné)
- Visualisation interactive des résultats

## 📁 Architecture du Projet

5.	stress_testing_app/
6.	│── app.py                 # Main Streamlit app
7.	│── requirements.txt        # Dependencies
8.	│── data/                   # Folder for uploaded files
9.	│── interfaces/                # interfaces of the project
10.	│   │── homepage.py  #
11.	│   │── calcul_ratios   #
12.	│   │── importation_donnees#
13.	│   │── choix_scenario #
14.	│   │── resultats_graphiques #
15.	│── modules/                # Backend processing modules
16.	│   │── data_processing.py  # Handles file uploads & data extraction
17.	│   │── stress_test.py      # Applies stress test scenarios
18.	│   │── visualization.py    # Generates graphs & reports
19.	│── assets/                 # Images, CSS, or additional resources
20.	│── reports/                # Generated reports
21.	│── config.py               # Configurations (thresholds, API keys if needed)
22.	│── README.md               # Project documentation

Pour lancer l'application

1. Cloner le dépôt
```bash
git clone <URL_DU_REPO>
cd stress_testing_app

2. Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

3. Installer les dépendances
pip install -r requirements.txt

4. Lancer l'application
streamlit run app.py

Fichiers attendus
-COREP.xlsx
-Bilan.xlsx
-CapitalPlanning.xlsx

the color palette used :
#F8F9FA (Light Gray) for side bar Background
#DEDEDE (Light Gray) – Backgrounds, dividers, or neutral elements.

#D93954 (Dark Red-Pink) – Alerts, warnings, or key call-to-action buttons.

#E0301E (Bright Red) – Critical errors, failures, or urgent warnings.

#FFB600 (Bright Yellow-Orange) – Warnings, notifications, or highlights.

#175C2C (Dark Green) – Success messages, confirmations, or stability indicators.






Auteurs: Echrak Bouafif & Nour Jeljeli
Développé dans le cadre d’un projet de fin d’études chez PwC Tunisie - Risk Services.