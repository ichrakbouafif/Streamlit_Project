import pandas as pd
def charger_feuille_80(file_path):
    """
    Charge et prépare la feuille 'C8000_TOTAL' du fichier COREP NSFR pour le recalcul du RSF.
    - Garde les colonnes montants (0010 à 0040) + les colonnes de pondération (0050 à 0080)
    - Respecte les NaN comme cellules non applicables (pas forcées à 0)
    - Ne crée pas de colonne supplémentaire : le RSF sera réécrit dans '0130'
    """
    try:
        # Lire sans entête
        raw_df = pd.read_excel(file_path, sheet_name="C8000_TOTAL", header=None)

        # Trouver la ligne qui contient "Item"
        #header_row_index = raw_df[raw_df.apply(lambda row: row.astype(str).str.contains("Item", case=False).any(), axis=1)].index[0]

        # Relire avec cette ligne comme en-tête
        df = pd.read_excel(file_path, sheet_name="C8000_TOTAL", header=10)

        # Nettoyages
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(how='all', inplace=True)
        df.columns = [str(col).strip() for col in df.columns]
        df.reset_index(drop=True, inplace=True)

        # Convertir les colonnes de montant (0010–0040) et pondération (0090–0120)
        target_cols = ['0010', '0020', '0030', '0040', '0090', '0100', '0110', '0120', '0130']
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Erreur lors du chargement/nettoyage de la feuille 80 : {e}")
        return None
