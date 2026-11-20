"""Chargement du modèle exporté par le notebook et prédiction de fraude.

Ce module est partagé par l'interface Tkinter (interface_tkinter.py) et le site Django (fraud_api/).

    from predicteur import ModeleFraude
    modele = ModeleFraude()
    resultat = modele.predire({"Time": 0, "Amount": 149.62, "V1": -1.36, ...})
"""
import sys
import threading
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent
CHEMIN_MODELE = RACINE / "models" / "fraud_detection_model.joblib"
CHEMIN_DONNEES = RACINE / "data" / "raw" / "creditcard.csv"

COLONNES_V = [f"V{i}" for i in range(1, 29)]
COLONNES_BRUTES = ["Time"] + COLONNES_V + ["Amount"]
COLONNES_MODELE = COLONNES_V + ["Amount_log", "Heure_sin", "Heure_cos"]
PART_TEST = 0.20  # identique au notebook : les 20 % de transactions les plus récentes


# --- Création des variables : copie exacte de la fonction du notebook (section 3.3) ---
def heure_du_jour(time_secondes):
    return (np.asarray(time_secondes, dtype=float) % 86400) / 3600


def ajouter_variables(X):
    heure = heure_du_jour(X["Time"])
    sortie = X[COLONNES_V].astype(float).copy()
    sortie["Amount_log"] = np.log1p(X["Amount"].astype(float).clip(lower=0))
    sortie["Heure_sin"] = np.sin(2 * np.pi * heure / 24)
    sortie["Heure_cos"] = np.cos(2 * np.pi * heure / 24)
    return sortie[COLONNES_MODELE]


# Le modèle a été enregistré depuis le notebook : il cherche « ajouter_variables » dans __main__.
sys.modules["__main__"].ajouter_variables = ajouter_variables

DECISIONS = {
    "bloquer": {"libelle": "Bloquer", "detail": "Score très élevé : transaction bloquée automatiquement."},
    "verifier": {"libelle": "Vérifier", "detail": "Transaction suspecte : un analyste doit contacter le client."},
    "accepter": {"libelle": "Accepter", "detail": "Aucun signal de fraude : transaction acceptée."},
}

NOMS_LISIBLES = {"Amount_log": "Montant", "Heure_sin": "Heure (sin)", "Heure_cos": "Heure (cos)"}


class ModeleFraude:
    """Le modèle exporté, ses seuils, et les transactions réelles de la période de test."""

    def __init__(self, chemin_modele=CHEMIN_MODELE, chemin_donnees=CHEMIN_DONNEES):
        paquet = joblib.load(chemin_modele)
        self.pipeline = paquet["pipeline"]
        self.seuil_alerte = float(paquet["seuil_alerte"])
        self.seuil_blocage = float(paquet["seuil_blocage"])
        self.colonnes_entree = list(paquet["colonnes_entree"])
        self.infos = {k: v for k, v in paquet.items() if k != "pipeline"}
        self.chemin_donnees = Path(chemin_donnees)
        self._test = None
        self._explicateur = None
        self._verrou = threading.Lock()

    # ---------- Prédiction ----------
    def decision(self, score):
        if score >= self.seuil_blocage:
            return "bloquer"
        if score >= self.seuil_alerte:
            return "verifier"
        return "accepter"

    def preparer(self, transactions):
        """Accepte un dict (une transaction) ou un DataFrame ; renvoie un DataFrame propre."""
        if isinstance(transactions, dict):
            transactions = pd.DataFrame([transactions])
        manquantes = [c for c in self.colonnes_entree if c not in transactions.columns]
        if manquantes:
            raise ValueError(f"Colonnes manquantes : {', '.join(manquantes)}")
        X = transactions[self.colonnes_entree].apply(pd.to_numeric, errors="coerce")
        if X.isna().any().any():
            lignes = X.index[X.isna().any(axis=1)].tolist()[:5]
            raise ValueError(f"Valeurs non numériques ou vides (lignes {lignes})")
        if (X["Amount"] < 0).any():
            raise ValueError("Le montant ne peut pas être négatif")
        if (X["Time"] < 0).any():
            raise ValueError("Time ne peut pas être négatif")
        return X

    def scores(self, transactions, n_jobs=1):
        X = self.preparer(transactions)
        modele = self.pipeline.named_steps["model"]
        if hasattr(modele, "n_jobs"):
            modele.n_jobs = n_jobs
        return self.pipeline.predict_proba(X)[:, 1]

    def predire(self, transaction):
        """Prédit une seule transaction (dict ou DataFrame d'une ligne)."""
        score = float(self.scores(transaction)[0])
        cle = self.decision(score)
        return {"score": score, "decision": cle, **DECISIONS[cle],
                "seuil_alerte": self.seuil_alerte, "seuil_blocage": self.seuil_blocage}

    def predire_lot(self, transactions):
        """Prédit un DataFrame de transactions ; renvoie le DataFrame enrichi du score et de la décision."""
        X = self.preparer(transactions)
        s = self.scores(X, n_jobs=-1)
        sortie = transactions.copy()
        sortie["score_fraude"] = np.round(s, 4)
        sortie["decision"] = [DECISIONS[self.decision(v)]["libelle"] for v in s]
        return sortie

    # ---------- Explication (SHAP) ----------
    def expliquer(self, transaction, n=8):
        """Contribution des variables au score (valeurs SHAP).

        Renvoie {"base": score moyen de départ, "contributions": [...]} ou None si SHAP est indisponible.
        Score de la transaction = base + somme de toutes les contributions.
        """
        try:
            import warnings
            warnings.filterwarnings("ignore")
            import shap
        except Exception:
            return None
        X = self.preparer(transaction)
        variables = self.pipeline.named_steps["variables"].transform(X)
        X_modele = self.pipeline.named_steps["scaler"].transform(variables)
        with self._verrou:
            if self._explicateur is None:
                self._explicateur = shap.TreeExplainer(self.pipeline.named_steps["model"])
            valeurs = self._explicateur.shap_values(X_modele)
        valeurs = np.asarray(valeurs)
        if valeurs.ndim == 3:          # (transactions, variables, classes)
            valeurs = valeurs[0, :, 1]
        elif valeurs.ndim == 2:
            valeurs = valeurs[0]
        brut = variables.iloc[0]
        contributions = [
            {"variable": NOMS_LISIBLES.get(nom, nom),
             "valeur": float(X["Amount"].iloc[0]) if nom == "Amount_log" else float(brut[nom]),
             "contribution": float(v)}
            for nom, v in zip(COLONNES_MODELE, valeurs)
        ]
        contributions.sort(key=lambda c: abs(c["contribution"]), reverse=True)
        base = np.ravel(self._explicateur.expected_value)
        return {"base": float(base[-1]), "contributions": contributions[:n]}

    # ---------- Transactions réelles de la période de test ----------
    def donnees_test(self):
        """Les 20 % de transactions les plus récentes : le modèle ne les a jamais vues."""
        with self._verrou:
            if self._test is None:
                df = pd.read_csv(self.chemin_donnees)
                df = df.drop_duplicates().sort_values("Time", kind="stable").reset_index(drop=True)
                self._test = df.iloc[int(len(df) * (1 - PART_TEST)):]
        return self._test

    def exemple(self, type_exemple="aleatoire", graine=None):
        """Une vraie transaction du test : 'fraude', 'normale' ou 'aleatoire'. Renvoie (dict, classe réelle)."""
        test = self.donnees_test()
        if type_exemple == "fraude":
            test = test[test["Class"] == 1]
        elif type_exemple == "normale":
            test = test[test["Class"] == 0]
        ligne = test.sample(1, random_state=graine).iloc[0]
        return {c: float(ligne[c]) for c in self.colonnes_entree}, int(ligne["Class"])
