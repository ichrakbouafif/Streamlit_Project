################## feuille_74 - Inflow  ##################
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
        # Rename the first column
        df.rename(columns={'Unnamed: 1': 'item'}, inplace=True)
        # Rename the second column
        df.rename(columns={'Unnamed: 2': 'row'}, inplace=True)

        return df

    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()

def calcul_inflows(df, row_number):
    """Calcule les inflows pour une ligne donnée cap 75%"""
    row = df[df['row'] == row_number]
    inflow = 0
    for amt_col, wgt_col in zip(['0010'], ['0080']):
        amt = row[amt_col].values[0] if amt_col in row else 0
        wgt = row[wgt_col].values[0] if wgt_col in row else 0
        if pd.notna(amt) and pd.notna(wgt):
            inflow += amt * wgt
    df.loc[df['row'] == row_number, '0140'] = inflow
    return inflow


# 1.1.1 Monies due from non-financial customers
def calcul_row_040(df):
    """Calcule les inflows de la ligne 040 (non-financial customers not principal repayment)."""
    return calcul_inflows(df, 40)

def calcul_row_060(df):
    """Calcule les inflows de la ligne 060 (retail customers)."""
    return calcul_inflows(df, 60)

def calcul_row_070(df):
    """Calcule les inflows de la ligne 070 (non-financial corporates)."""
    return calcul_inflows(df, 70)

def calcul_row_080(df):
    """Calcule les inflows de la ligne 080 (sovereigns, MLDBs, PSEs)."""
    return calcul_inflows(df, 80)

def calcul_row_090(df):
    """Calcule les inflows de la ligne 090 (other legal entities)."""
    return calcul_inflows(df, 90)

def calcul_row_050(df):
    """Calcule la valeur de la ligne 050 (somme des lignes 060 à 090)."""
    total = (calcul_row_060(df) + calcul_row_070(df) +
             calcul_row_080(df) + calcul_row_090(df))
    df.loc[df['row'] == 50, '0140'] = total
    return total

def calcul_row_030(df):
    """Calcule la valeur de la ligne 030 (somme des lignes 040 et 050)."""
    inflow_40 = calcul_row_040(df)
    inflow_50 = calcul_row_050(df)
    inflow_30 = inflow_40 +inflow_50
    df.loc[df['row'] == 30, '0140'] = inflow_30
    return inflow_30

# 1.1.2 Monies due from central banks and financial customers
def calcul_row_120(df):
    """Calcule les inflows de la ligne 120 (financial customers operational deposits symmetrical)."""
    return calcul_inflows(df, 120)

def calcul_row_130(df):
    """Calcule les inflows de la ligne 130 (financial customers operational deposits non-symmetrical)."""
    return calcul_inflows(df, 130)

def calcul_row_110(df):
    """Calcule la valeur de la ligne 110 (somme des lignes 120 et 130)."""
    inflow_120 = calcul_row_120(df)
    inflow_130 = calcul_row_130(df)
    inflow_110 = inflow_120 + inflow_130
    df.loc[df['row'] == 110, '0140'] =inflow_110
    return inflow_110

def calcul_row_150(df):
    """Calcule les inflows de la ligne 150 (central banks)."""
    return calcul_inflows(df, 150)

def calcul_row_160(df):
    """Calcule les inflows de la ligne 160 (financial customers)."""
    return calcul_inflows(df, 160)

def calcul_row_140(df):
    """Calcule la valeur de la ligne 140 (somme des lignes 150 et 160)."""
    inflow_140 = calcul_row_150(df) + calcul_row_160(df)
    df.loc[df['row'] == 140, '0140'] = inflow_140
    return inflow_140

def calcul_row_100(df):
    """Calcule la valeur de la ligne 100 (somme des lignes 110 et 140)."""
    inflow_100 = calcul_row_110(df) + calcul_row_140(df)
    df.loc[df['row'] == 100, '0140'] = inflow_100
    return inflow_100

# Other inflows sections
def calcul_row_170(df):
    """Calcule les inflows de la ligne 170 (promotional loan commitments)."""
    return calcul_inflows(df, 170)

def calcul_row_180(df):
    """Calcule les inflows de la ligne 180 (trade financing transactions)."""
    return calcul_inflows(df, 180)

def calcul_row_190(df):
    """Calcule les inflows de la ligne 190 (securities maturing within 30 days)."""
    return calcul_inflows(df, 190)

def calcul_row_201(df):
    """Calcule les inflows de la ligne 201 (loans with undefined end date)."""
    return calcul_inflows(df, 201)

def calcul_row_210(df):
    """Calcule les inflows de la ligne 210 (major index equity instruments)."""
    return calcul_inflows(df, 210)

def calcul_row_230(df):
    """Calcule les inflows de la ligne 230 (release of segregated accounts)."""
    return calcul_inflows(df, 230)

def calcul_row_240(df):
    """Calcule les inflows de la ligne 240 (inflows from derivatives)."""
    return calcul_inflows(df, 240)

def calcul_row_250(df):
    """Calcule les inflows de la ligne 250 (undrawn facilities from group/IPS)."""
    return calcul_inflows(df, 250)

def calcul_row_260(df):
    """Calcule les inflows de la ligne 260 (other inflows)."""
    return calcul_inflows(df, 260)

# 1.1 Inflows from unsecured transactions/deposits
def calcul_row_020(df):
    """Calcule la valeur de la ligne 020 (somme des lignes 030 à 260)."""
    total = (calcul_row_030(df) + calcul_row_100(df) + calcul_row_170(df) +
             calcul_row_180(df) + calcul_row_190(df) + calcul_row_201(df) +
             calcul_row_210(df) + calcul_row_230(df) + calcul_row_240(df) +
             calcul_row_250(df) + calcul_row_260(df))
    df.loc[df['row'] == 20, '0140'] = total
    return total

# 1.2 Inflows from secured lending and capital market-driven transactions
def calcul_row_269(df):
    """Calcule les inflows de la ligne 269 (Level 1 excl EHQ CB collateral)."""
    return calcul_inflows(df, 269)

def calcul_row_273(df):
    """Calcule les inflows de la ligne 273 (Level 1 EHQ CB collateral)."""
    return calcul_inflows(df, 273)

def calcul_row_277(df):
    """Calcule les inflows de la ligne 277 (Level 2A collateral)."""
    return calcul_inflows(df, 277)

def calcul_row_281(df):
    """Calcule les inflows de la ligne 281 (Level 2B residential/auto ABS)."""
    return calcul_inflows(df, 281)

def calcul_row_285(df):
    """Calcule les inflows de la ligne 285 (Level 2B covered bonds)."""
    return calcul_inflows(df, 285)

def calcul_row_289(df):
    """Calcule les inflows de la ligne 289 (Level 2B commercial/individuals ABS)."""
    return calcul_inflows(df, 289)

def calcul_row_293(df):
    """Calcule les inflows de la ligne 293 (other Level 2B collateral)."""
    return calcul_inflows(df, 293)

def calcul_row_267(df):
    """Calcule la valeur de la ligne 267 (somme des lignes 269 à 293)."""
    total = (calcul_row_269(df) + calcul_row_273(df) + calcul_row_277(df) +
             calcul_row_281(df) + calcul_row_285(df) + calcul_row_289(df) +
             calcul_row_293(df))
    df.loc[df['row'] == 267, '0140'] = total
    return total

def calcul_row_301(df):
    """Calcule les inflows de la ligne 301 (non-liquid equity collateral)."""
    return calcul_inflows(df, 301)

def calcul_row_303(df):
    """Calcule les inflows de la ligne 303 (other non-liquid collateral)."""
    return calcul_inflows(df, 303)

def calcul_row_299(df):
    """Calcule la valeur de la ligne 299 (somme des lignes 301 et 303)."""
    total = calcul_row_301(df) + calcul_row_303(df)
    df.loc[df['row'] == 299, '0140'] = total
    return total

def calcul_row_265(df):
    """Calcule la valeur de la ligne 265 (somme des lignes 267 et 299)."""
    inflow_267 = calcul_row_267(df)
    inflow_299 = calcul_row_299(df)
    df.loc[df['row'] == 265, '0140'] = inflow_267+ inflow_299
    return inflow_267 + inflow_299

# Non-central bank counterparty section
def calcul_row_309(df):
    """Calcule les inflows de la ligne 309 (Level 1 excl EHQ CB collateral)."""
    return calcul_inflows(df, 309)

def calcul_row_313(df):
    """Calcule les inflows de la ligne 313 (Level 1 EHQ CB collateral)."""
    return calcul_inflows(df, 313)

def calcul_row_317(df):
    """Calcule les inflows de la ligne 317 (Level 2A collateral)."""
    return calcul_inflows(df, 317)

def calcul_row_321(df):
    """Calcule les inflows de la ligne 321 (Level 2B residential/auto ABS)."""
    return calcul_inflows(df, 321)

def calcul_row_325(df):
    """Calcule les inflows de la ligne 325 (Level 2B covered bonds)."""
    return calcul_inflows(df, 325)

def calcul_row_329(df):
    """Calcule les inflows de la ligne 329 (Level 2B commercial/individuals ABS)."""
    return calcul_inflows(df, 329)

def calcul_row_333(df):
    """Calcule les inflows de la ligne 333 (other Level 2B collateral)."""
    return calcul_inflows(df, 333)

def calcul_row_307(df):
    """Calcule la valeur de la ligne 307 (somme des lignes 309 à 333)."""
    total = (calcul_row_309(df) + calcul_row_313(df) + calcul_row_317(df) +
             calcul_row_321(df) + calcul_row_325(df) + calcul_row_329(df) +
             calcul_row_333(df))
    df.loc[df['row'] == 307, '0140'] = total
    return total

def calcul_row_341(df):
    """Calcule les inflows de la ligne 341 (margin loans non-liquid collateral)."""
    return calcul_inflows(df, 341)

def calcul_row_343(df):
    """Calcule les inflows de la ligne 343 (non-liquid equity collateral)."""
    return calcul_inflows(df, 343)

def calcul_row_345(df):
    """Calcule les inflows de la ligne 345 (other non-liquid collateral)."""
    return calcul_inflows(df, 345)

def calcul_row_339(df):
    """Calcule la valeur de la ligne 339 (somme des lignes 341 à 345)."""
    inflow_341 = calcul_row_341(df)
    inflow_343 = calcul_row_343(df)
    inflow_345 = calcul_row_345(df)
    inflow_339 = inflow_341 + inflow_343 + inflow_345
    df.loc[df['row'] == 339, '0140'] = inflow_339
    return inflow_339


def calcul_row_305(df):
    """Calcule la valeur de la ligne 305 (somme des lignes 307 et 339)."""
    inflow_307 = calcul_row_307(df)
    inflow_339 = calcul_row_339(df)
    df.loc[df['row'] == 305, '0140'] = inflow_307 + inflow_339
    return inflow_307 + inflow_339

def calcul_row_263(df):
    """Calcule la valeur de la ligne 263 (somme des lignes 265 et 305)."""
    inflow_265 = calcul_row_265(df)
    inflow_305 = calcul_row_305(df)
    df.loc[df['row'] == 263, '0140'] = inflow_265 + inflow_305
    return inflow_265 + inflow_305


def calcul_row_410(df):
    """Calcule la valeur de la ligne 410 (same as line 010)."""
    total = calcul_inflows(df, 410)
    df.loc[df['row'] == 410, '0140'] = total
    return total

# Total inflows
''' def calcul_row_010(df):
    """Calcule la valeur de la ligne 010 (somme des lignes 020 et 263)."""
    total = calcul_row_020(df) + calcul_row_263(df) + calcul_row_410(df) - calcul_row_420(df) - calcul_row_430(df)
    # Sum up all capped and exempt values from children
    capped_75 = df.loc[df['Row'] == 20, '100'].values[0] + df.loc[df['Row'] == 263, '100'].values[0]
    capped_90 = df.loc[df['Row'] == 263, '110'].values[0]  # Only from secured transactions
    exempt = df.loc[df['Row'] == 20, '120'].values[0]  # Only from unsecured transactions
    df.loc[df['Row'] == 10, '100'] = capped_75, capped_90, exempt
    return total '''

def calcul_row_420(df):
    """Calcule la valeur de la ligne 420 (Difference for third country restrictions)."""
    adjustment = calcul_inflows(df, 420)
    df.loc[df['row'] == 420, '0140'] =adjustment
    return adjustment

def calcul_row_430(df):
    """Calcule la valeur de la ligne 430 (Excess inflows from related specialised CI)."""
    adjustment = calcul_inflows(df, 420)
    df.loc[df['row'] == 420, '0140'] = adjustment
    return adjustment

def calcul_row_00010(df):
    """Calcule la valeur de la ligne 010 (Total inflows after adjustments)."""
    # Calculate base components
    unsecured = calcul_row_020(df)
    secured = calcul_row_263(df)
    collateral_swaps = calcul_row_410(df)
    third_country_adjustment = calcul_row_420(df)
    specialised_ci_adjustment = calcul_row_430(df)

    # Calculate total with adjustments
    total = (unsecured + secured + collateral_swaps -
             third_country_adjustment - specialised_ci_adjustment)
    df.loc[df['row'] == 10, '0140'] = total
    return total

def calcul_inflow(df):
    inflow = calcul_row_00010(df)
    print(inflow)
    return inflow