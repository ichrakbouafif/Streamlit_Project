import pandas as pd

def charger_feuille_74(file_path, sheet_name='C7400_TOTAL'):
    """
    Charge et nettoie la feuille 74 du fichier COREP pour préparer le calcul du LCR.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=9)
        # Nettoyages
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(how='all', inplace=True)
        df.columns = [str(col).strip() for col in df.columns]
        df.reset_index(drop=True, inplace=True)

        # Convertir les colonnes de montant (0010–0030) et pondération (0080–0100)
        target_cols = ['0010','0020', '0030','0080','0090', '0100']
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()
