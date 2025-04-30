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
def calcul_asf_pondere(df, row_number):
    """Calcule l'ASF pondéré pour une ligne donnée."""
    row = df[df['row'] == row_number]
    asf = 0
    for amt_col, wgt_col in zip(['0010', '0020', '0030'], ['0070','0080', '0090']):
        amt = row[amt_col].values[0] if amt_col in row else 0
        wgt = row[wgt_col].values[0] if wgt_col in row else 0
        if pd.notna(amt) and pd.notna(wgt):
            asf += amt * wgt
    df.loc[df['row'] == row_number, '0100'] = asf
    return asf
def calcul_row_0030(df):
    """Calcule l'ASF de la ligne 0030 (Common Equity Tier 1) avec pondération (100%)."""
    asf = calcul_asf_pondere(df, 30)
    return asf

def calcul_row_0040(df):
    """Calcule l'ASF de la ligne 0040 (Additional Tier 1) avec pondération (0%, 0%, 100%)."""
    asf = calcul_asf_pondere(df, 40)
    return asf

def calcul_row_0050(df):
    """Calcule l'ASF de la ligne 0050 (Tier 2) avec pondération (0%, 0%, 100%)."""
    asf = calcul_asf_pondere(df, 50)
    return asf

def calcul_row_0060(df):
    """Calcule l'ASF de la ligne 0060 (Other capital instruments) avec pondération (0%, 0%, 100%)."""
    asf = calcul_asf_pondere(df, 60)
    return asf

def calcul_row_0020(df):
    """Calcule l'ASF de la ligne 0020 (ASF from capital items and instruments)."""
    asf_30 = calcul_row_0030(df)
    asf_40 = calcul_row_0040(df)
    asf_50 = calcul_row_0050(df)
    asf_60 = calcul_row_0060(df)
    asf_20 = asf_30 + asf_40 + asf_50 + asf_60
    df.loc[df['row'] == 20, '0100'] = asf_20
    return asf_20

def calcul_row_0080(df):
    """Calcule l'ASF de la ligne 0080 (ASF from retail bonds)."""
    asf = calcul_asf_pondere(df, 80)
    return asf

def calcul_row_0090(df):
    """Calcule l'ASF de la ligne 0090 (Stable retail deposits)"""
    asf = calcul_asf_pondere(df, 90)
    return asf

def calcul_row_0100(df):
    """Calcule l'ASF de la ligne 0100 (Other retail deposits) ."""
    asf = calcul_asf_pondere(df, 100)
    return asf

def calcul_row_0110(df):
    """Calcule l'ASF de la ligne 0110 (Other retail deposits) ."""
    asf = calcul_asf_pondere(df, 110)
    return asf

def calcul_row_0120(df):
    """Calcule l'ASF de la ligne 0120 (ASF from other non-financial customers)."""
    asf = calcul_asf_pondere(df, 120)
    return asf


def calcul_row_0070(df):
    """Calcule l'ASF from retail deposits."""
    asf_90 = calcul_row_0090(df)
    asf_110 = calcul_row_0110(df)
    asf_70 = asf_90 + asf_110
    df.loc[df['row'] == 70, '0100'] = asf_70
    return asf_70

def calcul_row_0140(df):
    """Calcule l'ASF de la ligne 0140 (Liabilities provided by the central government)."""
    asf = calcul_asf_pondere(df, 140)
    return asf

def calcul_row_0150(df):
    """Calcule l'ASF de la ligne 0150 (Liabilities provided by regional governments)."""
    asf = calcul_asf_pondere(df, 150)
    return asf

def calcul_row_0160(df):
    """Calcule l'ASF de la ligne 0160 (Liabilities provided by public sector entities)."""
    asf = calcul_asf_pondere(df, 160)
    return asf

def calcul_row_0170(df):
    """Calcule l'ASF de la ligne 0170 (Liabilities provided by multilateral development banks)."""
    asf = calcul_asf_pondere(df, 170)
    return asf

def calcul_row_0180(df):
    """Calcule l'ASF de la ligne 0180 (Liabilities provided by non-financial corporate customers)."""
    asf = calcul_asf_pondere(df, 180)
    return asf

def calcul_row_0190(df):
    """Calcule l'ASF de la ligne 0190 (Liabilities provided by credit unions)."""
    asf = calcul_asf_pondere(df, 190)
    return asf

def calcul_row_0200(df):
    """Calcule l'ASF de la ligne 0200 (Liabilities provided by credit unions, personal investment companies and deposit brokers)."""
    asf = calcul_asf_pondere(df, 200)
    return asf

def calcul_row_0210(df):
    """Calcule l'ASF de la ligne 0210 (ASF from liabilities and committed facilities within a group or an IPS)."""
    asf = calcul_asf_pondere(df, 210)
    return asf

def calcul_row_0130(df):
    """Calcule l'ASF de la ligne 0130 (Securities financing transactions)."""
    asf_160 = calcul_row_0160(df)
    asf_170 = calcul_row_0170(df)
    asf_180 = calcul_row_0180(df)
    asf_190 = calcul_row_0190(df)
    asf_200 = calcul_row_0200(df)
    asf_210 = calcul_row_0210(df)
    asf_0130 = asf_160 + asf_170 + asf_180 + asf_190 + asf_200 + asf_210
    df.loc[df['row'] == 130, '0100'] = asf_0130
    return asf_0130

def calcul_row_0220(df):
    """Calcule l'ASF de la ligne 0220 (ASF from financial customers and central banks)."""
    asf = calcul_asf_pondere(df, 220)
    return asf

def calcul_row_0240(df):
    """Calcule l'ASF de la ligne 0240 (Liabilities provided by the central bank of a third country)."""
    asf = calcul_asf_pondere(df, 240)
    return asf

def calcul_row_0250(df):
    """Calcule l'ASF de la ligne 0250 (Liabilities provided by financial customers)."""
    asf = calcul_asf_pondere(df, 250)
    return asf

def calcul_row_0260(df):
    """Calcule l'ASF de la ligne 0260 (Operational deposits) avec pondération (50%, 50%, 100%)."""
    asf = calcul_asf_pondere(df, 260)
    return asf

def calcul_row_0280(df):
    """Calcule l'ASF de la ligne 0280 (Other liabilities) avec pondération (0%, 50%, 100%)."""
    asf = calcul_asf_pondere(df, 280)
    return asf

def calcul_row_0290(df):
    """Calcule l'ASF de la ligne 0290 (Others) avec pondération (0%, 0%, 0%)."""
    asf = calcul_asf_pondere(df, 290)
    return asf

def calcul_row_0300(df):
    """Calcule l'ASF de la ligne 0300 (ASF from liabilities provided where the counterparty cannot be determined)."""
    asf = calcul_asf_pondere(df, 300)
    return asf

def calcul_row_0270(df):
    """Calcule l'ASF de la ligne 0270 (Excess operational deposits)."""
    asf_280 = calcul_row_0280(df)
    asf_290 = calcul_row_0290(df)
    asf_300 = calcul_row_0300(df)
    asf_270 = asf_280 + asf_290 + asf_300
    df.loc[df['row'] == 270, '0100'] = asf_270
    return asf_270

def calcul_row_0230(df):
    """Calcule l'ASF de la ligne 0230 (ASF from financial customers and central banks)"""
    asf_250 = calcul_row_0250(df)
    asf_260 = calcul_row_0260(df)
    asf_270 = calcul_row_0270(df)
    asf_230 = asf_250 + asf_260 + asf_270
    df.loc[df['row'] == 230, '0100'] = asf_230
    return asf_230

def calcul_row_0310(df):
    """Calcule l'ASF de la ligne 0310 (ASF from liabilities provided where countreparty ..)."""
    asf = calcul_asf_pondere(df, 310)
    return asf

def calcul_row_0320(df):
    """Calcule l'ASF de la ligne 0320 (ASF from net derivatives liabilities)."""
    asf = calcul_asf_pondere(df, 320)
    return asf

def calcul_row_0340(df):
    """Calcule l'ASF de la ligne 0340  """
    asf = calcul_asf_pondere(df, 340)
    return asf

def calcul_row_0350(df):
    """Calcule l'ASF de la ligne 0350 """
    asf = calcul_asf_pondere(df, 350)
    return asf

def calcul_row_0360(df):
    """Calcule l'ASF de la ligne 0360 """
    asf = calcul_asf_pondere(df, 360)
    return asf

def calcul_row_0370(df):
    """Calcule l'ASF de la ligne 0370 """
    asf = calcul_asf_pondere(df, 370)
    return asf

def calcul_row_0380(df):
    """Calcule l'ASF de la ligne 0380 """
    asf = calcul_asf_pondere(df, 380)
    return asf


def calcul_row_0330(df):
    """Calcule l'ASF de la ligne 0330 (ASF from interdependent derivatives liabilities)."""
    asf_340 = calcul_row_0340(df)
    asf_350 = calcul_row_0350(df)
    asf_360 = calcul_row_0360(df)
    asf_370 = calcul_row_0370(df)
    asf_380 = calcul_row_0380(df)
    asf_330 =asf_340 + asf_350 + asf_360 + asf_370 + asf_380
    df.loc[df['row'] == 330, '0100'] = asf_330
    return asf_330

def calcul_row_0400(df):
    """Calcule l'ASF de la ligne 0400 (Trade date payables) avec pondération (0%, 0%, 0%)."""
    asf = calcul_asf_pondere(df, 400)
    return asf

def calcul_row_0410(df):
    """Calcule l'ASF de la ligne 0410 (Deferred tax liabilities) avec pondération (0%, 50%, 100%)."""
    asf = calcul_asf_pondere(df, 410)
    return asf

def calcul_row_0420(df):
    """Calcule l'ASF de la ligne 0420 (Minority interests) avec pondération (0%, 50%, 100%)."""
    asf = calcul_asf_pondere(df, 420)
    return asf

def calcul_row_0430(df):
    """Calcule l'ASF de la ligne 0430 (Other liabilities) avec pondération (0%, 50%, 100%)."""
    asf = calcul_asf_pondere(df, 430)
    return asf

def calcul_row_0390(df):
    """Calcule l'ASF de la ligne 0390 (ASF from other liabilities)."""
    asf_400 = calcul_row_0400(df)
    asf_410 = calcul_row_0410(df)
    asf_420 = calcul_row_0420(df)
    asf_430 = calcul_row_0430(df)
    asf_390 = asf_400 + asf_410 + asf_420 + asf_430
    df.loc[df['row'] == 390, '0100'] = asf_390
    return asf_390

###################################       ASF       #######################
def calcul_row_0010(df):
    """Calcule l'ASF de la ligne 0010 (Available Stable Funding)."""
    asf_20 = calcul_row_0020(df)
    asf_70 = calcul_row_0070(df)
    asf_130 = calcul_row_0130(df)
    asf_220 = calcul_row_0220(df)
    asf_230 = calcul_row_0230(df)
    asf_310 = calcul_row_0310(df)
    asf_320 = calcul_row_0320(df)
    asf_330 = calcul_row_0330(df)
    asf_390 = calcul_row_0390(df)

    asf_10 = asf_20 + asf_70 + asf_130 +asf_220 + asf_230 +asf_310 + asf_320 + asf_330 + asf_390
    df.loc[df['row'] == 10, '0100'] = asf_10
    return asf_10

def calcul_ASF(df):
    ASF = calcul_row_0010(df_81)
    print(ASF)
    return