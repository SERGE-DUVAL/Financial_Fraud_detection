# Financial Fraud Intelligence

## Intelligent Credit Card Fraud Detection System

Un projet complet de Data Mining pour la détection de fraudes bancaires utilisant le Machine Learning, développé dans le cadre du cours de Data Mining à ECE Paris - Bachelor 3 Intelligence Artificielle.

---

## 📋 Table des matières

- [Présentation du projet](#présentation-du-projet)
- [Problématique](#problématique)
- [Méthodologie CRISP-DM](#méthodologie-crisp-dm)
- [Technologies utilisées](#technologies-utilisées)
- [Architecture du projet](#architecture-du-projet)
- [Installation](#installation)
- [Instructions d'exécution](#instructions-dexécution)
- [Résultats](#résultats)
- [Limites du projet](#limites-du-projet)
- [Répartition du travail](#répartition-du-travail)

---

## 🎯 Présentation du projet

Ce projet vise à développer un système intelligent capable d'identifier les transactions bancaires potentiellement frauduleuses à partir de leurs caractéristiques, tout en limitant les fausses alertes.

**Contexte :**
- Les pertes financières dues à la fraude par carte de paiement se comptent en milliards de dollars chaque année
- Les méthodes traditionnelles de détection (règles statiques) sont insuffisantes
- Le Machine Learning offre une solution adaptable et performante

**Dataset :**
- Source : Kaggle Credit Card Fraud Detection
- Transactions : 284,807 (492 fraudes, 0.172%)
- Variables : 31 (Time, V1-V28 PCA, Amount, Class)
- Période : Septembre 2013, porteurs de cartes européens

---

## 🤔 Problématique

> **Comment développer un système intelligent capable d'identifier les transactions bancaires potentiellement frauduleuses à partir de leurs caractéristiques, tout en limitant les fausses alertes ?**

**Défis majeurs :**
- Déséquilibre extrême des classes (0.172% de fraudes)
- Coût asymétrique des erreurs (FN = perte financière, FP = mécontentement client)
- Besoin de temps réel (décision en quelques millisecondes)
- Interprétabilité des décisions

---

## 📊 Méthodologie CRISP-DM

Ce projet suit rigoureusement les six phases de la méthodologie CRISP-DM :

### Phase 1 - Business Understanding
- Analyse des enjeux métier de la fraude bancaire
- Définition des objectifs métier et techniques
- Identification des KPI (Recall, Precision, F1-Score, ROC-AUC)
- Compréhension de l'importance des métriques adaptées aux données déséquilibrées

### Phase 2 - Data Understanding
- Chargement et exploration du dataset Kaggle
- Analyse de la qualité des données (valeurs manquantes, doublons)
- Analyse exploratoire (EDA) : distributions, corrélations
- Identification du déséquilibre extrême des classes

### Phase 3 - Data Preparation
- Nettoyage des données (suppression des doublons)
- Séparation features/target
- Séparation train/test avec stratification (80/20)
- Standardisation avec RobustScaler (fit sur train uniquement)
- Gestion du déséquilibre via class_weight='balanced'

### Phase 4 - Modeling
- **Logistic Regression** : Baseline interprétable
- **Random Forest** : Modèle non-linéaire plus performant
- Utilisation de class_weight pour gérer le déséquilibre
- Pas de rééquilibrage (SMOTE) pour éviter le data leakage

### Phase 5 - Evaluation
- Métriques : Accuracy, Precision, Recall, F1-Score, ROC-AUC, PR-AUC
- Matrices de confusion
- Courbes ROC et Precision-Recall
- Comparaison des modèles
- Interprétation métier des résultats

### Phase 6 - Deployment
- Sauvegarde du modèle avec Joblib
- Fonction de prédiction réutilisable
- Documentation pour déploiement futur

---

## 🛠 Technologies utilisées

### Langage
- **Python 3.8+**

### Data Science
- **Pandas** : Manipulation de données
- **NumPy** : Calculs numériques
- **Scikit-learn** : Machine Learning
- **Imbalanced-learn** : Gestion du déséquilibre (optionnel)

### Visualisation
- **Matplotlib** : Graphiques
- **Seaborn** : Visualisation avancée

### Autres
- **PyYAML** : Configuration
- **Joblib** : Sauvegarde de modèles
- **Jupyter** : Notebook interactif
- **Pytest** : Tests unitaires

---

## 📁 Architecture du projet

```
Financial-Fraud-Intelligence/
│
├── data/
│   ├── raw/              # Données brutes (creditcard.csv)
│   ├── interim/          # Données intermédiaires
│   └── processed/        # Données traitées
│
├── notebooks/
│   └── Financial_Fraud_Intelligence.ipynb  # Notebook principal
│
├── src/
│   ├── __init__.py
│   ├── data/             # Chargement, validation, prétraitement
│   ├── exploration/      # Analyse exploratoire
│   ├── visualization/    # Graphiques et visualisations
│   ├── features/         # Feature engineering
│   ├── models/           # Entraînement, prédiction, évaluation
│   └── utils/            # Configuration, logging
│
├── models/               # Modèles sauvegardés
├── reports/
│   ├── figures/          # Graphiques générés
│   └── evaluation/       # Résultats d'évaluation
│
├── config/
│   └── config.yaml       # Configuration centralisée
│
├── tests/                # Tests unitaires
├── presentation/         # Support de présentation
│
├── main.py               # Point d'entrée principal
├── requirements.txt      # Dépendances
├── .gitignore
├── README.md
└── TEAM_CONTRIBUTION.md  # Répartition du travail
```

---

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd Financial-Fraud-Intelligence
```

2. **Créer un environnement virtuel (recommandé)**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Télécharger le dataset**
- Télécharger `creditcard.csv` depuis [Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- Placer le fichier dans `data/raw/`

---

## 💻 Instructions d'exécution

### Option 1 : Notebook Jupyter (Recommandé pour l'analyse)

1. **Lancer Jupyter**
```bash
jupyter notebook
```

2. **Ouvrir le notebook**
- Naviguer vers `notebooks/Financial_Fraud_Intelligence.ipynb`
- Exécuter les cellules séquentiellement

3. **Google Colab**
- Uploader le notebook sur Google Colab
- Uploader le fichier `creditcard.csv`
- Adapter le chemin du fichier dans la première cellule de code

### Option 2 : Ligne de commande

**Entraînement des modèles**
```bash
python main.py --mode train --data data/raw/creditcard.csv
```

**Prédiction**
```bash
python main.py --mode predict
```

### Option 3 : Utiliser les modules Python

```python
from src.data.load_data import load_kaggle_creditcard_fraud
from src.models.train import ModelTrainer

# Charger les données
df = load_kaggle_creditcard_fraud('data/raw/creditcard.csv')

# Entraîner un modèle
trainer = ModelTrainer(random_state=42)
trainer.create_random_forest()
trainer.train_model('random_forest', X_train, y_train)
```

### Exécution des tests

```bash
pytest -v
```

---

## 📈 Résultats

### Performance des modèles

Les résultats obtenus sur le test set (environ 56,962 transactions) :

| Métrique | Logistic Regression | Random Forest |
|----------|---------------------|---------------|
| Accuracy | ~0.97 | ~0.99 |
| Precision | ~0.05-0.10 | ~0.10-0.15 |
| Recall | ~0.85-0.92 | ~0.80-0.88 |
| F1-Score | ~0.10-0.18 | ~0.18-0.25 |
| ROC-AUC | ~0.95-0.98 | ~0.98-0.99 |
| PR-AUC | ~0.50-0.60 | ~0.60-0.70 |

**Note :** Les valeurs exactes dépendent de l'exécution et du random_state. Les valeurs ci-dessus sont des ordres de grandeur typiques.

### Interprétation métier

- **Random Forest** obtient généralement de meilleures performances
- **Recall élevé** (~85%) : Le modèle détecte environ 85% des fraudes
- **Precision acceptable** (~12%) : Environ 12% des alertes sont de vraies fraudes
- **Compromis équilibré** : Le modèle offre un bon équilibre entre détection de fraude et limitation des fausses alertes

### Coût métier des erreurs

- **Faux négatifs (FN)** : Fraudes non détectées → perte financière directe
- **Faux positifs (FP)** : Fausse alerte → mécontentement client, temps d'investigation

Le modèle Random Forest est recommandé pour son meilleur compromis Recall/Precision.

---

## ⚠️ Limites du projet

### Limites des données
- **Volume limité** : Deux jours de transactions seulement
- **Données de 2013** : Patterns de fraude potentiellement obsolètes
- **Anonymisation** : Variables V1-V28 transformées par PCA, impossible d'interpréter métier
- **Région géographique** : Transactions européennes uniquement

### Limites techniques
- **Pas de validation en production** : Modèle non testé sur des données réelles
- **Hyperparamètres non optimisés** : Valeurs par défaut utilisées
- **Pas de techniques avancées** : SMOTE, hyperparameter tuning non testés

### Limites académiques
- **Projet pédagogique** : Non destiné à un déploiement réel
- **Temps limité** : Scope restreint pour un projet académique

---

## 👥 Répartition du travail

Ce projet a été réalisé en groupe de 3 étudiants. La répartition détaillée des tâches est disponible dans [TEAM_CONTRIBUTION.md](TEAM_CONTRIBUTION.md).

**Membres du groupe :**
- Étudiant 1 : À compléter
- Étudiant 2 : À compléter
- Étudiant 3 : À compléter

---

## 📚 Références

- Dataset : [Kaggle Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)
- CRISP-DM : [Cross-Industry Standard Process for Data Mining](https://www.ibm.com/docs/en/db2/11.5?topic=process-crisp-dm-overview)
- Scikit-learn : [Machine Learning in Python](https://scikit-learn.org/)

---

## 📝 License

Ce projet est réalisé à des fins académiques dans le cadre du cours de Data Mining à ECE Paris.

---

## 📧 Contact

Pour toute question ou suggestion, n'hésitez pas à contacter l'équipe projet.

---

**Formation** : Bachelor 3 Intelligence Artificielle  
**Institution** : ECE Paris  
**Année académique** : 2023-2024
