import streamlit as st
import pandas as pd

def format_large_number(num):
    """Format number with space as thousands separator and 2 decimal digits"""
    if pd.isna(num) or num == 0:
        return "0"
    return f"{num:,.2f}".replace(",", " ").replace(".", ".")

def format_number_espace(n):
    return f"{n:,.2f}".replace(",", " ").replace(".", ".")

def style_table(df, highlight_columns=None):
    """
    Stylise un tableau avec les couleurs PwC
    """
    # Couleurs PwC
    pwc_orange = "#d04a02"
    pwc_dark_blue = "#FFCDA8"
    pwc_light_gray = "#f5f0e6"
    
    # Style de base du tableau
    table_styles = [
        # Style de l'en-tête
        {"selector": "thead th", 
         "props": f"background-color: {pwc_dark_blue}; color: black; font-weight: bold; text-align: center; padding: 8px;"},
        # Style des cellules du corps
        {"selector": "tbody td", 
         "props": "padding: 6px; text-align: right;"},
        # Style des lignes alternées
        {"selector": "tbody tr:nth-child(odd) td", 
         "props": f"background-color: {pwc_light_gray};"},
        # Style de la première colonne
        {"selector": "tbody td:first-child", 
         "props": "text-align: center; font-weight: bold;"},
        # Style de la deuxième colonne (Description)
        {"selector": "tbody td:nth-child(2)", 
         "props": "text-align: left;"},
        # Style du tableau entier
        {"selector": "table", 
         "props": "width: 100%; border-collapse: collapse; font-size: 14px;"},
        # Bordure du tableau
        {"selector": "th, td", 
         "props": "border: 1px solid #ddd;"}
    ]
    
    # Convertir toutes les colonnes en type objet pour s'assurer que le formatage reste intact
    for col in df.columns:
        df[col] = df[col].astype(str)
    
    # Appliquer le style
    styled_df = df.style.set_table_styles(table_styles)
    
    # Mettre en évidence les colonnes de pourcentage si spécifiées
    if highlight_columns:
        for col in highlight_columns:
            if col in df.columns:
                styled_df = styled_df.set_properties(**{
                    'font-weight': 'bold',
                    'color': pwc_orange
                }, subset=[col])
    
    return styled_df


scenarios = {
    "idiosyncratique": {
        "Retrait massif des dépôts": ["Dépôts et avoirs de la clientèle"],
        "Tirage PNU": ["Créances clientèle"],
        "Défaillance client majeur": ["Créances sur la clientèle", "Provisions pour pertes sur prêts"],
        "Cyberattaque majeure": ["Autres passifs"],
        "Pertes juridiques": ["Résultat consolidé"],
        "Augmentation soudaine des exigences en capital": ["Capital social", "Emprunts et ressources spéciales"]
    },
    "macroéconomique": {
        "Détérioration portefeuille d’investissement": ["Portefeuille-titres commercial"],
        "Effondrement du marché immobilier": ["Valeurs immobilisées", "Créances sur la clientèle", "Portefeuille d’investissement immobilier"],
        "Retrait massif des dépôts": ["Dépôts et avoirs de la clientèle"]
    }
}
