############# Feuille 73 - Outflow #############
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
        # Rename the first column
        df.rename(columns={'Unnamed: 1': 'item'}, inplace=True)
        # Rename the second column
        df.rename(columns={'Unnamed: 2': 'row'}, inplace=True)
        return df

    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return pd.DataFrame()
    
def calcul_outflows(df, row_number):
    row = df[df['row'] == row_number]
    outflow = 0
    if not row.empty:
        montant = row['0010'].values[0] if '0010' in row else 0  # montant brut
        poids = row['0050'].values[0] if '0050' in row else 0    # poids réglementaire
        if pd.notna(montant) and pd.notna(poids):
            outflow = montant * poids
    df.loc[df['row'] == row_number, '0060'] = outflow
    return outflow

# Retail deposits section
def calcul_row_035(df):
    """Calcule les outflows de la ligne 035 (deposits exempted from the calculation of outflows)."""
    return calcul_outflows(df, 35)

def calcul_row_040(df):
    """Calcule les outflows de la ligne 040 (deposits where payout agreed within 30 days)."""
    return calcul_outflows(df, 40)

def calcul_row_060(df):
    """Calcule les outflows de la ligne 060 (category 1)."""
    return calcul_outflows(df, 60)

def calcul_row_070(df):
    """Calcule les outflows de la ligne 070 (category 2)."""
    return calcul_outflows(df, 70)


def calcul_row_050(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_060(df) + calcul_row_070(df)
    df.loc[df['row'] == 50, '060'] = total
    return total

def calcul_row_080(df):
    """Calcule les outflows de la ligne 080 (stable deposits)."""
    return calcul_outflows(df, 80)

def calcul_row_090(df):
    """Calcule les outflows de la ligne 090 (derogated stable deposits)."""
    return calcul_outflows(df, 90)

def calcul_row_100(df):
    """Calcule les outflows de la ligne 100 (deposits in third countries with higher outflow)."""
    return calcul_outflows(df, 100)

def calcul_row_110(df):
    """Calcule les outflows de la ligne 110 (other retail deposits)."""
    return calcul_outflows(df, 110)

def calcul_row_030(df):
    """Calcule la valeur de la ligne 030 (somme des lignes 035 à 110)."""
    total = (calcul_row_035(df) + calcul_row_040(df) + calcul_row_050(df) + calcul_row_080(df) +
            calcul_row_090(df) + calcul_row_100(df) + calcul_row_110(df))
    df.loc[df['row'] == 30, '0060'] = total
    return total

# Operational deposits section
def calcul_row_140(df):
    """Calcule les outflows de la ligne 140 (covered by DGS)."""
    return calcul_outflows(df, 140)

def calcul_row_150(df):
    """Calcule les outflows de la ligne 150 (not covered by DGS)."""
    return calcul_outflows(df, 150)

def calcul_row_130(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_140(df) + calcul_row_150(df)
    df.loc[df['row'] == 130, '0060'] = total
    return total

def calcul_row_170(df):
    """Calcule les outflows de la ligne 170 (not treated as liquid assets)."""
    return calcul_outflows(df, 170)

def calcul_row_180(df):
    """Calcule les outflows de la ligne 180 (treated as liquid assets)."""
    return calcul_outflows(df, 180)

def calcul_row_160(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_170(df) + calcul_row_180(df)
    df.loc[df['row'] == 1600, '0060'] = total
    return total

def calcul_row_190(df):
    """Calcule les outflows de la ligne 190 (operational relationship with non-financial customers)."""
    return calcul_outflows(df, 190)

def calcul_row_200(df):
    """Calcule les outflows de la ligne 200 (cash clearing and central credit institution services)."""
    return calcul_outflows(df, 200)

def calcul_row_120(df):
    """Calcule la valeur de la ligne 120 (somme des lignes 130 à 200)."""
    total = (calcul_row_130(df) + calcul_row_160(df) +
              calcul_row_190(df) + calcul_row_200(df))
    df.loc[df['row'] == 120, '0060'] = total
    return total

# Excess operational deposits section
def calcul_row_204(df):
    """Calcule les outflows de la ligne 204 (deposits by financial customers)."""
    return calcul_outflows(df, 204)

def calcul_row_206(df):
    """Calcule les outflows de la ligne 206 (covered by DGS)."""
    return calcul_outflows(df, 206)

def calcul_row_207(df):
    """Calcule les outflows de la ligne 207 (not covered by DGS)."""
    return calcul_outflows(df, 207)

def calcul_row_205(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_206(df) + calcul_row_207(df)
    df.loc[df['row'] == 205, '0060'] = total
    return total

def calcul_row_203(df):
    """Calcule la valeur de la ligne 203 (somme des lignes 204 à 207)."""
    total = calcul_row_204(df) + calcul_row_205(df)
    df.loc[df['row'] == 203, '0060'] = total
    return total

# Non-operational deposits section
def calcul_row_220(df):
    """Calcule les outflows de la ligne 220 (correspondent banking)."""
    return calcul_outflows(df, 220)

def calcul_row_230(df):
    """Calcule les outflows de la ligne 230 (deposits by financial customers)."""
    return calcul_outflows(df, 230)

def calcul_row_250(df):
    """Calcule les outflows de la ligne 250 (covered by DGS)."""
    return calcul_outflows(df, 250)

def calcul_row_260(df):
    """Calcule les outflows de la ligne 260 (not covered by DGS)."""
    return calcul_outflows(df, 260)

def calcul_row_240(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_250(df) + calcul_row_260(df)
    df.loc[df['row'] == 240, '0060'] = total
    return total

def calcul_row_210(df):
    """Calcule la valeur de la ligne 210 (somme des lignes 220 à 260)."""
    total = (calcul_row_220(df) + calcul_row_230(df) + calcul_row_240(df))
    df.loc[df['row'] == 210, '0060'] = total
    return total

# Additional outflows section
def calcul_row_280(df):
    """Calcule les outflows de la ligne 280 (non-Level 1 collateral for derivatives)."""
    return calcul_outflows(df, 280)

def calcul_row_290(df):
    """Calcule les outflows de la ligne 290 (Level 1 EHQ Covered Bonds collateral)."""
    return calcul_outflows(df, 290)

def calcul_row_300(df):
    """Calcule les outflows de la ligne 300 (deterioration of own credit quality)."""
    return calcul_outflows(df, 300)

def calcul_row_310(df):
    """Calcule les outflows de la ligne 310 (adverse market scenario on derivatives)."""
    return calcul_outflows(df, 310)

def calcul_row_340(df):
    """Calcule les outflows de la ligne 340 (outflows from derivatives)."""
    return calcul_outflows(df, 340)

def calcul_row_360(df):
    """Calcule les outflows de la ligne 360 (covered by collateralized SFT)."""
    return calcul_outflows(df, 360)

def calcul_row_370(df):
    """Calcule les outflows de la ligne 370 (other short positions)."""
    return calcul_outflows(df, 370)

def calcul_row_350(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_360(df) + calcul_row_370(df)
    df.loc[df['row'] == 350, '0060'] = total
    return total

def calcul_row_380(df):
    """Calcule les outflows de la ligne 380 (callable excess collateral)."""
    return calcul_outflows(df, 380)

def calcul_row_390(df):
    """Calcule les outflows de la ligne 390 (due collateral)."""
    return calcul_outflows(df, 390)

def calcul_row_400(df):
    """Calcule les outflows de la ligne 400 (liquid asset collateral exchangeable)."""
    return calcul_outflows(df, 400)

def calcul_row_420(df):
    """Calcule les outflows de la ligne 420 (structured financing instruments)."""
    return calcul_outflows(df, 420)

def calcul_row_430(df):
    """Calcule les outflows de la ligne 430 (financing facilities)."""
    return calcul_outflows(df, 430)

def calcul_row_410(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_420(df) + calcul_row_430(df)
    df.loc[df['row'] == 410, '0060'] = total
    return total

def calcul_row_450(df):
    """Calcule les outflows de la ligne 450 (internal netting of client positions)."""
    return calcul_outflows(df, 450)

def calcul_row_270(df):
    """Calcule la valeur de la ligne 270 (somme des lignes 280 à 450)."""
    total = (calcul_row_280(df) + calcul_row_290(df) + calcul_row_300(df) +
             calcul_row_310(df) + calcul_row_340(df) + calcul_row_350(df) +
             calcul_row_380(df) + calcul_row_390(df) + calcul_row_400(df) +
             calcul_row_410(df) + calcul_row_450(df))
    df.loc[df['row'] == 270, '0060'] = total
    return total

# Committed facilities section
def calcul_row_480(df):
    """Calcule les outflows de la ligne 480 (credit facilities to retail customers)."""
    return calcul_outflows(df, 480)

def calcul_row_490(df):
    """Calcule les outflows de la ligne 490 (to non-financial customers other than retail)."""
    return calcul_outflows(df, 490)


def calcul_row_510(df):
    """Calcule les outflows de la ligne 510 (for funding promotional loans of retail)."""
    return calcul_outflows(df, 510)

def calcul_row_520(df):
    """Calcule les outflows de la ligne 520 (for funding promotional loans of non-financial)."""
    return calcul_outflows(df, 520)

def calcul_row_530(df):
    """Calcule les outflows de la ligne 530 (other credit facilities to credit institutions)."""
    return calcul_outflows(df, 530)

def calcul_row_500(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_510(df) + calcul_row_520(df) + calcul_row_530(df)
    df.loc[df['row'] == 500, '0060'] = total
    return total

def calcul_row_540(df):
    """Calcule les outflows de la ligne 540 (to regulated financial institutions)."""
    return calcul_outflows(df, 540)

def calcul_row_550(df):
    """Calcule les outflows de la ligne 550 (within a group or IPS)."""
    return calcul_outflows(df, 550)

def calcul_row_560(df):
    """Calcule les outflows de la ligne 560 (within IPS treated as liquid asset)."""
    return calcul_outflows(df, 560)

def calcul_row_570(df):
    """Calcule les outflows de la ligne 570 (to other financial customers)."""
    return calcul_outflows(df, 570)

def calcul_row_470(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_480(df) + calcul_row_490(df) + calcul_row_500(df) +\
        calcul_row_540(df) + calcul_row_550(df) + calcul_row_560(df) + calcul_row_570(df)
    df.loc[df['row'] == 470, '0060'] = total
    return total

def calcul_row_590(df):
    """Calcule les outflows de la ligne 590 (to retail customers)."""
    return calcul_outflows(df, 590)

def calcul_row_600(df):
    """Calcule les outflows de la ligne 600 (to non-financial customers other than retail)."""
    return calcul_outflows(df, 600)

def calcul_row_610(df):
    """Calcule les outflows de la ligne 610 (to personal investment companies)."""
    return calcul_outflows(df, 610)


def calcul_row_630(df):
    """Calcule les outflows de la ligne 630 (to purchase assets other than securities)."""
    return calcul_outflows(df, 630)

def calcul_row_640(df):
    """Calcule les outflows de la ligne 640 (other SSPE liquidity facilities)."""
    return calcul_outflows(df, 640)

def calcul_row_620(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_630(df) + calcul_row_640(df)
    df.loc[df['row'] == 620, '0060'] = total
    return total

def calcul_row_660(df):
    """Calcule les outflows de la ligne 660 (for funding promotional loans of retail)."""
    return calcul_outflows(df, 660)

def calcul_row_670(df):
    """Calcule les outflows de la ligne 670 (for funding promotional loans of non-financial)."""
    return calcul_outflows(df, 670)

def calcul_row_680(df):
    """Calcule les outflows de la ligne 680 (other liquidity facilities to credit institutions)."""
    return calcul_outflows(df, 680)

def calcul_row_650(df):
    """Calcule les outflows de la ligne 050 (deposits subject to higher outflows)."""
    total =calcul_row_660(df) + calcul_row_670(df)+ calcul_row_680(df)
    df.loc[df['row'] == 650, '0060'] = total
    return total

def calcul_row_690(df):
    """Calcule les outflows de la ligne 690 (within a group or IPS)."""
    return calcul_outflows(df, 690)

def calcul_row_700(df):
    """Calcule les outflows de la ligne 700 (within IPS treated as liquid asset)."""
    return calcul_outflows(df, 700)

def calcul_row_710(df):
    """Calcule les outflows de la ligne 710 (to other financial customers)."""
    return calcul_outflows(df, 710)

def calcul_row_580(df):
    """Calcule les outflows de la ligne 580 (liquidity facilities)."""
    total =calcul_row_590(df) + calcul_row_600(df)+ calcul_row_610(df) +\
        calcul_row_620(df) +calcul_row_650(df) + calcul_row_690(df) +\
        calcul_row_700(df) +calcul_row_710(df)
    df.loc[df['row'] == 580, '0060'] = total
    return total

def calcul_row_460(df):
    """Calcule la valeur de la ligne 460 (somme des lignes 470 à 710)."""
    total = (calcul_row_470(df) + calcul_row_580(df))
    df.loc[df['row'] == 460, '0060'] = total
    return total

# Other products and services section (outflows)
def calcul_row_730(df):
    """Calcule les outflows de la ligne 730 (Uncommitted funding facilities)."""
    return calcul_outflows(df, 730)

def calcul_row_740(df):
    """Calcule les outflows de la ligne 740 (undrawn loans to wholesale counterparties)."""
    return calcul_outflows(df, 740)

def calcul_row_750(df):
    """Calcule les outflows de la ligne 750 (mortgages agreed but not drawn)."""
    return calcul_outflows(df, 750)

def calcul_row_760(df):
    """Calcule les outflows de la ligne 760 (credit cards)."""
    return calcul_outflows(df, 760)

def calcul_row_770(df):
    """Calcule les outflows de la ligne 770 (overdrafts)."""
    return calcul_outflows(df, 770)

def calcul_row_780(df):
    """Calcule les outflows de la ligne 780 (planned outflows for loan renewals)."""
    return calcul_outflows(df, 780)

def calcul_row_850(df):
    """Calcule les outflows de la ligne 850 (planned derivatives payables)."""
    return calcul_outflows(df, 850)

def calcul_row_860(df):
    """Calcule les outflows de la ligne 860 (trade finance off-balance sheet)."""
    return calcul_outflows(df, 860)

def calcul_row_870(df):
    """Calcule les outflows de la ligne 870 (others)."""
    return calcul_outflows(df, 870)

def calcul_row_720(df):
    """Calcule la valeur de la ligne 720 (somme des lignes 730 à 870)."""
    total = (calcul_row_730(df) + calcul_row_740(df) + calcul_row_750(df) +
             calcul_row_760(df) + calcul_row_770(df) + calcul_row_780(df) +
             calcul_row_850(df) + calcul_row_860(df) + calcul_row_870(df))
    df.loc[df['row'] == 720, '0060'] = total
    return total

# Other liabilities section
def calcul_row_890(df):
    """Calcule les outflows de la ligne 890 (operating expenses)."""
    return calcul_outflows(df, 890)

def calcul_row_900(df):
    """Calcule les outflows de la ligne 900 (debt securities not treated as retail)."""
    return calcul_outflows(df, 900)


def calcul_row_913(df):
    """Calcule les outflows de la ligne 913 (excess of funding to retail)."""
    return calcul_outflows(df, 913)

def calcul_row_914(df):
    """Calcule les outflows de la ligne 914 (excess of funding to non-financial corporates)."""
    return calcul_outflows(df, 914)

def calcul_row_915(df):
    """Calcule les outflows de la ligne 915 (excess of funding to sovereigns, MLDBs, PSEs)."""
    return calcul_outflows(df, 915)

def calcul_row_916(df):
    """Calcule les outflows de la ligne 916 (excess of funding to other legal entities)."""
    return calcul_outflows(df, 916)

def calcul_row_912(df):
    """Calcule les outflows de la ligne 912 (excess of funding to non-financial)."""
    total = calcul_row_913(df) + calcul_row_914(df) + calcul_row_915(df) + calcul_row_916(df)
    df.loc[df['row'] == 912, '0060'] = total
    return total

def calcul_row_917(df):
    """Calcule les outflows de la ligne 917 (assets borrowed unsecured)."""
    return calcul_outflows(df, 917)

def calcul_row_918(df):
    """Calcule les outflows de la ligne 918 (others)."""
    return calcul_outflows(df, 918)

def calcul_row_885(df):
    """Calcule la valeur de la ligne 885 (somme des lignes 890 à 918)."""
    total = (calcul_row_890(df) + calcul_row_900(df) + calcul_row_912(df) +
             calcul_row_917(df) + calcul_row_918(df))
    df.loc[df['row'] == 885, '0060'] = total
    return total

# Outflows from secured lending section
def calcul_row_940(df):
    """Calcule les outflows de la ligne 940 (level 1 excl. EHQ Covered Bonds collateral)."""
    return calcul_outflows(df, 940)

def calcul_row_950(df):
    """Calcule les outflows de la ligne 950 (level 1 EHQ Covered Bonds collateral)."""
    return calcul_outflows(df, 950)

def calcul_row_960(df):
    """Calcule les outflows de la ligne 960 (level 2A collateral)."""
    return calcul_outflows(df, 960)

def calcul_row_970(df):
    """Calcule les outflows de la ligne 970 (level 2B residential/auto ABS)."""
    return calcul_outflows(df, 970)

def calcul_row_980(df):
    """Calcule les outflows de la ligne 980 (level 2B covered bonds)."""
    return calcul_outflows(df, 980)

def calcul_row_990(df):
    """Calcule les outflows de la ligne 990 (level 2B commercial/individuals ABS)."""
    return calcul_outflows(df, 990)

def calcul_row_1000(df):
    """Calcule les outflows de la ligne 1000 (other Level 2B assets)."""
    return calcul_outflows(df, 1000)

def calcul_row_1010(df):
    """Calcule les outflows de la ligne 1010 (non-liquid assets)."""
    return calcul_outflows(df, 1010)

def calcul_row_930(df):
    """Calcule la valeur de la ligne 930 (somme des lignes 940 à 1010)."""
    total = (calcul_row_940(df) + calcul_row_950(df) + calcul_row_960(df) +
             calcul_row_970(df) + calcul_row_980(df) + calcul_row_990(df) +
             calcul_row_1000(df) + calcul_row_1010(df))
    df.loc[df['row'] == 930, '0060'] = total
    return total

# Non-central bank counterparty section
def calcul_row_1030(df):
    """Calcule les outflows de la ligne 1030 (level 1 excl. EHQ Covered Bonds collateral)."""
    return calcul_outflows(df, 1030)

def calcul_row_1040(df):
    """Calcule les outflows de la ligne 1040 (level 1 EHQ Covered Bonds collateral)."""
    return calcul_outflows(df, 1040)

def calcul_row_1050(df):
    """Calcule les outflows de la ligne 1050 (level 2A collateral)."""
    return calcul_outflows(df, 1050)

def calcul_row_1060(df):
    """Calcule les outflows de la ligne 1060 (level 2B residential/auto ABS)."""
    return calcul_outflows(df, 1060)

def calcul_row_1070(df):
    """Calcule les outflows de la ligne 1070 (level 2B covered bonds)."""
    return calcul_outflows(df, 1070)

def calcul_row_1080(df):
    """Calcule les outflows de la ligne 1080 (level 2B commercial/individuals ABS)."""
    return calcul_outflows(df, 1080)

def calcul_row_1090(df):
    """Calcule les outflows de la ligne 1090 (other Level 2B assets)."""
    return calcul_outflows(df, 1090)

def calcul_row_1100(df):
    """Calcule les outflows de la ligne 1100 (non-liquid assets)."""
    return calcul_outflows(df, 1100)

def calcul_row_1020(df):
    """Calcule la valeur de la ligne 1020 (somme des lignes 1030 à 1100)."""
    total = (calcul_row_1030(df) + calcul_row_1040(df) + calcul_row_1050(df) +
             calcul_row_1060(df) + calcul_row_1070(df) + calcul_row_1080(df) +
             calcul_row_1090(df) + calcul_row_1100(df))
    df.loc[df['row'] == 1020, '0060'] = total
    return total

def calcul_row_920(df):
    """Calcule la valeur de la ligne 920 (somme des lignes 930 et 1020)."""
    total = calcul_row_930(df) + calcul_row_1020(df)
    df.loc[df['row'] == 920, '0060'] = total
    return total

# Total outflows from unsecured transactions
def calcul_row_020(df):
    """Calcule la valeur de la ligne 020 (somme des lignes 030 à 885)."""
    total = (calcul_row_030(df) + calcul_row_120(df) + calcul_row_203(df) +\
             calcul_row_210(df) + calcul_row_270(df) + calcul_row_460(df) +\
                calcul_row_720(df) + calcul_row_885(df))
    df.loc[df['row'] == 20, '0060'] = total
    return total
#Total outflow from collateral swaps

def calcul_row_1130(df):
    """Calcule la valeur de la ligne 1130 (same as line 010)."""
    total = calcul_outflows(df, 1130)
    df.loc[df['row'] == 1130, '0060'] = total
    return total
# Total outflows
def calcul_row_010(df):
    """Calcule la valeur de la ligne 010 (somme des lignes 020 et 920)."""
    total = calcul_row_020(df) + calcul_row_920(df) + calcul_row_1130(df)
    df.loc[df['row'] == 10, '0060'] = total
    return total

def calcul_outflow(df):
    OUTFLOWS = calcul_row_010(df)
    #print("OUTFLOW = ", OUTFLOWS)
    return OUTFLOWS
