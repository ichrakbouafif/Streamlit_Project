############# Feuille 72 - Liquidity Buffer #############
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

def calcul_row_0040(df):
    """Calcule les liquid assets pondérés de la ligne 0040 (Coins and banknotes)."""
    return calcul_liquid_assets(df, 40)

def calcul_row_0050(df):
    """Calcule les liquid assets pondérés de la ligne 0050 (Withdrawable central bank reserves)."""
    return calcul_liquid_assets(df, 50)

def calcul_row_0060(df):
    """Calcule les liquid assets pondérés de la ligne 0060 (Central bank assets)."""
    return calcul_liquid_assets(df, 60)

def calcul_row_0070(df):
    """Calcule les liquid assets pondérés de la ligne 0070 (Central government assets)."""
    return calcul_liquid_assets(df, 70)

def calcul_row_0080(df):
    """Calcule les liquid assets pondérés de la ligne 0080 (Regional government / local authorities assets)."""
    return calcul_liquid_assets(df, 80)

def calcul_row_0090(df):
    """Calcule les liquid assets pondérés de la ligne 0090 (Public Sector Entity assets)."""
    return calcul_liquid_assets(df, 90)

def calcul_row_0100(df):
    """Calcule les liquid assets pondérés de la ligne 0100 (Recognisable domestic and foreign currency central government and central bank assets)."""
    return calcul_liquid_assets(df, 100)

def calcul_row_0110(df):
    """Calcule les liquid assets pondérés de la ligne 0110 (Credit institution assets protected by Member State government or promotional lender)."""
    return calcul_liquid_assets(df, 110)

def calcul_row_0120(df):
    """Calcule les liquid assets pondérés de la ligne 0120 (Multilateral development bank and international organisations assets)."""
    return calcul_liquid_assets(df, 120)

def calcul_row_0130(df):
    """Calcule les liquid assets pondérés de la ligne 0130 (Qualifying CIU shares/units: underlying is coins/banknotes and/or central bank exposure)."""
    return calcul_liquid_assets(df, 130)

def calcul_row_0140(df):
    """Calcule les liquid assets pondérés de la ligne 0140 (Qualifying CIU shares/units: underlying is Level 1 assets excluding extremely high quality covered bonds)."""
    return calcul_liquid_assets(df, 140)

def calcul_row_0150(df):
    """Calcule les liquid assets pondérés de la ligne 0150 (Alternative Liquidity Approaches: Central bank credit facility)."""
    return calcul_liquid_assets(df, 150)

def calcul_row_0160(df):
    """Calcule les liquid assets pondérés de la ligne 0160 (Central institutions: Level 1 assets excl. EHQ CB considered liquid for the depositing CI)."""
    return calcul_liquid_assets(df, 160)

def calcul_row_0170(df):
    """Calcule les liquid assets pondérés de la ligne 0170 (ALA: Inclusion of Level 2A assets recognised as Level 1)."""
    return calcul_liquid_assets(df, 170)

#### calcul 1.1.1
def calcul_row_0030(df):
    """Calcule la valeur de la ligne 0030 (somme des lignes 0040 à 0170)."""
    val_0040 = calcul_row_0040(df)
    val_0050 = calcul_row_0050(df)
    val_0060 = calcul_row_0060(df)
    val_0070 = calcul_row_0070(df)
    val_0080 = calcul_row_0080(df)
    val_0090 = calcul_row_0090(df)
    val_0100 = calcul_row_0100(df)
    val_0110 = calcul_row_0110(df)
    val_0120 = calcul_row_0120(df)
    val_0130 = calcul_row_0130(df)
    val_0140 = calcul_row_0140(df)
    val_0150 = calcul_row_0150(df)
    val_0160 = calcul_row_0160(df)
    val_0170 = calcul_row_0170(df)
    total = (val_0040 + val_0050 + val_0060 + val_0070 + val_0080 + val_0090 +
             val_0100 + val_0110 + val_0120 + val_0130 + val_0140 + val_0150 +
             val_0160 + val_0170)
    df.loc[df['row'] == 30, '0040'] = total
    return total

def calcul_row_0190(df):
    """Calcule les liquid assets pondérés de la ligne 0190 (Extremely high quality covered bonds)."""
    return calcul_liquid_assets(df, 190)

def calcul_row_0200(df):
    """Calcule les liquid assets pondérés de la ligne 0200 (Qualifying CIU shares/units: EHQ covered bonds)."""
    return calcul_liquid_assets(df, 200)

def calcul_row_0210(df):
    """Calcule les liquid assets pondérés de la ligne 0210 (Central institutions: Level 1 EHQ covered bonds)."""
    return calcul_liquid_assets(df, 210)

#########################
def calcul_row_0180(df):
    """Calcule la valeur de la ligne 0180 (somme des lignes 0190 à 0210)."""
    val_0190 = calcul_row_0190(df)
    val_0200 = calcul_row_0200(df)
    val_0210 = calcul_row_0210(df)
    total = val_0190 + val_0200 + val_0210
    df.loc[df['row'] == 180, '0040'] = total
    return total

### 1.1
def calcul_row_0020(df):
    """Calcule la valeur de la ligne 0020 (somme des lignes 0030 et 0180)."""
    val_0030 = calcul_row_0030(df)
    val_0180 = calcul_row_0180(df)
    total = val_0030 + val_0180
    df.loc[df['row'] == 20, '0040'] = total
    return total



def calcul_row_0240(df):
    """Calcule les liquid assets pondérés de la ligne 0240 (Regional/local/PSE assets, Member State, RW20%)."""
    return calcul_liquid_assets(df, 240)

def calcul_row_0250(df):
    """Calcule les liquid assets pondérés de la ligne 0250 (CB/Gov/PSE assets, Third Country, RW20%)."""
    return calcul_liquid_assets(df, 250)

def calcul_row_0260(df):
    """Calcule les liquid assets pondérés de la ligne 0260 (High quality covered bonds, CQS2)."""
    return calcul_liquid_assets(df, 260)

def calcul_row_0270(df):
    """Calcule les liquid assets pondérés de la ligne 0270 (High quality covered bonds, Third Country, CQS1)."""
    return calcul_liquid_assets(df, 270)

def calcul_row_0280(df):
    """Calcule les liquid assets pondérés de la ligne 0280 (Corporate debt securities, CQS1)."""
    return calcul_liquid_assets(df, 280)

def calcul_row_0290(df):
    """Calcule les liquid assets pondérés de la ligne 0290 (Qualifying CIU shares/units: Level 2A assets)."""
    return calcul_liquid_assets(df, 290)

def calcul_row_0300(df):
    """Calcule les liquid assets pondérés de la ligne 0300 (Central institutions: Level 2A assets)."""
    return calcul_liquid_assets(df, 300)

### 1.2.1

def calcul_row_0230(df):
    """Calcule la valeur de la ligne 0230 (somme des lignes 0240 à 0300)."""
    val_0240 = calcul_row_0240(df)
    val_0250 = calcul_row_0250(df)
    val_0260 = calcul_row_0260(df)
    val_0270 = calcul_row_0270(df)
    val_0280 = calcul_row_0280(df)
    val_0290 = calcul_row_0290(df)
    val_0300 = calcul_row_0300(df)
    total = (val_0240 + val_0250 + val_0260 + val_0270 +
             val_0280 + val_0290 + val_0300)
    df.loc[df['row'] == 230, '0040'] = total
    return total

def calcul_row_0320(df):
    """Calcule les liquid assets pondérés de la ligne 0320 (Asset-backed securities, residential, CQS1)."""
    return calcul_liquid_assets(df, 320)

def calcul_row_0330(df):
    """Calcule les liquid assets pondérés de la ligne 0330 (Asset-backed securities, auto, CQS1)."""
    return calcul_liquid_assets(df, 330)

def calcul_row_0340(df):
    """Calcule les liquid assets pondérés de la ligne 0340 (High quality covered bonds, RW35%)."""
    return calcul_liquid_assets(df, 340)

def calcul_row_0350(df):
    """Calcule les liquid assets pondérés de la ligne 0350 (Asset-backed securities, commercial/individuals, Member State, CQS1)."""
    return calcul_liquid_assets(df, 350)

def calcul_row_0360(df):
    """Calcule les liquid assets pondérés de la ligne 0360 (Corporate debt securities, CQS2/3)."""
    return calcul_liquid_assets(df, 360)

def calcul_row_0370(df):
    """Calcule les liquid assets pondérés de la ligne 0370 (Corporate debt - non-interest bearing, for religious reasons, CQS1/2/3)."""
    return calcul_liquid_assets(df, 370)

def calcul_row_0380(df):
    """Calcule les liquid assets pondérés de la ligne 0380 (Shares included in major stock index)."""
    return calcul_liquid_assets(df, 380)

def calcul_row_0390(df):
    """Calcule les liquid assets pondérés de la ligne 0390 (Non-interest bearing assets, for religious reasons, CQS3-5)."""
    return calcul_liquid_assets(df, 390)

def calcul_row_0400(df):
    """Calcule les liquid assets pondérés de la ligne 0400 (Restricted-use central bank committed liquidity facilities)."""
    return calcul_liquid_assets(df, 400)

def calcul_row_0410(df):
    """Calcule les liquid assets pondérés de la ligne 0410 (Qualifying CIU shares/units: asset-backed securities - residential/auto, CQS1)."""
    return calcul_liquid_assets(df, 410)

def calcul_row_0420(df):
    """Calcule les liquid assets pondérés de la ligne 0420 (Qualifying CIU shares/units: High quality covered bonds, RW35%)."""
    return calcul_liquid_assets(df, 420)

def calcul_row_0430(df):
    """Calcule les liquid assets pondérés de la ligne 0430 (Qualifying CIU shares/units: asset-backed securities - commercial/individuals, CQS1)."""
    return calcul_liquid_assets(df, 430)

def calcul_row_0440(df):
    """Calcule les liquid assets pondérés de la ligne 0440 (Qualifying CIU shares/units: corporate debt/shares/non-interest bearing, CQS3-5)."""
    return calcul_liquid_assets(df, 440)

def calcul_row_0450(df):
    """Calcule les liquid assets pondérés de la ligne 0450 (Deposits by network member with central institution - no obligated investment)."""
    return calcul_liquid_assets(df, 450)

def calcul_row_0460(df):
    """Calcule les liquid assets pondérés de la ligne 0460 (Liquidity funding from central institution - non-specified collateral)."""
    return calcul_liquid_assets(df, 460)

def calcul_row_0470(df):
    """Calcule les liquid assets pondérés de la ligne 0470 (Central institutions: Level 2B assets considered liquid)."""
    return calcul_liquid_assets(df, 470)

#### 1.2.2
def calcul_row_0310(df):
    """Calcule la valeur de la ligne 0310 (somme des lignes 0320 à 0470)."""
    val_0320 = calcul_row_0320(df)
    val_0330 = calcul_row_0330(df)
    val_0340 = calcul_row_0340(df)
    val_0350 = calcul_row_0350(df)
    val_0360 = calcul_row_0360(df)
    val_0370 = calcul_row_0370(df)
    val_0380 = calcul_row_0380(df)
    val_0390 = calcul_row_0390(df)
    val_0400 = calcul_row_0400(df)
    val_0410 = calcul_row_0410(df)
    val_0420 = calcul_row_0420(df)
    val_0430 = calcul_row_0430(df)
    val_0440 = calcul_row_0440(df)
    val_0450 = calcul_row_0450(df)
    val_0460 = calcul_row_0460(df)
    val_0470 = calcul_row_0470(df)
    total = (val_0320 + val_0330 + val_0340 + val_0350 + val_0360 + val_0370 +
             val_0380 + val_0390 + val_0400 + val_0410 + val_0420 + val_0430 +
             val_0440 + val_0450 + val_0460 + val_0470)
    df.loc[df['row'] == 310, '0040'] = total
    return total

#### 1.2

def calcul_row_0220(df):
    """Calcule la valeur de la ligne 0220 (somme des lignes 0230 et 0310)."""
    val_0230 = calcul_row_0230(df)
    val_0310 = calcul_row_0310(df)
    total = val_0230 + val_0310
    df.loc[df['row'] == 220, '0040'] = total
    return total


#### 1 Total unajusted liquid assets

def calcul_row_0010(df):
    """Calcule la valeur de la ligne 0010 (somme des lignes 0020 et 0200)."""
    val_0020 = calcul_row_0020(df)
    val_0200 = calcul_row_0200(df)
    total = val_0020 + val_0200
    df.loc[df['row'] == 10, '0040'] = total
    return total

def calcul_HQLA(df):
    HQLA = calcul_row_0010(df)
    print("HQLA = ",HQLA)
    return HQLA
