import pandas as pd

def charger_feuille_72(file_path, sheet_name='C7200_TOTAL'):
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=8)
        df.dropna(axis=1, how='all', inplace=True)
        df.dropna(how='all', inplace=True)
        df.columns = [str(col).strip() for col in df.columns]
        df.reset_index(drop=True, inplace=True)

        target_cols = ['0010','0030', '0040']
        for col in target_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()
