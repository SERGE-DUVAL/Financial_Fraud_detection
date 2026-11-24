"""Application Web Streamlit - Financial Fraud Intelligence
Système interactif de détection de fraude bancaire par Machine Learning.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# Configuration du chemin du projet
RACINE = Path(__file__).resolve().parent
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from predicteur import ModeleFraude, DECISIONS, NOMS_LISIBLES

# -----------------------------------------------------------------------------
# Configuration de la page Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Financial Fraud Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Style CSS personnalisé pour un rendu professionnel
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-bloquer {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
        border: 1px solid #F87171;
    }
    .badge-verifier {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
        border: 1px solid #FBBF24;
    }
    .badge-accepter {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.4rem 0.8rem;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.2rem;
        display: inline-block;
        border: 1px solid #34D399;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Chargement du modèle (mis en cache pour la rapidité)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Chargement du modèle de détection...")
def charger_modele():
    try:
        return ModeleFraude()
    except Exception as e:
        st.error(f"Erreur lors du chargement du modèle : {e}")
        return None

modele = charger_modele()

if modele is None:
    st.stop()


# -----------------------------------------------------------------------------
# Barre latérale (Sidebar) - Navigation et Seuils décisionnels
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=64)
    st.title("Fraud Intelligence")
    st.markdown("**ECE Paris - Bachelor 3 IA**")
    st.markdown("Projet de Data Mining")
    st.divider()

    menu = st.radio(
        "Navigation",
        [
            "🔍 Détection Unitaire",
            "📁 Détection par Lot (CSV)",
            "📊 Métriques & Coût Métier",
            "ℹ️ Architecture & Méthodologie"
        ],
        index=0
    )

    st.divider()
    st.subheader("⚙️ Seuils Décisionnels")
    st.caption("Ajustez la sensibilité du système de scoring :")

    seuil_alerte = st.slider(
        "Seuil d'alerte (Vérification)",
        min_value=0.01,
        max_value=0.50,
        value=float(modele.seuil_alerte),
        step=0.01,
        help="En dessous : Accepté. Au-dessus : Envoyé à un analyste bancaire."
    )

    seuil_blocage = st.slider(
        "Seuil de blocage (Automatique)",
        min_value=0.50,
        max_value=0.99,
        value=float(modele.seuil_blocage),
        step=0.01,
        help="Au-dessus : Transaction bloquée immédiatement."
    )

    # Mise à jour dynamique des seuils
    modele.seuil_alerte = seuil_alerte
    modele.seuil_blocage = seuil_blocage

    st.info(
        f"🟢 **< {seuil_alerte:.2f}** : Accepté\n\n"
        f"🟡 **{seuil_alerte:.2f} à {seuil_blocage:.2f}** : Vérifier\n\n"
        f"🔴 **≥ {seuil_blocage:.2f}** : Bloquer"
    )


# -----------------------------------------------------------------------------
# ONGLET 1 : DÉTECTION UNITAIRE
# -----------------------------------------------------------------------------
if menu == "🔍 Détection Unitaire":
    st.markdown('<div class="main-header">🛡️ Analyse en Temps Réel d\'une Transaction</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Testez une transaction manuellement ou chargez un exemple réel du jeu de test.</div>', unsafe_allow_html=True)

    # Boutons d'exemples rapides
    st.markdown("##### ⚡ Remplissage rapide depuis des données réelles")
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    if "current_trans" not in st.session_state:
        # Valeur par défaut
        st.session_state.current_trans = {c: 0.0 for c in modele.colonnes_entree}
        st.session_state.current_trans["Amount"] = 50.0
        st.session_state.current_trans["Time"] = 3600.0
        st.session_state.source_info = "Valeurs par défaut"

    with col_btn1:
        if st.button("🟢 Charger une transaction Normale", use_container_width=True):
            try:
                ex, real_cls = modele.exemple("normale")
                st.session_state.current_trans = ex
                st.session_state.source_info = "Exemple réel du test set : Transaction Légitime (Classe 0)"
                st.rerun()
            except Exception as e:
                st.warning(f"Impossible de charger le jeu de test : {e}")

    with col_btn2:
        if st.button("🔴 Charger une Vraie Fraude", use_container_width=True):
            try:
                ex, real_cls = modele.exemple("fraude")
                st.session_state.current_trans = ex
                st.session_state.source_info = "Exemple réel du test set : FRAUDE AVÉRÉE (Classe 1)"
                st.rerun()
            except Exception as e:
                st.warning(f"Impossible de charger le jeu de test : {e}")

    with col_btn3:
        if st.button("🎲 Transaction Aléatoire", use_container_width=True):
            try:
                ex, real_cls = modele.exemple("aleatoire")
                st.session_state.current_trans = ex
                nom_classe = "Fraude" if real_cls == 1 else "Normale"
                st.session_state.source_info = f"Exemple aléatoire réel (Vérité terrain : {nom_classe})"
                st.rerun()
            except Exception as e:
                st.warning(f"Impossible de charger le jeu de test : {e}")

    st.caption(f"📌 *Statut actuel : {st.session_state.get('source_info', '')}*")

    # Formulaire de saisie
    with st.form("form_transaction"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            amount = st.number_input(
                "Montant de la transaction (€)",
                min_value=0.0,
                max_value=50000.0,
                value=float(st.session_state.current_trans.get("Amount", 50.0)),
                step=10.0
            )
        with col_t2:
            time_val = st.number_input(
                "Temps écoulé (Time en secondes depuis 1re trans.)",
                min_value=0.0,
                value=float(st.session_state.current_trans.get("Time", 3600.0)),
                step=60.0
            )

        with st.expander("🛠️ Ajuster les variables PCA (V1 à V28)", expanded=False):
            st.caption("Les variables V1 à V28 sont les composantes principales anonymisées (PCA).")
            v_cols = st.columns(4)
            v_values = {}
            for i in range(1, 29):
                v_name = f"V{i}"
                with v_cols[(i - 1) % 4]:
                    val = float(st.session_state.current_trans.get(v_name, 0.0))
                    v_values[v_name] = st.number_input(v_name, value=val, step=0.1, format="%.3f")

        submitted = st.form_submit_button("🚀 Évaluer le risque de fraude", use_container_width=True)

    if submitted or "last_eval" in st.session_state:
        # Préparation du dictionnaire
        trans_dict = {"Time": time_val, "Amount": amount, **v_values}
        st.session_state.last_eval = trans_dict

        resultat = modele.predire(trans_dict)
        score = resultat["score"]
        decision = resultat["decision"]

        st.divider()
        st.markdown("### 📋 Résultat de l'analyse")

        col_res1, col_res2, col_res3 = st.columns([1.2, 1, 1.2])

        with col_res1:
            st.markdown("#### Décision du Système")
            if decision == "bloquer":
                st.markdown('<div class="badge-bloquer">🚨 BLOQUER LA TRANSACTION</div>', unsafe_allow_html=True)
                st.error("Score de risque très élevé. La transaction a été immédiatement interceptée.")
            elif decision == "verifier":
                st.markdown('<div class="badge-verifier">⚠️ VÉRIFICATION REQUISE</div>', unsafe_allow_html=True)
                st.warning("Suspicion modérée. Une alerte a été transmise à l'analyste pour confirmation auprès du porteur.")
            else:
                st.markdown('<div class="badge-accepter">✅ TRANSACTION ACCEPTÉE</div>', unsafe_allow_html=True)
                st.success("Aucune anomalie critique détectée. Paiement validé.")

        with col_res2:
            st.markdown("#### Probabilité de Fraude")
            st.metric(label="Score prédictif", value=f"{score * 100:.2f} %")
            st.progress(min(score, 1.0))

        with col_res3:
            st.markdown("#### Positionnement par rapport aux seuils")
            st.write(f"- Seuil d'alerte : **{modele.seuil_alerte:.2f}**")
            st.write(f"- Seuil de blocage : **{modele.seuil_blocage:.2f}**")
            st.write(f"- Montant évalué : **{amount:.2f} €**")

        # Explication SHAP
        st.divider()
        st.markdown("### 🧠 Explicabilité du Modèle (XAI - Valeurs SHAP)")
        st.caption("Comprendre pourquoi l'algorithme a pris cette décision (obligation de transparence bancaire ACPR / RGPD) :")

        with st.spinner("Calcul des contributions SHAP..."):
            explication = modele.expliquer(trans_dict, n=8)

        if explication and "contributions" in explication:
            contribs = explication["contributions"]
            df_shap = pd.DataFrame(contribs)
            
            fig, ax = plt.subplots(figsize=(8, 3.8))
            couleurs = ['#EF4444' if c > 0 else '#10B981' for c in df_shap["contribution"]]
            
            y_pos = range(len(df_shap))
            ax.barh(y_pos, df_shap["contribution"], color=couleurs)
            ax.set_yticks(y_pos)
            labels = [f"{row['variable']} ({row['valeur']:.2f})" for _, row in df_shap.iterrows()]
            ax.set_yticklabels(labels)
            ax.invert_yaxis()
            ax.axvline(0, color='gray', linestyle='--', linewidth=0.8)
            ax.set_xlabel("Impact sur le score de fraude (Rouge = augmente le risque, Vert = diminue)")
            ax.set_title("Top variables influentes sur cette transaction", fontsize=11, fontweight='bold')
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Le module SHAP est en cours d'initialisation ou indisponible pour cette configuration.")


# -----------------------------------------------------------------------------
# ONGLET 2 : DÉTECTION PAR LOT (CSV)
# -----------------------------------------------------------------------------
elif menu == "📁 Détection par Lot (CSV)":
    st.markdown('<div class="main-header">📁 Analyse en Lot de Transactions (Batch)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Chargez un fichier CSV de transactions pour appliquer le modèle en masse.</div>', unsafe_allow_html=True)

    fichier_csv = st.file_uploader("Déposer un fichier CSV contenant les transactions", type=["csv"])

    col_opt1, col_opt2 = st.columns([2, 1])
    with col_opt2:
        charger_demo = st.button("📥 Charger un extrait de 500 transactions réelles", use_container_width=True)

    df_a_traiter = None

    if charger_demo:
        try:
            df_test = modele.donnees_test()
            df_a_traiter = df_test.sample(500, random_state=42)
            st.success("Extrait réel de 500 transactions chargé avec succès.")
        except Exception as e:
            st.error(f"Erreur : {e}")
    elif fichier_csv is not None:
        try:
            df_a_traiter = pd.read_csv(fichier_csv)
            st.success(f"Fichier chargé : {len(df_a_traiter)} transactions trouvées.")
        except Exception as e:
            st.error(f"Erreur de lecture CSV : {e}")

    if df_a_traiter is not None:
        st.divider()
        with st.spinner("Prédiction du lot en cours avec traitement multi-cœurs..."):
            resultats_df = modele.predire_lot(df_a_traiter)

        nb_total = len(resultats_df)
        nb_bloquer = (resultats_df["decision"] == "Bloquer").sum()
        nb_verifier = (resultats_df["decision"] == "Vérifier").sum()
        nb_accepter = (resultats_df["decision"] == "Accepter").sum()

        st.markdown("### 📊 Synthèse du lot")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total transactions", f"{nb_total:,}")
        col_m2.metric("🚨 Bloquées", f"{nb_bloquer} ({nb_bloquer/nb_total*100:.1f}%)")
        col_m3.metric("⚠️ À vérifier", f"{nb_verifier} ({nb_verifier/nb_total*100:.1f}%)")
        col_m4.metric("✅ Acceptées", f"{nb_accepter} ({nb_accepter/nb_total*100:.1f}%)")

        filtre = st.selectbox("Filtrer l'affichage par décision :", ["Toutes", "Bloquer", "Vérifier", "Accepter"])
        
        df_affiche = resultats_df
        if filtre != "Toutes":
            df_affiche = resultats_df[resultats_df["decision"] == filtre]

        st.dataframe(
            df_affiche[["Time", "Amount", "score_fraude", "decision"] + [f"V{i}" for i in range(1, 6)]],
            use_container_width=True,
            height=320
        )

        csv_export = resultats_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "💾 Télécharger les résultats avec scores (.CSV)",
            data=csv_export,
            file_name="resultats_detection_fraude.csv",
            mime="text/csv",
            use_container_width=True
        )


# -----------------------------------------------------------------------------
# ONGLET 3 : TABLEAU DE BORD & COÛT MÉTIER
# -----------------------------------------------------------------------------
elif menu == "📊 Métriques & Coût Métier":
    st.markdown('<div class="main-header">📊 Évaluation Métier & Matrice des Coûts</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Pourquoi l\'Accuracy est trompeuse et comment optimiser le coût réel pour la banque.</div>', unsafe_allow_html=True)

    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.markdown("""
        #### 🏦 Le piège de l'Accuracy en détection de fraude
        - Dans notre dataset, **99.83 %** des transactions sont normales et **0.17 %** sont des fraudes.
        - Un modèle bête qui dirait *"tout est normal"* aurait **99.83 % d'Accuracy**, mais laisserait passer **100 % des voleurs** !
        - **Les vraies métriques clés sont donc :**
          - **Rappel (Recall)** : Quelle proportion des fraudes a-t-on attrapée ?
          - **Précision** : Quand le modèle sonne l'alarme, est-ce vraiment un voleur ?
          - **PR-AUC (Precision-Recall AUC)** : La métrique de référence pour données déséquilibrées.
        """)

    with col_exp2:
        st.markdown("#### 💶 Simulateur de Perte Financière")
        cout_fn = st.number_input("Coût moyen d'une fraude manquée (Faux Négatif en €)", value=250.0, step=25.0)
        cout_fp = st.number_input("Coût de traitement d'une fausse alerte (Faux Positif en €)", value=10.0, step=1.0)
        st.caption("Le modèle cherche le seuil qui minimise : `(FN × Coût_FN) + (FP × Coût_FP)`.")

    st.divider()
    st.markdown("### 🏆 Comparatif des Modèles du Projet")

    perf_data = {
        "Modèle": ["Régression Logistique (Baseline)", "Random Forest (Sélectionné)", "LightGBM", "XGBoost"],
        "Recall Fraude": ["86.5 %", "88.2 %", "87.8 %", "88.9 %"],
        "Précision": ["64.2 %", "89.5 %", "88.1 %", "90.2 %"],
        "F1-Score": ["0.737", "0.888", "0.879", "0.895"],
        "PR-AUC": ["0.781", "0.865", "0.859", "0.872"],
        "Temps d'inférence (ms)": ["0.1 ms", "1.8 ms", "0.4 ms", "0.5 ms"]
    }
    st.table(pd.DataFrame(perf_data))


# -----------------------------------------------------------------------------
# ONGLET 4 : ARCHITECTURE & MÉTHODOLOGIE
# -----------------------------------------------------------------------------
elif menu == "ℹ️ Architecture & Méthodologie":
    st.markdown('<div class="main-header">ℹ️ Méthodologie CRISP-DM & Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Structure du projet développé dans le cadre du Bachelor 3 IA - ECE Paris.</div>', unsafe_allow_html=True)

    col_crisp1, col_crisp2 = st.columns(2)
    with col_crisp1:
        st.markdown("""
        #### 🔄 Les 6 Phases CRISP-DM
        1. **Business Understanding** : Comprendre les enjeux financiers et la tolérance aux faux positifs.
        2. **Data Understanding (TP 4)** : Exploration des 284 807 transactions et des 31 variables.
        3. **Data Preparation (TP 4)** : Nettoyage, suppression des doublons, standardisation robuste (`RobustScaler`), découpage Train (70%) / Test (30%).
        4. **Modeling** : Entraînement avec gestion du déséquilibre (`class_weight='balanced'`).
        5. **Evaluation** : Analyse de la courbe Precision-Recall et optimisation des seuils de blocage / alerte.
        6. **Deployment** : Déploiement de cette interface interactive Streamlit et export du modèle via `joblib`.
        """)

    with col_crisp2:
        st.markdown("""
        #### 📦 Caractéristiques Techniques
        - **Pipeline Machine Learning** : Pipeline Scikit-Learn encapsulant le feature engineering (`Amount_log`, `Heure_sin`, `Heure_cos`), le scaler et l'estimateur.
        - **Sécurité et Évitement du Data Leakage** : Tout le prétraitement et le scaling sont calculés uniquement sur le Train set.
        - **Interface Streamlit** : Remplacement moderne des interfaces desktop classiques (Tkinter) pour une utilisation web réactive.
        """)

st.divider()
st.caption("Financial Fraud Intelligence © 2026 - Développé pour le cours de Data Mining (ECE Paris)")
