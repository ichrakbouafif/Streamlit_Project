def appliquer_stress_tirage_pnu(bilan_df, pourcentage, inclure_corpo, inclure_retail, inclure_hypo, impact_dettes, impact_portefeuille):
    # Filtrer les lignes selon les segments cochés
    segments = []
    if inclure_corpo:
        segments.append("Corporate")
    if inclure_retail:
        segments.append("Retail")
    if inclure_hypo:
        segments.append("Hypothécaire")

    # Appliquer le tirage PNU sur les postes de créances concernées
    bilan_df = bilan_df.copy()
    mask = bilan_df["Poste"].isin(segments)
    bilan_df.loc[mask, "Montant"] *= (1 + pourcentage)

    # Appliquer l’impact sur les autres postes
    bilan_df.loc[bilan_df["Poste"] == "Dettes envers établissements de crédit", "Montant"] *= (1 - impact_dettes)
    bilan_df.loc[bilan_df["Poste"] == "Portefeuille", "Montant"] *= (1 - impact_portefeuille)

    return bilan_df
