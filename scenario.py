import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import backend_stress_test as bst

def show():
    st.title("Scénario de Stress Test: Retrait Massif des Dépôts")
    
    # Initialiser la session state pour éviter les erreurs
    if "resultats_stress_test" not in st.session_state:
        st.session_state.resultats_stress_test = None
        
    # Afficher un message d'information au démarrage
    if st.session_state.resultats_stress_test is None:
        st.info("👇 Configurez les paramètres du stress test ci-dessous et cliquez sur 'Exécuter le stress test' pour commencer l'analyse.")
    
    # Créer une section pour les paramètres dans la page principale
    st.header("Paramètres du stress test")
    
    # Utiliser des colonnes pour organiser les paramètres
    col1, col2 = st.columns(2)
    
    with col1:
        # Paramètre p1: pourcentage de diminution des dépôts
        p1 = st.slider(
            "Pourcentage de diminution des dépôts (%)",
            min_value=5,
            max_value=50,
            value=15,
            step=5
        ) / 100.0  # Conversion en décimal
        
        # Paramètre p2: horizon d'absorption du choc
        p2 = st.slider(
            "Horizon d'absorption du choc (années)",
            min_value=1,
            max_value=5,
            value=1,
            step=1
        )
        
        # Paramètre p3: mode d'écoulement (uniquement si p2 > 1)
        p3 = 'equitable'
        if p2 > 1:
            p3_options = {'Équitable': 'equitable', 'Première année seulement': 'premiere_annee'}
            p3 = st.radio(
                "Mode d'écoulement du choc",
                options=list(p3_options.keys())
            )
            p3 = p3_options[p3]
    
    with col2:
        # Paramètre année de départ
        annee_depart = st.selectbox(
            "Année de départ",
            options=["2024", "2025", "2026", "2027"],
            index=1  # 2025 par défaut
        )
        
        # Paramètres de contrepartie
        st.subheader("Contreparties impactées")
        st.markdown("Répartition de l'impact du retrait des dépôts:")
        
        # Utiliser des sous-colonnes pour les sliders de poids
        subcol1, subcol2 = st.columns(2)
        with subcol1:
            poids_portefeuille = st.slider(
                "Portefeuille (%)",
                min_value=0,
                max_value=100,
                value=50,
                step=5
            ) / 100.0
        
        with subcol2:
            poids_creances = st.slider(
                "Créances bancaires (%)",
                min_value=0,
                max_value=100,
                value=50,
                step=5
            ) / 100.0
        
        # Vérifier que la somme est égale à 100%
        total_poids = poids_portefeuille + poids_creances
        if not np.isclose(total_poids, 1.0):
            st.warning(f"La somme des pourcentages doit être égale à 100%. Actuellement: {total_poids*100:.0f}%")
            st.info("Ajustement automatique appliqué.")
            # Normalisation
            poids_portefeuille = poids_portefeuille / total_poids
            poids_creances = poids_creances / total_poids
    
    # Bouton pour exécuter le stress test, placé après les paramètres
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Exécuter le stress test", use_container_width=True):
            with st.spinner("Exécution du stress test en cours..."):
                resultats = bst.executer_stress_test_retrait_depots(
                    p1=p1,
                    p2=p2,
                    p3=p3,
                    annee_depart=annee_depart,
                    poids_portefeuille=poids_portefeuille,
                    poids_creances=poids_creances
                )
                
                if "erreur" in resultats:
                    st.error(f"Erreur: {resultats['erreur']}")
                else:
                    st.session_state.resultats_stress_test = resultats
                    st.success("Stress test exécuté avec succès!")
    
    # Séparateur visuel entre les paramètres et les résultats
    if st.session_state.resultats_stress_test is not None:
        st.markdown("---")
    
    # Affichage des résultats si disponibles
    if "resultats_stress_test" in st.session_state and st.session_state.resultats_stress_test is not None:
        afficher_resultats(st.session_state.resultats_stress_test)


def afficher_resultats(resultats):
    # Check if results are valid
    if resultats is None:
        st.warning("Aucun résultat disponible. Veuillez exécuter le stress test.")
        return
        
    st.header("Résultats du stress test")
    
    # 1. Paramètres utilisés
    with st.expander("Paramètres utilisés", expanded=True):
        # Check if parameters exist in the results dictionary
        if "parametres" in resultats:
            params = resultats["parametres"]
        else:
            # Fallback to accessing parameters directly from the results dictionary
            params = {
                "p1": resultats.get("p1", 0),
                "p2": resultats.get("p2", 1),
                "p3": resultats.get("p3", "equitable"),
                "annee_depart": resultats.get("annee_depart", "2025"),
                "poids_portefeuille": resultats.get("poids_portefeuille", 0.5),
                "poids_creances": resultats.get("poids_creances", 0.5)
            }
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Diminution des dépôts:** {params['p1']*100:.1f}%")
            st.write(f"**Horizon d'absorption:** {params['p2']} année(s)")
            st.write(f"**Mode d'écoulement:** {params['p3']}")
        with col2:
            st.write(f"**Année de départ:** {params['annee_depart']}")
            st.write(f"**Répartition Portefeuille:** {params['poids_portefeuille']*100:.1f}%")
            st.write(f"**Répartition Créances bancaires:** {params['poids_creances']*100:.1f}%")
    
    # 2. Impact sur le bilan
    with st.expander("Impact sur le bilan", expanded=True):
        postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
        
        # Vérifier si les données du bilan sont disponibles
        if "bilan_original_impacte" not in resultats or "bilan_impacte" not in resultats:
            st.warning("Les données du bilan ne sont pas disponibles dans les résultats.")
            return
            
        # Extraire les données originales et stressées
        bilan_orig = resultats["bilan_original_impacte"]
        bilan_stress = resultats["bilan_impacte"]
        
        # Vérifier que les données sont bien des DataFrames
        if not isinstance(bilan_orig, pd.DataFrame) or not isinstance(bilan_stress, pd.DataFrame):
            st.warning("Les données du bilan ne sont pas au format attendu (DataFrame).")
            return
            
        # Préparer les données pour l'affichage
        try:
            annees = [str(int(params['annee_depart']) + i) for i in range(params['p2'])]
            
            if not annees:
                annees = [params['annee_depart']]
        except (KeyError, ValueError, TypeError):
            st.warning("Problème avec les paramètres d'années. Utilisation de l'année par défaut.")
            annees = ["2025"]
        
        for annee in annees:
            if annee not in bilan_orig.columns or annee not in bilan_stress.columns:
                st.warning(f"Les données pour l'année {annee} ne sont pas disponibles.")
                continue
                
            st.subheader(f"Impact pour l'année {annee}")
            
            # Filtrer les postes qui existent dans les deux bilans
            valid_postes = [p for p in postes_concernes if p in bilan_orig.index and p in bilan_stress.index]
            
            if not valid_postes:
                st.warning("Aucun poste du bilan correspondant n'a été trouvé.")
                continue
                
            # Créer un dataframe pour comparer les valeurs
            comparaison = pd.DataFrame()
            comparaison["Poste"] = valid_postes
            comparaison["Valeur d'origine"] = [bilan_orig.loc[poste, annee] for poste in valid_postes]
            comparaison["Valeur stressée"] = [bilan_stress.loc[poste, annee] for poste in valid_postes]
            comparaison["Variation absolue"] = comparaison["Valeur stressée"] - comparaison["Valeur d'origine"]
            comparaison["Variation (%)"] = (comparaison["Variation absolue"] / comparaison["Valeur d'origine"]) * 100
            
            st.dataframe(comparaison.style.format({
                "Valeur d'origine": "{:,.2f}",
                "Valeur stressée": "{:,.2f}",
                "Variation absolue": "{:,.2f}",
                "Variation (%)": "{:.2f}%"
            }))
            
            # Graphique de comparaison
            fig, ax = plt.subplots(figsize=(10, 5))
            x = np.arange(len(postes_concernes))
            width = 0.35
            
            # Barres pour les valeurs originales et stressées
            rects1 = ax.bar(x - width/2, comparaison["Valeur d'origine"], width, label='Original')
            rects2 = ax.bar(x + width/2, comparaison["Valeur stressée"], width, label='Stressé')
            
            ax.set_title(f'Comparaison des valeurs pour {annee}')
            ax.set_xticks(x)
            ax.set_xticklabels([p.split(' ')[0] for p in postes_concernes])
            ax.legend()
            
            st.pyplot(fig)
    
    # 3. Impact sur le ratio LCR
    with st.expander("Impact sur le ratio LCR", expanded=True):
        lcr_original = resultats.get("lcr_original")
        lcr_stresse = resultats.get("lcr_stresse")
        delta_lcr = resultats.get("delta_lcr")
        
        if lcr_original is not None and lcr_stresse is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("LCR Original", f"{lcr_original:.2f}%")
            with col2:
                st.metric("LCR Stressé", f"{lcr_stresse:.2f}%")
            with col3:
                st.metric("Impact", f"{delta_lcr:.2f}%", 
                         delta=f"{-delta_lcr:.2f}%", 
                         delta_color="inverse")
            
            # Graphique LCR
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.bar(["LCR Original", "LCR Stressé"], [lcr_original, lcr_stresse], color=['green', 'orange'])
            ax.axhline(y=100, color='r', linestyle='-', label="Seuil réglementaire")
            ax.set_ylabel("Ratio LCR (%)")
            ax.set_title("Impact du stress test sur le ratio LCR")
            ax.legend()
            
            # Ajouter des étiquettes de valeur sur les barres
            for i, v in enumerate([lcr_original, lcr_stresse]):
                ax.text(i, v + 3, f"{v:.2f}%", ha='center')
                
            st.pyplot(fig)
            
            # Analyse de l'impact sur le LCR
            st.subheader("Analyse de l'impact")
            if lcr_stresse < 100:
                st.warning("⚠️ Le ratio LCR stressé est inférieur au seuil réglementaire de 100%.")
                st.write(f"La diminution de {delta_lcr:.2f}% du ratio LCR place la banque en dessous du seuil réglementaire, ce qui nécessiterait des mesures correctives.")
            else:
                st.success("✅ Le ratio LCR stressé reste au-dessus du seuil réglementaire de 100%.")
                st.write(f"Malgré une diminution de {delta_lcr:.2f}%, le ratio LCR reste conforme aux exigences réglementaires.")
    
    # 4. Évolution temporelle (si horizon > 1 an)
    if params.get("p2", 1) > 1:
        with st.expander("Évolution temporelle des indicateurs", expanded=True):
            annees = [str(int(params.get("annee_depart", "2025")) + i) for i in range(params.get("p2", 1))]
            
            # Si les résultats contiennent l'évolution des LCR
            if "lcr_evolution" in resultats:
                st.subheader("Évolution du ratio LCR")
                lcr_evol = resultats["lcr_evolution"]
                
                # Créer un dataframe pour l'évolution
                df_evol = pd.DataFrame({
                    "Année": annees,
                    "LCR": lcr_evol
                })
                
                # Graphique d'évolution
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df_evol["Année"], df_evol["LCR"], marker='o', linewidth=2)
                ax.axhline(y=100, color='r', linestyle='--', label="Seuil réglementaire")
                ax.set_ylabel("Ratio LCR (%)")
                ax.set_title("Évolution du ratio LCR sur la période de stress")
                ax.grid(True, linestyle='--', alpha=0.7)
                ax.legend()
                
                st.pyplot(fig)
                
                # Tableau d'évolution
                st.dataframe(df_evol.style.format({
                    "LCR": "{:.2f}%"
                }))
            
            # Évolution des postes du bilan
            st.subheader("Évolution des postes du bilan")
            postes_concernes = ["Depots clients (passif)", "Portefeuille", "Créances banques autres"]
            
            # Check if the balance sheet data exists in the expected format
            if "bilan_impacte" in resultats and isinstance(resultats["bilan_impacte"], pd.DataFrame):
                bilan_stress = resultats["bilan_impacte"]
                
                # Ensure all required posts and years exist in the DataFrame
                valid_postes = [p for p in postes_concernes if p in bilan_stress.index]
                valid_annees = [a for a in annees if a in bilan_stress.columns]
                
                if valid_postes and valid_annees:
                    # Préparer les données pour le graphique
                    df_evol_bilan = pd.DataFrame()
                    for poste in valid_postes:
                        df_evol_bilan[poste] = [bilan_stress.loc[poste, annee] if annee in bilan_stress.columns else 0 
                                               for annee in valid_annees]
                    df_evol_bilan.index = valid_annees
                else:
                    st.warning("Certains postes ou années ne sont pas disponibles dans les résultats.")
                    df_evol_bilan = pd.DataFrame(index=annees)
            else:
                st.warning("Les données du bilan ne sont pas disponibles dans le format attendu.")
                df_evol_bilan = pd.DataFrame(index=annees)
            
            # Graphique d'évolution
            fig, ax = plt.subplots(figsize=(10, 6))
            for poste in postes_concernes:
                if poste in df_evol_bilan.columns:
                    ax.plot(df_evol_bilan.index, df_evol_bilan[poste], marker='o', linewidth=2, label=poste)
            
            ax.set_ylabel("Valeur")
            ax.set_title("Évolution des postes du bilan sur la période de stress")
            ax.grid(True, linestyle='--', alpha=0.7)
            ax.legend()
            
            st.pyplot(fig)
            
            # Tableau d'évolution
            if not df_evol_bilan.empty and df_evol_bilan.columns.size > 0:
                st.dataframe(df_evol_bilan.T.style.format("{:,.2f}"))
    
    # 5. Conclusion et recommandations
    with st.expander("Conclusion et recommandations", expanded=True):
        st.subheader("Synthèse de l'analyse")
        
        # Impact sur les dépôts
        impact_depots = params.get("p1", 0) * 100
        st.write(f"Le scénario de stress test simule un retrait de {impact_depots:.1f}% des dépôts clients sur une période de {params.get('p2', 1)} année(s).")
        
        # Impact sur le LCR
        if "lcr_stresse" in resultats and "lcr_original" in resultats:
            impact_lcr = resultats["delta_lcr"]
            st.write(f"Ce retrait massif entraîne une diminution de {impact_lcr:.2f}% du ratio LCR.")
            
            if resultats["lcr_stresse"] < 100:
                st.error("⚠️ Le ratio LCR stressé est inférieur au seuil réglementaire.")
                st.write("Recommandations:")
                st.write("- Augmenter les actifs liquides de haute qualité (HQLA)")
                st.write("- Diversifier les sources de financement")
                st.write("- Mettre en place un plan d'urgence de liquidité")
                st.write("- Évaluer la possibilité de recourir à des lignes de crédit supplémentaires")
            elif resultats["lcr_stresse"] < 110:
                st.warning("⚠️ Le ratio LCR stressé est proche du seuil réglementaire.")
                st.write("Recommandations:")
                st.write("- Surveiller attentivement l'évolution du ratio LCR")
                st.write("- Envisager d'augmenter le coussin d'actifs liquides")
                st.write("- Réviser la stratégie de gestion des liquidités")
            else:
                st.success("✅ La banque maintient un ratio LCR satisfaisant malgré le stress.")
                st.write("Recommandations:")
                st.write("- Maintenir la politique actuelle de gestion des liquidités")
                st.write("- Continuer à surveiller régulièrement les indicateurs de liquidité")
        
        # Graphique radar d'impact global
        st.subheader("Impact global")
        # Création d'un graphique radar pour visualiser l'impact global
        categories = ['LCR', 'Dépôts', 'Portefeuille', 'Créances']
        
        # Calculer les valeurs normalisées pour chaque catégorie
        lcr_impact = min(100, (resultats["delta_lcr"] / 50) * 100) if "delta_lcr" in resultats else 0
        depots_impact = min(100, (params.get("p1", 0) * 100))
        portefeuille_impact = min(100, (params.get("p1", 0) * params.get("poids_portefeuille", 0.5) * 100))
        creances_impact = min(100, (params.get("p1", 0) * params.get("poids_creances", 0.5) * 100))
        
        values = [lcr_impact, depots_impact, portefeuille_impact, creances_impact]
        
        # Créer le graphique radar
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, polar=True)
        
        # Plot
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
        values = values + [values[0]]
        angles = angles + [angles[0]]
        categories = categories + [categories[0]]
        
        ax.plot(angles, values, 'o-', linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        ax.set_thetagrids(np.degrees(angles[:-1]), categories[:-1])
        ax.set_ylim(0, 100)
        ax.set_title("Impact global du stress test (%)")
        ax.grid(True)
        
        st.pyplot(fig)


if __name__ == "__main__":
    show()