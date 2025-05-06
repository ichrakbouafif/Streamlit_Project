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
        # Rename the first column
        df.rename(columns={'Unnamed: 1': 'item'}, inplace=True)
        # Rename the second column
        df.rename(columns={'Unnamed: 2': 'row'}, inplace=True)

        return df

    except Exception as e:
        print(f"Erreur lors du chargement/nettoyage de la feuille 80 : {e}")
        return None
import pandas as pd

""" def calcul_rsf_pondere(df, row_number):
    
    row = df[df['row'] == row_number]
    rsf = 0
    for amt_col, wgt_col in zip(['0010', '0020', '0030', '0040'], ['0090', '0100', '0110', '0120']):
        amt = row[amt_col].values[0] if amt_col in row else 0
        wgt = row[wgt_col].values[0] if wgt_col in row else 0
        if pd.notna(amt) and pd.notna(wgt):
            rsf += amt * wgt
    df.loc[df['row'] == row_number, '0130'] = rsf
    return rsf """

def calcul_rsf_pondere(df, row_number):
    """Calcule le RSF pondéré pour une ligne donnée."""
    try:
        # Look for the row - use string comparison if needed
        row = df[df['row'].astype(str).str.strip() == str(row_number)]
        
        if row.empty:
            print(f"Warning: Row {row_number} not found in DataFrame")
            return 0
        
        rsf = 0
        for amt_col, wgt_col in zip(['0010', '0020', '0030', '0040'], 
                                  ['0090', '0100', '0110', '0120']):
            # Safely get values with default 0 if column doesn't exist
            amt = row[amt_col].iloc[0] if amt_col in row.columns else 0
            wgt = row[wgt_col].iloc[0] if wgt_col in row.columns else 0
            
            if pd.notna(amt) and pd.notna(wgt):
                rsf += amt * wgt
        
        # Update the value in DataFrame if row exists
        if not row.empty:
            df.loc[df['row'].astype(str).str.strip() == str(row_number), '0130'] = rsf
            
        return rsf
        
    except Exception as e:
        print(f"Error calculating RSF for row {row_number}: {str(e)}")
        return 0
    
#RSF from Central Bank assets
import pandas as pd

def calcul_row_40(df):
    """Calcule le RSF de la ligne 40"""
    return calcul_rsf_pondere(df, 40)

def calcul_row_50(df):
    """Calcule le RSF de la ligne 50"""
    return calcul_rsf_pondere(df, 50)

def calcul_row_60(df):
    """Calcule le RSF de la ligne 60"""
    return calcul_rsf_pondere(df, 60)

def calcul_row_30(df):
    """Calcule la ligne 30 comme la somme des RSF des lignes 40, 50, 60."""
    rsf_40 = calcul_row_40(df)
    rsf_50 = calcul_row_50(df)
    rsf_60 = calcul_row_60(df)
    rsf_30 = rsf_40 + rsf_50 + rsf_60
    df.loc[df['row'] == 30, '0130'] = rsf_30
    return rsf_30

def calcul_row_70(df):
    """Calcule le RSF de la ligne 70 (autres expositions banques centrales)."""
    return calcul_rsf_pondere(df, 70)

def calcul_row_20(df):
    """Calcule la ligne 20 comme la somme des lignes 30 et 70."""
    rsf_30 = calcul_row_30(df)
    rsf_70 = calcul_row_70(df)
    rsf_20 = rsf_30 + rsf_70
    df.loc[df['row'] == 20, '0130'] = rsf_20
    return rsf_20
#RSF From Liquid Assets
import pandas as pd

def calcul_row_100(df):
    """Calcule le RSF de la ligne 100 (1.2.1.1)"""
    return calcul_rsf_pondere(df, 100)

def calcul_row_110(df):
    """Calcule le RSF de la ligne 110 (1.2.1.2)"""
    return calcul_rsf_pondere(df, 110)

def calcul_row_120(df):
    """Calcule le RSF de la ligne 120 (1.2.1.3)"""
    return calcul_rsf_pondere(df, 120)

def calcul_row_90(df):
    """Calcule la ligne 90 (1.2.1) comme la somme des lignes 100, 110, 120."""
    rsf_100 = calcul_row_100(df)
    rsf_110 = calcul_row_110(df)
    rsf_120 = calcul_row_120(df)
    rsf_090 = rsf_100 + rsf_110 + rsf_120
    df.loc[df['row'] == 90, '0130'] = rsf_090
    return rsf_090

def calcul_row_140(df):
    """Calcule le RSF de la ligne 140 (1.2.2.1)."""
    return calcul_rsf_pondere(df, 140)

def calcul_row_150(df):
    """Calcule le RSF de la ligne 150 (1.2.2.2)."""
    return calcul_rsf_pondere(df, 150)

def calcul_row_160(df):
    """Calcule le RSF de la ligne 160 (1.2.2.3)."""
    return calcul_rsf_pondere(df, 160)

def calcul_row_130(df):
    """Calcule la ligne 130 comme la somme des lignes 140, 150, 160 (1.2.2)."""
    rsf_140 = calcul_row_140(df)
    rsf_150 = calcul_row_150(df)
    rsf_160 = calcul_row_160(df)
    rsf_130 = rsf_140 + rsf_150 + rsf_160
    df.loc[df['row'] == 130, '0130'] = rsf_130
    return rsf_130

def calcul_row_180(df):
    """Calcule le RSF de la ligne 180 (1.2.3.1)."""
    return calcul_rsf_pondere(df, 180)

def calcul_row_190(df):
    """Calcule le RSF de la ligne 190 (1.2.3.2)."""
    return calcul_rsf_pondere(df, 190)

def calcul_row_200(df):
    """Calcule le RSF de la ligne 200 (1.2.3.3)."""
    return calcul_rsf_pondere(df, 200)

def calcul_row_170(df):
    """Calcule la ligne 170 comme la somme des lignes 180, 190, 200 (1.2.3)."""
    rsf_180 = calcul_row_180(df)
    rsf_190 = calcul_row_190(df)
    rsf_200 = calcul_row_200(df)
    rsf_170 = rsf_180 + rsf_190 + rsf_200
    df.loc[df['row'] == 170, '0130'] = rsf_170
    return rsf_170

def calcul_row_220(df):
    """Calcule le RSF de la ligne 220 (1.2.4.1)."""
    return calcul_rsf_pondere(df, 220)

def calcul_row_230(df):
    """Calcule le RSF de la ligne 230 (1.2.4.2)."""
    return calcul_rsf_pondere(df, 230)

def calcul_row_240(df):
    """Calcule le RSF de la ligne 240 (1.2.4.3)."""
    return calcul_rsf_pondere(df, 240)

def calcul_row_210(df):
    """Calcule la ligne 210 comme la somme des lignes 220, 230, 240 (1.2.4)."""
    rsf_220 = calcul_row_220(df)
    rsf_230 = calcul_row_230(df)
    rsf_240 = calcul_row_240(df)
    rsf_210 = rsf_220 + rsf_230 + rsf_240
    df.loc[df['row'] == 210, '0130'] = rsf_210
    return rsf_210
def calcul_row_260(df):
    """Calcule le RSF de la ligne 260 (1.2.5.1)."""
    return calcul_rsf_pondere(df, 260)

def calcul_row_270(df):
    """Calcule le RSF de la ligne 270 (1.2.5.2)."""
    return calcul_rsf_pondere(df, 270)

def calcul_row_280(df):
    """Calcule le RSF de la ligne 280 (1.2.5.3)."""
    return calcul_rsf_pondere(df, 280)

def calcul_row_250(df):
    """Calcule la ligne 250 comme la somme des lignes 260, 270, 280 (1.2.5)."""
    rsf_260 = calcul_row_260(df)
    rsf_270 = calcul_row_270(df)
    rsf_280 = calcul_row_280(df)
    rsf_250 = rsf_260 + rsf_270 + rsf_280
    df.loc[df['row'] == 250, '0130'] = rsf_250
    return rsf_250
def calcul_row_300(df):
    """Calcule le RSF de la ligne 300 (1.2.6.1)."""
    return calcul_rsf_pondere(df, 300)

def calcul_row_310(df):
    """Calcule le RSF de la ligne 310 (1.2.6.2)."""
    return calcul_rsf_pondere(df, 310)

def calcul_row_320(df):
    """Calcule le RSF de la ligne 320 (1.2.6.3)."""
    return calcul_rsf_pondere(df, 320)

def calcul_row_290(df):
    """Calcule la ligne 290 comme la somme des lignes 300, 310, 320 (1.2.6)."""
    rsf_300 = calcul_row_300(df)
    rsf_310 = calcul_row_310(df)
    rsf_320 = calcul_row_320(df)
    rsf_290 = rsf_300 + rsf_310 + rsf_320
    df.loc[df['row'] == 290, '0130'] = rsf_290
    return rsf_290
def calcul_row_340(df):
    """Calcule le RSF de la ligne 340 (1.2.7.1)."""
    return calcul_rsf_pondere(df, 340)

def calcul_row_350(df):
    """Calcule le RSF de la ligne 350 (1.2.7.2)."""
    return calcul_rsf_pondere(df, 350)

def calcul_row_360(df):
    """Calcule le RSF de la ligne 360 (1.2.7.3)."""
    return calcul_rsf_pondere(df, 360)

def calcul_row_330(df):
    """Calcule la ligne 330 comme la somme des lignes 340, 350, 360 (1.2.7)."""
    rsf_340 = calcul_row_340(df)
    rsf_350 = calcul_row_350(df)
    rsf_360 = calcul_row_360(df)
    rsf_330 = rsf_340 + rsf_350 + rsf_360
    df.loc[df['row'] == 330, '0130'] = rsf_330
    return rsf_330
def calcul_row_380(df):
    """Calcule le RSF de la ligne 380 (1.2.8.1)."""
    return calcul_rsf_pondere(df, 380)

def calcul_row_390(df):
    """Calcule le RSF de la ligne 390 (1.2.8.2)."""
    return calcul_rsf_pondere(df, 390)

def calcul_row_400(df):
    """Calcule le RSF de la ligne 400 (1.2.8.3)."""
    return calcul_rsf_pondere(df, 400)

def calcul_row_370(df):
    """Calcule la ligne 370 comme la somme des lignes 380, 390, 400 (1.2.8)."""
    rsf_380 = calcul_row_380(df)
    rsf_390 = calcul_row_390(df)
    rsf_400 = calcul_row_400(df)
    rsf_370 = rsf_380 + rsf_390 + rsf_400
    df.loc[df['row'] == 370, '0130'] = rsf_370
    return rsf_370
def calcul_row_420(df):
    """Calcule le RSF de la ligne 420 (1.2.9.1)."""
    return calcul_rsf_pondere(df, 420)

def calcul_row_430(df):
    """Calcule le RSF de la ligne 430 (1.2.9.2)."""
    return calcul_rsf_pondere(df, 430)

def calcul_row_440(df):
    """Calcule le RSF de la ligne 440 (1.2.9.3)."""
    return calcul_rsf_pondere(df, 440)

def calcul_row_410(df):
    """Calcule la ligne 410 comme la somme des lignes 420, 430, 440 (1.2.9)."""
    rsf_420 = calcul_row_420(df)
    rsf_430 = calcul_row_430(df)
    rsf_440 = calcul_row_440(df)
    rsf_410 = rsf_420 + rsf_430 + rsf_440
    df.loc[df['row'] == 410, '0130'] = rsf_410
    return rsf_410
def calcul_row_460(df):
    """Calcule le RSF de la ligne 460 (1.2.10.1)."""
    return calcul_rsf_pondere(df, 460)

def calcul_row_470(df):
    """Calcule le RSF de la ligne 470 (1.2.10.2)."""
    return calcul_rsf_pondere(df, 470)

def calcul_row_480(df):
    """Calcule le RSF de la ligne 480 (1.2.10.3)."""
    return calcul_rsf_pondere(df, 480)

def calcul_row_450(df):
    """Calcule la ligne 450 comme la somme des lignes 460, 470, 480 (1.2.10)."""
    rsf_460 = calcul_row_460(df)
    rsf_470 = calcul_row_470(df)
    rsf_480 = calcul_row_480(df)
    rsf_450 = rsf_460 + rsf_470 + rsf_480
    df.loc[df['row'] == 450, '0130'] = rsf_450
    return rsf_450
def calcul_row_500(df):
    """Calcule le RSF de la ligne 500 (1.2.11.1)."""
    return calcul_rsf_pondere(df, 500)

def calcul_row_510(df):
    """Calcule le RSF de la ligne 510 (1.2.11.2)."""
    return calcul_rsf_pondere(df, 510)

def calcul_row_490(df):
    """Calcule la ligne 490 comme la somme des lignes 500, 510 (1.2.11)."""
    rsf_500 = calcul_row_500(df)
    rsf_510 = calcul_row_510(df)
    rsf_490 = rsf_500 + rsf_510
    df.loc[df['row'] == 490, '0130'] = rsf_490
    return rsf_490
def calcul_row_530(df):
    """Calcule le RSF de la ligne 530 (1.2.12.1)."""
    return calcul_rsf_pondere(df, 530)

def calcul_row_540(df):
    """Calcule le RSF de la ligne 540 (1.2.12.2)."""
    return calcul_rsf_pondere(df, 540)

def calcul_row_520(df):
    """Calcule la ligne 520 comme la somme des lignes 530, 540 (1.2.12)."""
    rsf_530 = calcul_row_530(df)
    rsf_540 = calcul_row_540(df)
    rsf_520 = rsf_530 + rsf_540
    df.loc[df['row'] == 520, '0130'] = rsf_520
    return rsf_520
def calcul_row_550(df):
    """Calcule le RSF de la ligne 550 (1.2.13)."""
    return calcul_rsf_pondere(df, 550)
#########################################################
def calcul_row_80(df):
    """Calcule le RSF from liquid assets somme de 1.2.1 -> 1.2.13"""
    rsf_90 = calcul_row_90(df) #1.2.1
    rsf_130 = calcul_row_130(df) #1.2.2
    rsf_170 = calcul_row_170(df) #1.2.3
    rsf_210 = calcul_row_210(df) #1.2.4
    rsf_250 = calcul_row_250(df) #1.2.5
    rsf_290 = calcul_row_290(df) #1.2.6
    rsf_330 = calcul_row_330(df) #1.2.7
    rsf_370 = calcul_row_370(df) #1.2.8
    rsf_410 = calcul_row_410(df) #1.2.9
    rsf_450 = calcul_row_450(df) #1.2.10
    rsf_490 = calcul_row_490(df) #1.2.11
    rsf_520 = calcul_row_520(df) #1.2.12
    rsf_550 = calcul_row_550(df) #1.2.13

    rsf_80 = rsf_90 + rsf_130 + rsf_170 + rsf_210 + rsf_250 + rsf_290 + rsf_330 + rsf_370 + rsf_410 + rsf_450 + rsf_490 + rsf_520 + rsf_550
    df.loc[df['row'] == 80, '0130'] = rsf_80
    return rsf_80
#RSF from securities other than liquid assets
def calcul_row_580(df):
    """Calcule le RSF de la ligne 580 """
    rsf = calcul_rsf_pondere(df, 580)
    return rsf

def calcul_row_590(df):
    """Calcule le RSF de la ligne 590"""
    rsf = calcul_rsf_pondere(df, 590)
    return rsf

def calcul_row_570(df):
    """Calcule le RSF de la ligne 570 somme de 580 et 590"""
    rsf_580 = calcul_row_580(df)
    rsf_590 = calcul_row_590(df)
    rsf_570 = rsf_580 + rsf_590
    return rsf_570

def calcul_row_600(df):
    """Calcule le RSF de la ligne 600 avec pondération (100%)."""
    rsf = calcul_rsf_pondere(df, 600)
    return rsf

def calcul_row_610(df):
    """Calcule le RSF de la ligne 610 avec pondérations (85%)."""
    rsf = calcul_rsf_pondere(df, 610)
    return rsf

def calcul_row_560(df):
    """Calcule le RSF de la ligne 560 comme la somme des lignes 570, 600 et 610."""
    rsf_570 = calcul_row_570(df)
    rsf_600 = calcul_row_600(df)
    rsf_610 = calcul_row_610(df)
    rsf_560 = rsf_570 + rsf_600 + rsf_610
    df.loc[df['row'] == 560, '0130'] = rsf_560
    return rsf_560
#RSF FROM LOANS
def calcul_row_630(df):
    """Calcule le RSF de la ligne 630 (opérationnal deposits) """
    rsf = calcul_rsf_pondere(df, 630)
    return rsf

def calcul_row_660(df):
    """Calcule le RSF de la ligne 660 """
    rsf = calcul_rsf_pondere(df, 660)
    return rsf

def calcul_row_670(df):
    """Calcule le RSF de la ligne 670 """
    rsf = calcul_rsf_pondere(df, 670)
    return rsf

def calcul_row_680(df):
    """Calcule le RSF de la ligne 680 """
    rsf = calcul_rsf_pondere(df, 680)
    return rsf

def calcul_row_650(df):
    """Calcule le RSF de la ligne 640 (securities financing transactions with financial customers)."""
    rsf_660 = calcul_row_660(df)
    rsf_670 = calcul_row_670(df)
    rsf_680 = calcul_row_680(df)
    rsf_650 = rsf_660 + rsf_670 + rsf_680
    df.loc[df['row'] == 650, '0130'] = rsf_650
    return rsf_650

def calcul_row_700(df):
    """Calcule le RSF de la ligne 700 avec pondérations (5%, 50%, et 100%)."""
    rsf = calcul_rsf_pondere(df, 700)
    return rsf

def calcul_row_710(df):
    """Calcule le RSF de la ligne 710 avec pondérations (50%, 50%, et 100%)."""
    rsf = calcul_rsf_pondere(df, 710)
    return rsf

def calcul_row_720(df):
    """Calcule le RSF de la ligne 720 avec pondérations (100%, 100%, et 100%)."""
    rsf = calcul_rsf_pondere(df, 720)
    return rsf

def calcul_row_690(df):
    """Calcule le RSF de la ligne 690 (collateralized by other assets)."""
    rsf_700 = calcul_row_700(df)
    rsf_710 = calcul_row_710(df)
    rsf_720 = calcul_row_720(df)
    rsf_690 = rsf_700 + rsf_710 + rsf_720
    df.loc[df['row'] == 690, '0130'] = rsf_690
    return rsf_690

def calcul_row_640(df):
    """Calcule le RSF de la ligne 640"""
    rsf_650 = calcul_row_650(df)
    rsf_690 = calcul_row_690(df)
    rsf_640 = rsf_650 + rsf_690
    df.loc[df['row'] == 640, '0130'] = rsf_640
    return rsf_640

def calcul_row_730(df):
    """Calcule le RSF de la ligne 730 avec pondements (10%, 50%, et 100%)."""
    rsf = calcul_rsf_pondere(df, 730)
    return rsf

def calcul_row_740(df):
    """Calcule le RSF de la ligne 740 avec pondements (85%)."""
    rsf = calcul_rsf_pondere(df, 740)
    return rsf

def calcul_row_760(df):
    """Calcule le RSF de la ligne 760 (residential mortgages)."""
    rsf = calcul_rsf_pondere(df, 760)
    return rsf

def calcul_row_770(df):
    """Calcule le RSF de la ligne 770 """
    rsf = calcul_rsf_pondere(df, 770)
    return rsf

def calcul_row_780(df):
    """Calcule le RSF de la ligne 780 ."""
    rsf = calcul_rsf_pondere(df, 780)
    return rsf

def calcul_row_790(df):
    """Calcule le RSF de la ligne 790"""
    rsf = calcul_rsf_pondere(df, 790)
    return rsf

def calcul_row_750(df):
    """Calcule le RSF de la ligne 750 (loans to non-financial customers with risk weight of 35% or less)."""
    rsf_760 = calcul_row_760(df)
    rsf_770 = calcul_row_770(df)
    rsf_780 = calcul_row_780(df)
    rsf_790 = calcul_row_790(df)
    rsf_750 = rsf_760 + rsf_770 + rsf_780 + rsf_790
    df.loc[df['row'] == 750, '0130'] = rsf_750
    return rsf_750

def calcul_row_810(df):
    """Calcule le RSF de la ligne 810 (residential mortgages)."""
    rsf = calcul_rsf_pondere(df, 810)
    return rsf

def calcul_row_820(df):
    """Calcule le RSF de la ligne 820 avec pondérations (50%, 50%, et 85%)."""
    rsf = calcul_rsf_pondere(df, 820)
    return rsf

def calcul_row_830(df):
    """Calcule le RSF de la ligne 830 avec pondérations (100%, 100%, et 100%)."""
    rsf = calcul_rsf_pondere(df, 830)
    return rsf

def calcul_row_800(df):
    """Calcule le RSF de la ligne 800 (other loans to non-financial customers)."""
    rsf_810 = calcul_row_810(df)
    rsf_820 = calcul_row_820(df)
    rsf_830 = calcul_row_830(df)
    rsf_800 = rsf_810 + rsf_820 + rsf_830
    df.loc[df['row'] == 800, '0130'] = rsf_800
    return rsf_800

def calcul_row_840(df):
    """Calcule le RSF de la ligne 840 avec pondements (10%, 50%, et 85%)."""
    rsf = calcul_rsf_pondere(df, 840)
    return rsf

##################################################################
def calcul_row_620(df):
    """Calcule le RSF from loans somme de 630 à 840"""
    rsf_630 = calcul_row_630(df)
    rsf_640 = calcul_row_640(df)
    rsf_730 = calcul_row_730(df)
    rsf_740 = calcul_row_740(df)
    rsf_750 = calcul_row_750(df)
    rsf_800 = calcul_row_800(df)
    rsf_840 = calcul_row_840(df)
    rsf_620 = rsf_630 + rsf_640 + rsf_730 + rsf_740 + rsf_750 + rsf_800 + rsf_840
    df.loc[df['row'] == 620, '0130'] = rsf_620
    return rsf_620

def calcul_row_860(df):
    """Calcule le RSF de la ligne 860 (centralised regulated savings)."""
    rsf = calcul_rsf_pondere(df, 860)
    return rsf

def calcul_row_870(df):
    """Calcule le RSF de la ligne 870 (promotional loans and credit and liquidity facilities)."""
    rsf = calcul_rsf_pondere(df, 870)
    return rsf

def calcul_row_880(df):
    """Calcule le RSF de la ligne 880 (eligible covered bonds)."""
    rsf = calcul_rsf_pondere(df, 880)
    return rsf

def calcul_row_890(df):
    """Calcule le RSF de la ligne 890 (derivatives client clearing activities)."""
    rsf = calcul_rsf_pondere(df, 890)
    return rsf

def calcul_row_900(df):
    """Calcule le RSF de la ligne 900 (others)."""
    rsf = calcul_rsf_pondere(df, 900)
    return rsf
def calcul_row_850(df):
    """Calcule le RSF de la ligne 850 (RSF from independent assets)."""
    rsf_860 = calcul_row_860(df)
    rsf_870 = calcul_row_870(df)
    rsf_880 = calcul_row_880(df)
    rsf_890 = calcul_row_890(df)
    rsf_900 = calcul_row_900(df)
    rsf_850 = rsf_860 + rsf_870 + rsf_880 + rsf_890 + rsf_900
    df.loc[df['row'] == 850, '0130'] = rsf_850
    return rsf_850

def calcul_row_910(df):
    """Calcule le RSF de la ligne 910 (assets within a group or an IPS if subject to preferential treatment)."""
    rsf = calcul_rsf_pondere(df, 910)
    return rsf


def calcul_row_930(df):
    """Calcule le RSF de la ligne 930 (required stable funding for derivative liabilities) avec pondération (5%)."""
    rsf = calcul_rsf_pondere(df, 930)
    return rsf

def calcul_row_940(df):
    """Calcule le RSF de la ligne 940 (NSFR derivative assets) avec pondération (100%)."""
    rsf = calcul_rsf_pondere(df, 940)
    return rsf

def calcul_row_950(df):
    """Calcule le RSF de la ligne 950 (initial margin posted) avec pondération (85%)."""
    rsf = calcul_rsf_pondere(df, 950)
    return rsf

def calcul_row_920(df):
    """Calcule le RSF de la ligne 920 (RSF from derivatives)."""
    rsf_930 = calcul_row_930(df)
    rsf_940 = calcul_row_940(df)
    rsf_950 = calcul_row_950(df)
    rsf_920 = rsf_930 + rsf_940 + rsf_950
    df.loc[df['row'] == 920, '0130'] = rsf_920
    return rsf_920
def calcul_row_960(df):
    """Calcule le RSF de la ligne 960 (contributions to CCP default fund) avec pondération (85%)."""
    rsf = calcul_rsf_pondere(df, 960)
    return rsf

def calcul_row_990(df):
    """Calcule le RSF de la ligne 990 (unencumbered or encumbered for a residual maturity of less than one year) avec pondération (85%)."""
    rsf = calcul_rsf_pondere(df, 990)
    return rsf

def calcul_row_1000(df):
    """Calcule le RSF de la ligne 1000 (encumbered for a residual maturity of one year or more) avec pondération (100%)."""
    rsf = calcul_rsf_pondere(df, 1000)
    return rsf

def calcul_row_980(df):
    """Calcule le RSF de la ligne 980 (physically traded commodities)."""
    rsf_990 = calcul_row_990(df)
    rsf_1000 = calcul_row_1000(df)
    rsf_980 = rsf_990 + rsf_1000
    df.loc[df['row'] == 980, '0130'] = rsf_980
    return rsf_980

def calcul_row_1010(df):
    """Calcule le RSF de la ligne 1010 (trade date receivables) avec pondération (0%)."""
    rsf = calcul_rsf_pondere(df, 1010)
    return rsf

def calcul_row_1020(df):
    """Calcule le RSF de la ligne 1020 (non-performing assets) avec pondération (100%)."""
    rsf = calcul_rsf_pondere(df, 1020)
    return rsf

def calcul_row_1030(df):
    """Calcule le RSF de la ligne 1030 (other assets) avec pondération (50%)."""
    rsf = calcul_rsf_pondere(df, 1030)
    return rsf

###################################################

def calcul_row_970(df):
    """Calcule le RSF de la ligne 970 (other assets)."""
    rsf_980 = calcul_row_980(df)
    rsf_1010 = calcul_row_1010(df)
    rsf_1020 = calcul_row_1020(df)
    rsf_1030 = calcul_row_1030(df)
    rsf_970 =rsf_980 + rsf_1010 + rsf_1020 + rsf_1030
    df.loc[df['row'] == 970, '0130'] = rsf_970
    return rsf_970

#RSF from OBS items

def calcul_row_1050(df):
    """Calcule le RSF de la ligne 1050 (committed facilities within a group or an IPS if subject to preferential treatment) """
    rsf = calcul_rsf_pondere(df, 1050)
    return rsf

def calcul_row_1060(df):
    """Calcule le RSF de la ligne 1060 (committed facilities)."""
    rsf = calcul_rsf_pondere(df, 1060)
    return rsf

def calcul_row_1070(df):
    """Calcule le RSF de la ligne 1070 (trade finance off-balance sheet items) """
    rsf = calcul_rsf_pondere(df, 1070)
    return rsf

def calcul_row_1080(df):
    """Calcule le RSF de la ligne 1080 (non-performing off-balance sheet items)"""
    rsf = calcul_rsf_pondere(df, 1080)
    return rsf

def calcul_row_1090(df):
    """Calcule le RSF de la ligne 1090 (other off-balance sheet exposures for which the competent authority has determined RSF factors)."""
    rsf = calcul_rsf_pondere(df, 1080)
    return rsf

def calcul_row_1040(df):
    """Calcule le RSF de la ligne 1040 ."""
    rsf_1050 = calcul_row_1050(df)
    rsf_1060 = calcul_row_1060(df)
    rsf_1070 = calcul_row_1070(df)
    rsf_1080 = calcul_row_1080(df)
    rsf_1090 = calcul_row_1090(df)
    rsf_1040 = rsf_1050 + rsf_1060 + rsf_1070 + rsf_1080 + rsf_1090
    df.loc[df['row'] == 1040, '0130'] = rsf_1040
    return rsf_1040
def calcul_row_20(df):
  """Calcul REQUIRED STABLE FUNDING somme de 1.1 -> 1.10"""
  rsf_80 = calcul_row_80(df)
  rsf_560 = calcul_row_560(df)
  rsf_620 = calcul_row_620(df)
  rsf_850 = calcul_row_850(df)
  rsf_910 = calcul_row_910(df)
  rsf_920 = calcul_row_920(df)
  rsf_960 = calcul_row_960(df)
  rsf_970 = calcul_row_970(df)
  rsf_1040 = calcul_row_1040(df)
  rsf_20 = rsf_80 + rsf_560 + rsf_620 + rsf_850 + rsf_910 + rsf_920 + rsf_960 + rsf_970 + rsf_1040
  df.loc[df['row'] == 20, '0130'] = rsf_20
  return rsf_20

def calcul_RSF(df):
    RSF =calcul_row_20(df)
    print("RSF = ", RSF)
    return RSF