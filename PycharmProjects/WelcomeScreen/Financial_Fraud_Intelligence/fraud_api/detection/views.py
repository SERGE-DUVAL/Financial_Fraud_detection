"""Page de test et API JSON du modèle de détection de fraude."""
import json

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from predicteur import COLONNES_V

from .services import modele

TYPES_EXEMPLE = {"fraude", "normale", "aleatoire"}


def erreur(message, statut=400):
    return JsonResponse({"erreur": message}, status=statut)


@require_GET
def index(request):
    return render(request, "detection/index.html", {"colonnes_v": COLONNES_V})


@require_GET
def api_modele(request):
    """Fiche du modèle : algorithme, seuils, résultats sur la période de test."""
    return JsonResponse(modele().infos)


@require_GET
def api_exemple(request):
    """Une vraie transaction de la période de test (?type=fraude|normale|aleatoire)."""
    type_exemple = request.GET.get("type", "aleatoire")
    if type_exemple not in TYPES_EXEMPLE:
        return erreur(f"type doit être l'une de ces valeurs : {', '.join(sorted(TYPES_EXEMPLE))}")
    transaction, classe = modele().exemple(type_exemple)
    return JsonResponse({"transaction": transaction, "classe_reelle": classe})


@csrf_exempt  # API JSON sans session : pas de jeton CSRF
@require_POST
def api_predire(request):
    """Prédit une transaction envoyée en JSON : {"Time": ..., "V1": ..., ..., "V28": ..., "Amount": ...}."""
    try:
        transaction = json.loads(request.body or b"")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return erreur("Le corps de la requête doit être du JSON valide.")
    if not isinstance(transaction, dict):
        return erreur("Envoyez un objet JSON décrivant une seule transaction.")
    m = modele()
    try:
        resultat = m.predire(transaction)
    except ValueError as e:
        return erreur(str(e))
    resultat["explication"] = m.expliquer(transaction) if request.GET.get("expliquer", "1") != "0" else None
    return JsonResponse(resultat)


@csrf_exempt
@require_POST
def api_lot(request):
    """Analyse un fichier CSV (champ « fichier ») ou toute la période de test (source=test)."""
    m = modele()
    if "fichier" in request.FILES:
        fichier = request.FILES["fichier"]
        try:
            df = pd.read_csv(fichier)
        except Exception:
            return erreur("Impossible de lire ce fichier : envoyez un CSV avec les colonnes Time, V1 à V28 et Amount.")
        source = fichier.name
    elif request.POST.get("source") == "test":
        df, source = m.donnees_test(), "Période de test (7,7 dernières heures du dataset)"
    else:
        return erreur("Envoyez un fichier CSV (champ « fichier ») ou source=test.")
    if df.empty:
        return erreur("Le fichier ne contient aucune transaction.")
    try:
        resultats = m.predire_lot(df)
    except ValueError as e:
        return erreur(str(e))

    comptes = resultats["decision"].value_counts()
    resume = {"transactions": len(resultats),
              "accepter": int(comptes.get("Accepter", 0)),
              "verifier": int(comptes.get("Vérifier", 0)),
              "bloquer": int(comptes.get("Bloquer", 0))}
    if "Class" in resultats.columns:
        alerte = resultats["decision"] != "Accepter"
        fraude = pd.to_numeric(resultats["Class"], errors="coerce") == 1
        resume.update({"fraudes": int(fraude.sum()), "fraudes_detectees": int((alerte & fraude).sum()),
                       "fausses_alertes": int((alerte & ~fraude).sum())})

    top = resultats.sort_values("score_fraude", ascending=False).head(100)
    lignes = [{"time": float(r["Time"]), "montant": float(r["Amount"]), "score": float(r["score_fraude"]),
               "decision": r["decision"],
               "realite": (("Fraude" if r["Class"] == 1 else "Normale") if "Class" in top.columns else None)}
              for _, r in top.iterrows()]
    return JsonResponse({"source": source, "resume": resume, "lignes": lignes})
