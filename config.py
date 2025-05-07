scenarios = {
    "idiosyncratique": {
        "Retrait massif des dépôts": ["Dépôts et avoirs de la clientèle"],
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

# --- CONTREPARTIES RÉELLES ---
contreparties = {
    "Dépôts et avoirs de la clientèle": [
<<<<<<< HEAD
        "Portefeuille d’investissement",
        "Créances sur les établissements bancaires et financiers"
=======
        "Portefeuille",
        "Créances banques autres"
>>>>>>> nour
    ],
    "Créances sur la clientèle": [
        "Provisions pour pertes sur prêts",
        "Résultat consolidé"
    ],
    "Provisions pour pertes sur prêts": [
        "Résultat consolidé"
    ],
    "Autres passifs": [
        "Résultat consolidé"
    ],
    "Résultat consolidé": [
        "Créances sur la clientèle"
    ],
    "Capital social": [
        "Portefeuille d’investissement"
    ],
    "Emprunts et ressources spéciales": [
        "Portefeuille d’investissement"
    ],
    "Portefeuille-titres commercial": [
        "Provisions pour pertes sur titres",
        "Résultat consolidé"
    ],
    "Valeurs immobilisées": [
        "Provisions pour pertes sur prêts",
        "Réserves consolidées"
    ],
    "Portefeuille d’investissement immobilier": [
        "Provisions pour pertes sur prêts",
        "Réserves consolidées"
    ]
}

# --- MAPPING COREP (CAPITAL) ---
corep_capital_mapping = {
    "Dépôts et avoirs de la clientèle": {},

    "Créances sur la clientèle": {
        "Solvabilité": ["Retail exposures", "Exposures in default"],
        "Levier": ["Exposures to retail"]
    },

    "Provisions pour pertes sur prêts": {
        "Solvabilité": ["Retained earnings"]
    },

    "Résultat consolidé": {
        "Solvabilité": ["Retained earnings"]
    },

    "Capital social": {
        "Solvabilité": ["Capital instruments eligible as CET1 Capital"]
    },

    "Emprunts et ressources spéciales": {
        "Solvabilité": ["Capital instruments eligible as Tier 2 Capital"]
    },

    "Portefeuille-titres commercial": {
        "Solvabilité": ["Trading book exposures"],
        "Levier": ["Trading book assets"]
    },

    "Portefeuille d’investissement immobilier": {
        "Solvabilité": ["Real estate exposures"],
        "Levier": ["Real estate assets"]
    },

    "Valeurs immobilisées": {
        "Solvabilité": ["Other assets"],
        "Levier": ["Property, plant and equipment"]
    },

    "Portefeuille d’investissement": {
        "Solvabilité": ["Equity exposures"]
    },

    "Provisions pour pertes sur titres": {
        "Solvabilité": ["Retained earnings"]
    },

    "Réserves consolidées": {
        "Solvabilité": ["Retained earnings"]
    },

    "Créances sur les établissements bancaires et financiers": {
        "Solvabilité": ["Exposures to institutions"]
    }
}

# --- MAPPING COREP (LIQUIDITÉ) ---
corep_liquidite_mapping = {
    "Dépôts et avoirs de la clientèle": {
        "LCR": ["Outflows – Retail Deposits", "Outflows – Unsecured Wholesale"],
        "NSFR": ["Liabilities with residual maturity ≤ 6m"]
    },
    "Créances sur la clientèle": {
        "LCR": ["Inflows – Performing Retail Loans"],
        "NSFR": ["Loans with maturity > 1y"]
    },
    "Résultat consolidé": {
        "LCR": ["Other inflows/outflows"],
        "NSFR": ["Stable funding adjustments"]
    },
    "Provisions pour pertes sur prêts": {
        "LCR": ["Other outflows"],
        "NSFR": ["Adjustments to funding needs"]
    },
    "Capital social": {
        "NSFR": ["Stable funding sources"]
    },
    "Emprunts et ressources spéciales": {
        "LCR": ["Outflows – Long-term funding"],
        "NSFR": ["Additional available stable funding"]
    }
}
