"""Interface graphique pour tester le modèle de détection de fraude.

Lancement (depuis le dossier du projet) :
    python interface_tkinter.py
"""
import math
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from predicteur import COLONNES_V, ModeleFraude

try:  # texte net sur les écrans haute résolution (Windows)
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

C = {
    "fond": "#eef2f7", "carte": "#ffffff", "bordure": "#e2e8f0", "texte": "#0f172a", "doux": "#64748b",
    "pale": "#94a3b8", "entete": "#0f172a", "entete2": "#1e293b", "primaire": "#4f46e5", "primaire_survol": "#4338ca",
    "champ": "#f8fafc", "desactive": "#cbd5e1",
    "vert": "#16a34a", "vert_clair": "#dcfce7", "orange": "#d97706", "orange_clair": "#fef3c7",
    "rouge": "#dc2626", "rouge_clair": "#fee2e2", "gris_clair": "#f1f5f9",
}
COULEURS_DECISION = {
    "accepter": (C["vert"], C["vert_clair"]),
    "verifier": (C["orange"], C["orange_clair"]),
    "bloquer": (C["rouge"], C["rouge_clair"]),
}
POLICE = "Segoe UI"
POLICE_GRAS = "Segoe UI Semibold"


def nombre_fr(x, decimales=2):
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


class Bouton(tk.Label):
    """Bouton plat avec effet de survol."""

    def __init__(self, parent, texte, commande, fond, survol, couleur="white", taille=10, gras=True, padx=16, pady=8):
        super().__init__(parent, text=texte, bg=fond, fg=couleur, cursor="hand2", padx=padx, pady=pady,
                         font=(POLICE_GRAS if gras else POLICE, taille))
        self.fond, self.survol, self.couleur, self.commande, self.actif = fond, survol, couleur, commande, True
        self.bind("<Enter>", lambda e: self.actif and self.config(bg=self.survol))
        self.bind("<Leave>", lambda e: self.actif and self.config(bg=self.fond))
        self.bind("<Button-1>", lambda e: self.actif and self.commande())

    def activer(self, oui):
        self.actif = oui
        self.config(bg=self.fond if oui else C["desactive"], fg=self.couleur if oui else "white",
                    cursor="hand2" if oui else "arrow")


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.echelle = max(1.0, self.winfo_fpixels("1i") / 96)
        self.title("Fraud Intelligence — Détection de fraude bancaire")
        self.configure(bg=C["fond"])
        largeur, hauteur = min(self.px(1380), self.winfo_screenwidth() - 40), min(self.px(900), self.winfo_screenheight() - 80)
        self.geometry(f"{largeur}x{hauteur}+20+10")
        self.minsize(self.px(1100), self.px(700))

        self.modele = None
        self.file = queue.Queue()
        self.classe_reelle = None
        self.score_affiche = 0.0
        self.resultats_lot = None
        self.boutons_travail = []

        self._styles()
        self._entete()
        self._onglets()
        self._occupe(True)
        self.after(50, self._lire_file)
        self.executer(ModeleFraude, self._modele_pret, "Chargement du modèle…")

    # ================================================================ outils
    def px(self, n):
        return int(round(n * self.echelle))

    def executer(self, fonction, rappel, message=None):
        """Lance un calcul en arrière-plan pour que la fenêtre reste fluide."""
        if message:
            self.statut(message, "travail")

        def tache():
            try:
                self.file.put((rappel, fonction(), None))
            except Exception as erreur:  # affichée dans la fenêtre
                self.file.put((rappel, None, erreur))

        threading.Thread(target=tache, daemon=True).start()

    def _lire_file(self):
        try:
            while True:
                rappel, resultat, erreur = self.file.get_nowait()
                if erreur is not None:
                    self._occupe(False)
                    self.statut("Erreur", "erreur")
                    messagebox.showerror("Erreur", str(erreur), parent=self)
                else:
                    rappel(resultat)
        except queue.Empty:
            pass
        self.after(50, self._lire_file)

    def _occupe(self, oui):
        for b in self.boutons_travail:
            b.activer(not oui and self.modele is not None)

    def statut(self, texte, etat="ok"):
        couleurs = {"ok": ("#22c55e", "#052e16"), "travail": ("#f59e0b", "#2a1a03"), "erreur": ("#ef4444", "#2a0606")}
        point, fond = couleurs[etat]
        self.statut_point.config(fg=point, bg=fond)
        self.statut_texte.config(text=texte, bg=fond)
        self.statut_cadre.config(bg=fond)

    def carte(self, parent, titre=None, sous_titre=None):
        cadre = tk.Frame(parent, bg=C["carte"], highlightthickness=1, highlightbackground=C["bordure"])
        corps = tk.Frame(cadre, bg=C["carte"])
        corps.pack(fill="both", expand=True, padx=self.px(22), pady=self.px(14))
        if titre:
            tk.Label(corps, text=titre, bg=C["carte"], fg=C["texte"], font=(POLICE_GRAS, 14)).pack(anchor="w")
        if sous_titre:
            tk.Label(corps, text=sous_titre, bg=C["carte"], fg=C["doux"], font=(POLICE, 10), justify="left",
                     wraplength=self.px(640)).pack(anchor="w", pady=(self.px(2), 0))
        return cadre, corps

    def champ(self, parent, largeur=12):
        e = tk.Entry(parent, width=largeur, font=(POLICE, 10), bg=C["champ"], fg=C["texte"], relief="flat",
                     highlightthickness=1, highlightbackground=C["bordure"], highlightcolor=C["primaire"],
                     insertbackground=C["texte"])
        e.bind("<KeyRelease>", self._saisie_modifiee)
        return e

    # ================================================================ construction
    def _styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", font=(POLICE, 10))
        s.configure("TNotebook", background=C["fond"], borderwidth=0, tabmargins=(self.px(24), self.px(8), 0, 0))
        s.configure("TNotebook.Tab", font=(POLICE_GRAS, 11), padding=(self.px(20), self.px(9)), borderwidth=0,
                    background="#dde3ec", foreground=C["doux"], lightcolor=C["fond"], bordercolor=C["fond"])
        s.map("TNotebook.Tab", background=[("selected", C["carte"])], foreground=[("selected", C["primaire"])],
              expand=[("selected", (0, 0, 0, 0))], padding=[("selected", (self.px(20), self.px(9)))])
        s.configure("Lot.Treeview", font=(POLICE, 10), rowheight=self.px(30), background=C["carte"],
                    fieldbackground=C["carte"], borderwidth=0)
        s.configure("Lot.Treeview.Heading", font=(POLICE_GRAS, 10), background=C["gris_clair"],
                    foreground=C["doux"], relief="flat", padding=(self.px(8), self.px(6)))
        s.map("Lot.Treeview", background=[("selected", "#e0e7ff")], foreground=[("selected", C["texte"])])
        s.configure("Fin.Vertical.TScrollbar", background=C["bordure"], troughcolor=C["carte"], borderwidth=0,
                    arrowsize=self.px(12))

    def _entete(self):
        bandeau = tk.Frame(self, bg=C["entete"], height=self.px(70))
        bandeau.pack(fill="x")
        bandeau.pack_propagate(False)

        logo = tk.Canvas(bandeau, width=self.px(40), height=self.px(46), bg=C["entete"], highlightthickness=0)
        logo.pack(side="left", padx=(self.px(28), self.px(14)))
        w, h = self.px(40), self.px(46)
        bouclier = [w * .5, h * .04, w * .94, h * .2, w * .9, h * .58, w * .5, h * .96, w * .1, h * .58, w * .06, h * .2]
        logo.create_polygon(bouclier, fill=C["primaire"], outline="#818cf8", width=self.px(2), smooth=False)
        logo.create_line(w * .3, h * .5, w * .45, h * .65, w * .72, h * .36, fill="white", width=self.px(4),
                         capstyle="round", joinstyle="round")

        textes = tk.Frame(bandeau, bg=C["entete"])
        textes.pack(side="left")
        tk.Label(textes, text="Fraud Intelligence", bg=C["entete"], fg="white", font=(POLICE_GRAS, 17)).pack(anchor="w")
        tk.Label(textes, text="Détection de fraude bancaire — testez le modèle sur de vraies transactions",
                 bg=C["entete"], fg=C["pale"], font=(POLICE, 10)).pack(anchor="w")

        self.statut_cadre = tk.Frame(bandeau, bg="#2a1a03", padx=self.px(14), pady=self.px(6))
        self.statut_cadre.pack(side="right", padx=self.px(28))
        self.statut_point = tk.Label(self.statut_cadre, text="●", font=(POLICE, 11), bg="#2a1a03", fg="#f59e0b")
        self.statut_point.pack(side="left")
        self.statut_texte = tk.Label(self.statut_cadre, text="Démarrage…", font=(POLICE_GRAS, 10), fg="white",
                                     bg="#2a1a03")
        self.statut_texte.pack(side="left", padx=(self.px(6), 0))

        self.modele_texte = tk.Label(bandeau, text="", bg=C["entete"], fg=C["pale"], font=(POLICE, 10), justify="right")
        self.modele_texte.pack(side="right")

    def _onglets(self):
        onglets = ttk.Notebook(self)
        onglets.pack(fill="both", expand=True)
        self.onglet_unique = tk.Frame(onglets, bg=C["fond"])
        self.onglet_lot = tk.Frame(onglets, bg=C["fond"])
        self.onglet_modele = tk.Frame(onglets, bg=C["fond"])
        onglets.add(self.onglet_unique, text="  Analyser une transaction  ")
        onglets.add(self.onglet_lot, text="  Analyser un lot  ")
        onglets.add(self.onglet_modele, text="  Le modèle  ")
        self._construire_unique()
        self._construire_lot()

    # ---------------------------------------------------------------- onglet 1
    def _construire_unique(self):
        p = self.onglet_unique
        p.columnconfigure(0, weight=11, uniform="col")
        p.columnconfigure(1, weight=9, uniform="col")
        p.rowconfigure(0, weight=1)

        # ----- Formulaire
        cadre, corps = self.carte(p, "Transaction à analyser",
                                  "Chargez une vraie transaction de la période de test (le modèle ne l'a jamais vue) "
                                  "ou saisissez vos propres valeurs.")
        cadre.grid(row=0, column=0, sticky="nsew", padx=(self.px(24), self.px(10)), pady=self.px(14))

        exemples = tk.Frame(corps, bg=C["carte"])
        exemples.pack(fill="x", pady=(self.px(10), self.px(4)))
        for texte, cle, fond, survol, couleur in [
            ("Fraude réelle", "fraude", C["rouge_clair"], "#fecaca", C["rouge"]),
            ("Transaction normale", "normale", C["vert_clair"], "#bbf7d0", C["vert"]),
            ("Au hasard", "aleatoire", "#e0e7ff", "#c7d2fe", C["primaire"]),
        ]:
            b = Bouton(exemples, texte, lambda c=cle: self.charger_exemple(c), fond, survol, couleur, padx=14, pady=7)
            b.pack(side="left", padx=(0, self.px(8)))
            self.boutons_travail.append(b)
        Bouton(exemples, "Effacer", self.effacer, C["gris_clair"], C["bordure"], C["doux"], padx=14, pady=7).pack(side="left")

        self.source_texte = tk.Label(corps, text="", bg=C["carte"], fg=C["doux"], font=(POLICE, 9, "italic"), anchor="w")
        self.source_texte.pack(fill="x")

        principaux = tk.Frame(corps, bg=C["carte"])
        principaux.pack(fill="x", pady=(self.px(6), self.px(2)))
        tk.Label(principaux, text="Montant (€)", bg=C["carte"], fg=C["texte"], font=(POLICE_GRAS, 10)).grid(row=0, column=0, sticky="w")
        tk.Label(principaux, text="Time (secondes depuis le début de la collecte)", bg=C["carte"], fg=C["texte"],
                 font=(POLICE_GRAS, 10)).grid(row=0, column=1, sticky="w", padx=(self.px(18), 0))
        self.champ_montant = self.champ(principaux, 16)
        self.champ_montant.grid(row=1, column=0, sticky="we", ipady=self.px(5), pady=(self.px(4), 0))
        self.champ_time = self.champ(principaux, 16)
        self.champ_time.grid(row=1, column=1, sticky="w", ipady=self.px(5), pady=(self.px(4), 0), padx=(self.px(18), 0))
        self.heure_texte = tk.Label(principaux, text="", bg=C["carte"], fg=C["primaire"], font=(POLICE_GRAS, 10))
        self.heure_texte.grid(row=1, column=2, sticky="w", padx=(self.px(10), 0))
        self.champ_time.bind("<KeyRelease>", lambda e: (self._saisie_modifiee(e), self._maj_heure()), add="")

        tk.Frame(corps, bg=C["bordure"], height=1).pack(fill="x", pady=(self.px(10), self.px(6)))
        tk.Label(corps, text="Variables anonymisées V1 à V28", bg=C["carte"], fg=C["texte"],
                 font=(POLICE_GRAS, 10)).pack(anchor="w")
        tk.Label(corps, text="Issues d'une ACP par la banque pour protéger les clients : elles n'ont pas de sens lisible.",
                 bg=C["carte"], fg=C["doux"], font=(POLICE, 9)).pack(anchor="w")

        grille = tk.Frame(corps, bg=C["carte"])
        grille.pack(fill="x", pady=(self.px(4), 0))
        self.champs_v = {}
        for i, nom in enumerate(COLONNES_V):
            ligne, col = i % 7, i // 7
            grille.columnconfigure(col * 2 + 1, weight=1)
            tk.Label(grille, text=nom, bg=C["carte"], fg=C["doux"], font=(POLICE_GRAS, 9), width=4,
                     anchor="e").grid(row=ligne, column=col * 2, padx=(self.px(6), self.px(6)), pady=self.px(2))
            e = self.champ(grille, 9)
            e.grid(row=ligne, column=col * 2 + 1, sticky="we", ipady=self.px(2), pady=self.px(2))
            self.champs_v[nom] = e

        self.bouton_analyser = Bouton(corps, "Analyser la transaction", self.analyser, C["primaire"],
                                      C["primaire_survol"], taille=12, pady=9)
        self.bouton_analyser.pack(fill="x", pady=(self.px(12), 0))
        self.boutons_travail.append(self.bouton_analyser)

        # ----- Résultat
        cadre, corps = self.carte(p, "Résultat")
        cadre.grid(row=0, column=1, sticky="nsew", padx=(self.px(10), self.px(24)), pady=self.px(14))
        self.jauge = tk.Canvas(corps, width=self.px(380), height=self.px(185), bg=C["carte"], highlightthickness=0)
        self.jauge.pack()
        self.badge = tk.Label(corps, text="En attente", font=(POLICE_GRAS, 15), bg=C["gris_clair"], fg=C["doux"],
                              padx=self.px(22), pady=self.px(5))
        self.badge.pack()
        self.detail = tk.Label(corps, text="Chargez un exemple, puis cliquez sur « Analyser ».", bg=C["carte"],
                               fg=C["doux"], font=(POLICE, 10), wraplength=self.px(440))
        self.detail.pack(pady=(self.px(4), 0))
        self.realite = tk.Label(corps, text="", bg=C["carte"], font=(POLICE_GRAS, 10), padx=self.px(12),
                                pady=self.px(4))
        self.realite.pack(pady=(self.px(6), 0))

        tk.Frame(corps, bg=C["bordure"], height=1).pack(fill="x", pady=(self.px(8), self.px(6)))
        tk.Label(corps, text="Pourquoi ce score ?", bg=C["carte"], fg=C["texte"], font=(POLICE_GRAS, 12)).pack(anchor="w")
        self.explication_texte = tk.Label(corps, text="Contribution de chaque variable au score (valeurs SHAP).",
                                          bg=C["carte"], fg=C["doux"], font=(POLICE, 9), justify="left")
        self.explication_texte.pack(anchor="w")
        self.explication = tk.Canvas(corps, height=self.px(190), bg=C["carte"], highlightthickness=0)
        self.explication.pack(fill="both", expand=True, pady=(self.px(4), 0))
        self.explication.bind("<Configure>", lambda e: self._dessiner_explication(getattr(self, "_derniere_expl", None)))
        self._dessiner_jauge(0, vide=True)

    # ---------------------------------------------------------------- onglet 2
    def _construire_lot(self):
        p = self.onglet_lot
        cadre, corps = self.carte(p, "Analyser un lot de transactions",
                                  "Rejouez toute la période de test (les 20 % de transactions les plus récentes) ou "
                                  "ouvrez votre propre fichier CSV avec les colonnes Time, V1 à V28 et Amount "
                                  "(et Class si vous connaissez la réalité).")
        cadre.pack(fill="both", expand=True, padx=self.px(24), pady=self.px(14))

        barre = tk.Frame(corps, bg=C["carte"])
        barre.pack(fill="x", pady=(self.px(14), self.px(12)))
        b1 = Bouton(barre, "Rejouer la période de test", self.rejouer_test, C["primaire"], C["primaire_survol"])
        b2 = Bouton(barre, "Ouvrir un fichier CSV…", self.ouvrir_csv, "#e0e7ff", "#c7d2fe", C["primaire"])
        self.bouton_export = Bouton(barre, "Exporter les résultats…", self.exporter, C["gris_clair"], C["bordure"], C["texte"])
        for b in (b1, b2, self.bouton_export):
            b.pack(side="left", padx=(0, self.px(8)))
        self.boutons_travail += [b1, b2]
        self.bouton_export.activer(False)
        self.lot_source = tk.Label(barre, text="", bg=C["carte"], fg=C["doux"], font=(POLICE, 9, "italic"))
        self.lot_source.pack(side="left", padx=self.px(8))

        self.tuiles = tk.Frame(corps, bg=C["carte"])
        self.tuiles.pack(fill="x", pady=(0, self.px(12)))

        tk.Label(corps, text="Les 300 transactions les plus suspectes", bg=C["carte"], fg=C["texte"],
                 font=(POLICE_GRAS, 11)).pack(anchor="w", pady=(0, self.px(6)))
        zone = tk.Frame(corps, bg=C["carte"], highlightthickness=1, highlightbackground=C["bordure"])
        zone.pack(fill="both", expand=True)
        colonnes = ("rang", "heure", "montant", "score", "decision", "realite")
        self.tableau = ttk.Treeview(zone, columns=colonnes, show="headings", style="Lot.Treeview")
        for col, titre, largeur, ancre in [("rang", "#", 60, "center"), ("heure", "Heure", 110, "center"),
                                           ("montant", "Montant", 140, "e"), ("score", "Score de fraude", 150, "center"),
                                           ("decision", "Décision", 150, "center"), ("realite", "Réalité", 180, "center")]:
            self.tableau.heading(col, text=titre)
            self.tableau.column(col, width=self.px(largeur), anchor=ancre)
        for cle, (fort, clair) in COULEURS_DECISION.items():
            self.tableau.tag_configure(cle, background=clair, foreground=C["texte"])
        defil = ttk.Scrollbar(zone, orient="vertical", command=self.tableau.yview, style="Fin.Vertical.TScrollbar")
        self.tableau.configure(yscrollcommand=defil.set)
        self.tableau.pack(side="left", fill="both", expand=True)
        defil.pack(side="right", fill="y")

    # ---------------------------------------------------------------- onglet 3
    def _construire_modele(self):
        p = self.onglet_modele
        infos = self.modele.infos
        m, ic = infos["metriques_test"], infos.get("intervalles_confiance_95", {})
        p.columnconfigure((0, 1), weight=1, uniform="m")

        cadre, corps = self.carte(p, "Le modèle exporté", "Fichier models/fraud_detection_model.joblib, créé par le notebook.")
        cadre.grid(row=0, column=0, sticky="nsew", padx=(self.px(24), self.px(10)), pady=self.px(20))
        h = infos["hyperparametres"]
        lignes = [
            ("Algorithme", infos["nom_modele"]),
            ("Gestion du déséquilibre", infos["strategie_desequilibre"]),
            ("Nombre d'arbres", h.get("model__n_estimators", "—")),
            ("Profondeur maximale", h.get("model__max_depth", "—")),
            ("Seuil d'alerte (vérifier)", nombre_fr(infos["seuil_alerte"], 3)),
            ("Seuil de blocage", nombre_fr(infos["seuil_blocage"], 3)),
            ("Période d'entraînement", f"{nombre_fr(infos['periode_entrainement_heures'][0], 0)} h à "
                                       f"{nombre_fr(infos['periode_entrainement_heures'][1], 1)} h"),
            ("Coût d'une vérification", f"{nombre_fr(infos['hypotheses']['cout_verification_eur'], 0)} €"),
            ("Capacité de vérification", f"{infos['hypotheses']['capacite_alertes_jour']} alertes / jour"),
            ("Date d'export", str(infos["date"]).replace("T", " à ")),
        ]
        self._tableau_cles(corps, lignes)

        cadre, corps = self.carte(p, "Résultats sur la période de test",
                                  "74 fraudes jamais vues, sur les 7,7 dernières heures du dataset.")
        cadre.grid(row=0, column=1, sticky="nsew", padx=(self.px(10), self.px(24)), pady=self.px(20))

        def avec_ic(nom):
            valeur = f"{nombre_fr(m[nom] * 100, 1)} %"
            if nom in ic:
                valeur += f"   (IC 95 % : {nombre_fr(ic[nom][0] * 100, 0)} – {nombre_fr(ic[nom][1] * 100, 0)} %)"
            return valeur

        lignes = [
            ("Fraudes détectées", f"{int(m['TP'])} sur {int(m['TP'] + m['FN'])}"),
            ("Recall", avec_ic("Recall")),
            ("Precision", avec_ic("Precision")),
            ("Fausses alertes", f"{int(m['FP'])} sur {nombre_fr(m['FP'] + m['TN'], 0)} transactions normales"),
            ("PR-AUC", nombre_fr(m["PR-AUC"], 3)),
            ("ROC-AUC", nombre_fr(m["ROC-AUC"], 3)),
            ("Alertes par jour", nombre_fr(m["Alertes / jour"], 0)),
            ("Coût total (pertes + vérifications)", f"{nombre_fr(m['Coût total (€)'], 0)} €"),
        ]
        self._tableau_cles(corps, lignes)

    def _tableau_cles(self, parent, lignes):
        grille = tk.Frame(parent, bg=C["carte"])
        grille.pack(fill="x", pady=(self.px(14), 0))
        grille.columnconfigure(1, weight=1)
        for i, (cle, valeur) in enumerate(lignes):
            fond = C["gris_clair"] if i % 2 == 0 else C["carte"]
            tk.Label(grille, text=cle, bg=fond, fg=C["doux"], font=(POLICE, 10), anchor="w", padx=self.px(12),
                     pady=self.px(8)).grid(row=i, column=0, sticky="we")
            tk.Label(grille, text=str(valeur), bg=fond, fg=C["texte"], font=(POLICE_GRAS, 10), anchor="w",
                     padx=self.px(12), pady=self.px(8)).grid(row=i, column=1, sticky="we")

    # ================================================================ actions
    def _modele_pret(self, modele):
        self.modele = modele
        self.modele_texte.config(text=f"{modele.infos['nom_modele']} · {modele.infos['strategie_desequilibre']}\n"
                                      f"alerte ≥ {nombre_fr(modele.seuil_alerte, 3)} · "
                                      f"blocage ≥ {nombre_fr(modele.seuil_blocage, 3)}")
        self._construire_modele()
        self._dessiner_jauge(0, vide=True)
        self._occupe(False)
        self.statut("Modèle prêt")

    def _saisie_modifiee(self, _evenement=None):
        if self.classe_reelle is not None:
            self.classe_reelle = None
            self.source_texte.config(text="Valeurs modifiées à la main : la réalité n'est plus connue.")

    def _maj_heure(self):
        try:
            t = float(self.champ_time.get().replace(",", ".").replace(" ", ""))
            heure = (t % 86400) / 3600
            self.heure_texte.config(text=f"→ {int(heure):02d} h {int(heure % 1 * 60):02d}  (jour {int(t // 86400) + 1})")
        except ValueError:
            self.heure_texte.config(text="")

    def charger_exemple(self, type_exemple):
        self._occupe(True)
        message = "Chargement des transactions…" if self.modele._test is None else "Tirage d'une transaction…"
        self.executer(lambda: self.modele.exemple(type_exemple), self._remplir, message)

    def _remplir(self, resultat):
        transaction, classe = resultat
        self._vider_champs()
        self.champ_montant.insert(0, f"{transaction['Amount']:.2f}")
        self.champ_time.insert(0, f"{transaction['Time']:.0f}")
        for nom, e in self.champs_v.items():
            e.insert(0, f"{transaction[nom]:.6f}")
        self._maj_heure()
        self.classe_reelle = classe
        self.source_texte.config(text="Vraie transaction de la période de test. La réalité s'affichera après l'analyse.")
        self._reinitialiser_resultat()
        self._occupe(False)
        self.statut("Modèle prêt")

    def _vider_champs(self):
        for e in [self.champ_montant, self.champ_time, *self.champs_v.values()]:
            e.delete(0, "end")

    def effacer(self):
        self._vider_champs()
        self.classe_reelle = None
        self.source_texte.config(text="")
        self.heure_texte.config(text="")
        self._reinitialiser_resultat()

    def _lire_formulaire(self):
        def lire(e, nom):
            texte = e.get().strip().replace(",", ".").replace(" ", "")
            if not texte:
                raise ValueError(f"Le champ {nom} est vide. Remplissez tous les champs ou chargez un exemple.")
            try:
                return float(texte)
            except ValueError:
                raise ValueError(f"Le champ {nom} doit être un nombre (valeur saisie : « {e.get()} »).") from None

        transaction = {"Time": lire(self.champ_time, "Time"), "Amount": lire(self.champ_montant, "Montant")}
        transaction.update({nom: lire(e, nom) for nom, e in self.champs_v.items()})
        return transaction

    def analyser(self):
        try:
            transaction = self._lire_formulaire()
            self.modele.preparer(transaction)
        except ValueError as erreur:
            messagebox.showwarning("Saisie incomplète", str(erreur), parent=self)
            return
        self._occupe(True)
        classe = self.classe_reelle
        self.executer(lambda: (self.modele.predire(transaction), self.modele.expliquer(transaction), classe),
                      self._afficher_resultat, "Analyse en cours…")

    def _reinitialiser_resultat(self):
        self._animer_jauge(0, vide=True)
        self.badge.config(text="En attente", bg=C["gris_clair"], fg=C["doux"])
        self.detail.config(text="Cliquez sur « Analyser la transaction ».")
        self.realite.config(text="", bg=C["carte"])
        self._derniere_expl = None
        self._dessiner_explication(None)

    def _afficher_resultat(self, resultat):
        prediction, explication, classe = resultat
        fort, clair = COULEURS_DECISION[prediction["decision"]]
        self._animer_jauge(prediction["score"])
        self.badge.config(text=prediction["libelle"].upper(), bg=clair, fg=fort)
        self.detail.config(text=prediction["detail"])
        if classe is None:
            self.realite.config(text="Réalité inconnue (valeurs saisies à la main)", bg=C["gris_clair"], fg=C["doux"])
        else:
            alerte = prediction["decision"] != "accepter"
            juste = alerte == bool(classe)
            reel = "FRAUDE" if classe else "transaction NORMALE"
            if juste:
                texte = f"✓  Bonne réponse — en réalité : {reel}"
            elif classe:
                texte = f"✗  Fraude ratée — en réalité : {reel}"
            else:
                texte = f"✗  Fausse alerte — en réalité : {reel}"
            self.realite.config(text=texte, bg=C["vert_clair"] if juste else C["rouge_clair"],
                                fg=C["vert"] if juste else C["rouge"])
        self._derniere_expl = explication
        self._dessiner_explication(explication)
        self._occupe(False)
        self.statut("Modèle prêt")

    # ---------------------------------------------------------------- lot
    def rejouer_test(self):
        self._occupe(True)

        def calcul():
            test = self.modele.donnees_test()
            return self.modele.predire_lot(test), "Période de test : 7,7 dernières heures du dataset"

        self.executer(calcul, self._afficher_lot, "Analyse de la période de test…")

    def ouvrir_csv(self):
        chemin = filedialog.askopenfilename(parent=self, title="Choisir un fichier de transactions",
                                            filetypes=[("Fichiers CSV", "*.csv"), ("Tous les fichiers", "*.*")])
        if not chemin:
            return
        self._occupe(True)
        self.executer(lambda: (self.modele.predire_lot(pd.read_csv(chemin)), chemin), self._afficher_lot,
                      "Analyse du fichier…")

    def _afficher_lot(self, resultat):
        df, source = resultat
        self.resultats_lot = df
        self.lot_source.config(text=source)
        for w in self.tuiles.winfo_children():
            w.destroy()

        comptes = df["decision"].value_counts()
        tuiles = [("Transactions", nombre_fr(len(df), 0), C["texte"]),
                  ("Acceptées", nombre_fr(comptes.get("Accepter", 0), 0), C["vert"]),
                  ("À vérifier", nombre_fr(comptes.get("Vérifier", 0), 0), C["orange"]),
                  ("Bloquées", nombre_fr(comptes.get("Bloquer", 0), 0), C["rouge"])]
        if "Class" in df.columns:
            alerte = df["decision"] != "Accepter"
            fraudes = int(df["Class"].sum())
            tp = int((alerte & (df["Class"] == 1)).sum())
            fp = int((alerte & (df["Class"] == 0)).sum())
            tuiles += [("Fraudes détectées", f"{tp} / {fraudes}", C["primaire"]),
                       ("Recall", f"{nombre_fr(tp / fraudes * 100, 1)} %" if fraudes else "—", C["primaire"]),
                       ("Fausses alertes", nombre_fr(fp, 0), C["doux"])]
        for i, (titre, valeur, couleur) in enumerate(tuiles):
            t = tk.Frame(self.tuiles, bg=C["gris_clair"], padx=self.px(16), pady=self.px(10))
            t.grid(row=0, column=i, sticky="we", padx=(0, self.px(10)))
            self.tuiles.columnconfigure(i, weight=1)
            tk.Label(t, text=titre, bg=C["gris_clair"], fg=C["doux"], font=(POLICE, 9)).pack(anchor="w")
            tk.Label(t, text=valeur, bg=C["gris_clair"], fg=couleur, font=(POLICE_GRAS, 18)).pack(anchor="w")

        self.tableau.delete(*self.tableau.get_children())
        cle_decision = {"Accepter": "accepter", "Vérifier": "verifier", "Bloquer": "bloquer"}
        for rang, (_, ligne) in enumerate(df.sort_values("score_fraude", ascending=False).head(300).iterrows(), 1):
            heure = (ligne["Time"] % 86400) / 3600
            realite = ("Fraude" if ligne["Class"] == 1 else "Normale") if "Class" in df.columns else "—"
            self.tableau.insert("", "end", tags=(cle_decision[ligne["decision"]],), values=(
                rang, f"{int(heure):02d} h {int(heure % 1 * 60):02d}", f"{nombre_fr(ligne['Amount'])} €",
                nombre_fr(ligne["score_fraude"], 3), ligne["decision"], realite))
        self.bouton_export.activer(True)
        self._occupe(False)
        self.statut("Modèle prêt")

    def exporter(self):
        if self.resultats_lot is None:
            return
        chemin = filedialog.asksaveasfilename(parent=self, defaultextension=".csv", initialfile="resultats_fraude.csv",
                                              filetypes=[("Fichiers CSV", "*.csv")])
        if chemin:
            self.resultats_lot.to_csv(chemin, index=False)
            messagebox.showinfo("Export terminé", f"{len(self.resultats_lot):,} lignes enregistrées dans\n{chemin}",
                                parent=self)

    # ================================================================ dessins
    def _animer_jauge(self, cible, vide=False):
        depart = self.score_affiche
        etapes = 24

        def etape(i):
            t = i / etapes
            t = 1 - (1 - t) ** 3  # ralentit à la fin
            self._dessiner_jauge(depart + (cible - depart) * t, vide=vide and i == etapes)
            if i < etapes:
                self.after(16, etape, i + 1)
            else:
                self.score_affiche = cible

        etape(1)

    def _dessiner_jauge(self, score, vide=False):
        cv = self.jauge
        cv.delete("all")
        w, h = self.px(380), self.px(185)
        cx, cy, r, ep = w / 2, h - self.px(34), self.px(132), self.px(22)
        sa = self.modele.seuil_alerte if self.modele else 0.233
        sb = self.modele.seuil_blocage if self.modele else 0.614
        boite = (cx - r, cy - r, cx + r, cy + r)
        for debut, fin, couleur in [(0, sa, "#86efac"), (sa, sb, "#fcd34d"), (sb, 1, "#fca5a5")]:
            cv.create_arc(boite, start=180 - 180 * debut, extent=-180 * (fin - debut), style="arc",
                          outline=couleur, width=ep)
        if not vide:  # partie « remplie » jusqu'au score
            couleur = C["vert"] if score < sa else C["orange"] if score < sb else C["rouge"]
            if score > 0.002:
                cv.create_arc(boite, start=180, extent=-180 * min(score, 0.999), style="arc", outline=couleur,
                              width=self.px(8))
        for s in (sa, sb):  # graduations des seuils
            a = math.radians(180 - 180 * s)
            x1, y1 = cx + (r + ep / 2 + self.px(3)) * math.cos(a), cy - (r + ep / 2 + self.px(3)) * math.sin(a)
            x2, y2 = cx + (r - ep / 2 - self.px(3)) * math.cos(a), cy - (r - ep / 2 - self.px(3)) * math.sin(a)
            cv.create_line(x1, y1, x2, y2, fill=C["texte"], width=self.px(2))
            xt, yt = cx + (r + ep / 2 + self.px(16)) * math.cos(a), cy - (r + ep / 2 + self.px(16)) * math.sin(a)
            cv.create_text(xt, yt, text=nombre_fr(s, 2), fill=C["doux"], font=(POLICE, 8))
        cv.create_text(cx - r, cy + self.px(20), text="0", fill=C["pale"], font=(POLICE, 9))
        cv.create_text(cx + r, cy + self.px(20), text="1", fill=C["pale"], font=(POLICE, 9))
        if vide:
            cv.create_text(cx, cy - self.px(30), text="—", fill=C["pale"], font=(POLICE_GRAS, 34))
            cv.create_text(cx, cy + self.px(4), text="score de fraude", fill=C["pale"], font=(POLICE, 10))
            return
        a = math.radians(180 - 180 * score)  # aiguille
        lg = r - ep / 2 - self.px(14)
        cv.create_line(cx, cy, cx + lg * math.cos(a), cy - lg * math.sin(a), fill=C["texte"], width=self.px(3),
                       capstyle="round")
        cv.create_oval(cx - self.px(7), cy - self.px(7), cx + self.px(7), cy + self.px(7), fill=C["texte"], outline="")
        couleur = C["vert"] if score < sa else C["orange"] if score < sb else C["rouge"]
        cv.create_text(cx, cy - self.px(46), text=f"{nombre_fr(score * 100, 1)} %", fill=couleur,
                       font=(POLICE_GRAS, 24))
        cv.create_text(cx, cy + self.px(20), text="score de fraude", fill=C["doux"], font=(POLICE, 10))

    def _dessiner_explication(self, explication):
        cv = self.explication
        cv.delete("all")
        w = max(cv.winfo_width(), self.px(300))
        if explication is None:
            if self.modele is not None and getattr(self, "_derniere_expl", None) is None:
                cv.create_text(w / 2, self.px(60), text="Les variables qui ont le plus pesé\ns'afficheront ici.",
                               fill=C["pale"], font=(POLICE, 10), justify="center")
            return
        contributions = explication["contributions"][:6]
        maxi = max(max(abs(c["contribution"]) for c in contributions), 0.05)  # petites contributions = petites barres
        col_nom, col_val = self.px(130), self.px(60)
        centre = col_nom + (w - col_nom - col_val) / 2
        demi = (w - col_nom - col_val) / 2 - self.px(6)
        hauteur = self.px(25)
        cv.create_line(centre, 0, centre, hauteur * len(contributions), fill=C["bordure"], width=self.px(2))
        for i, c in enumerate(contributions):
            y = i * hauteur + hauteur / 2
            valeur = nombre_fr(c["valeur"], 2) + (" €" if c["variable"] == "Montant" else "")
            cv.create_text(col_nom - self.px(8), y, text=f"{c['variable']} = {valeur}", anchor="e",
                           fill=C["texte"], font=(POLICE, 9))
            longueur = demi * abs(c["contribution"]) / maxi
            positif = c["contribution"] > 0
            couleur = "#ef4444" if positif else "#22c55e"
            x0, x1 = (centre, centre + longueur) if positif else (centre - longueur, centre)
            cv.create_rectangle(x0, y - hauteur * .32, max(x1, x0 + 1), y + hauteur * .32, fill=couleur, outline="")
            signe = "+" if positif else "−"
            cv.create_text(w - self.px(4), y, text=f"{signe}{nombre_fr(abs(c['contribution']), 3)}", anchor="e",
                           fill="#b91c1c" if positif else "#15803d", font=(POLICE_GRAS, 9))
        y = hauteur * len(contributions) + self.px(14)
        cv.create_text(centre - self.px(8), y, text="← vers « normale »", anchor="e", fill="#15803d", font=(POLICE, 9))
        cv.create_text(centre + self.px(8), y, text="vers « fraude » →", anchor="w", fill="#b91c1c", font=(POLICE, 9))
        self.explication_texte.config(
            text=f"Score moyen de départ : {nombre_fr(explication['base'], 3)}. Chaque variable l'augmente (rouge) "
                 f"ou le diminue (vert).")


if __name__ == "__main__":
    Application().mainloop()
