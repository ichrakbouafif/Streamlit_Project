import streamlit as st
import pandas as pd

def format_large_number(num):
    """Format number with space as thousands separator and 2 decimal digits"""
    if pd.isna(num) or num == 0:
        return "0"
    return f"{num:,.2f}".replace(",", " ").replace(".", ".")

def format_number_espace(n):
    return f"{n:,.2f}".replace(",", " ").replace(".", ".")


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
