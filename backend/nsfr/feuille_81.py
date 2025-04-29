import pandas as pd
def charger_feuille_81(file_path):
    """
    Charge et prépare la feuille 'C8100_TOTAL' du fichier COREP NSFR pour le recalcul du ASF.
    - Garde les colonnes montants (0010 à 0030) + les colonnes de pondération (0070 à 0070)
    - Respecte les NaN comme cellules non applicables (pas forcées à 0)
    - Ne crée pas de colonne supplémentaire : le ASF sera réécrit dans '0100'
    """
    try:
        
        # lire avec cette ligne comme en-tête
        df = pd.read_excel(file_path, sheet_name="C8100_TOTAL", header=9)

        # Nettoyages
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(how='all', inplace=True)
        df.columns = [str(col).strip() for col in df.columns]
        df.reset_index(drop=True, inplace=True)

        # Convertir les colonnes de montant (0010–0030) et pondération (0070–0090)
        target_cols = ['0010', '0020', '0030','0070','0080', '0090', '0100']
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Erreur lors du chargement/nettoyage de la feuille 81 : {e}")
        return None
