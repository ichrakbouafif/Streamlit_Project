import pandas as pd

def charger_feuille_73(file_path, sheet_name='C7300_TOTAL'):
    """
    Charge et nettoie la feuille 73 du fichier COREP pour préparer le calcul du LCR.
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=9)
        # Nettoyages
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(how='all', inplace=True)
        df.columns = [str(col).strip() for col in df.columns]
        df.reset_index(drop=True, inplace=True)

        # Convertir les colonnes de ammount , weight , outflow 
        target_cols = ['0010','0050', '0060']
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()
