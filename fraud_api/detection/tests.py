"""Tests du site : python manage.py test"""
import io
import json

from django.test import SimpleTestCase

from .services import modele


class TestsDetection(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fraude, _ = modele().exemple("fraude", graine=3)
        cls.normale, _ = modele().exemple("normale", graine=3)

    def predire(self, donnees, brut=False):
        corps = donnees if brut else json.dumps(donnees)
        return self.client.post("/api/predire/", corps, content_type="application/json")

    def test_page_accueil(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Analyser la transaction")
        self.assertContains(r, 'name="V28"')

    def test_fiche_modele(self):
        infos = self.client.get("/api/modele/").json()
        self.assertEqual(infos["nom_modele"], "Random Forest")
        self.assertLess(infos["seuil_alerte"], infos["seuil_blocage"])
        self.assertNotIn("pipeline", infos)

    def test_exemple_fraude_et_normale(self):
        self.assertEqual(self.client.get("/api/exemple/?type=fraude").json()["classe_reelle"], 1)
        self.assertEqual(self.client.get("/api/exemple/?type=normale").json()["classe_reelle"], 0)
        self.assertEqual(self.client.get("/api/exemple/?type=nimporte").status_code, 400)

    def test_prediction_complete(self):
        r = self.predire(self.fraude)
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertTrue(0 <= d["score"] <= 1)
        self.assertIn(d["decision"], {"accepter", "verifier", "bloquer"})
        self.assertEqual(len(d["explication"]["contributions"]), 8)

    def test_meme_score_que_le_modele(self):
        attendu = modele().predire(self.normale)["score"]
        self.assertAlmostEqual(self.predire(self.normale).json()["score"], attendu, places=9)

    def test_decision_coherente_avec_les_seuils(self):
        d = self.predire(self.fraude).json()
        attendu = ("bloquer" if d["score"] >= d["seuil_blocage"]
                   else "verifier" if d["score"] >= d["seuil_alerte"] else "accepter")
        self.assertEqual(d["decision"], attendu)

    def test_sans_explication(self):
        r = self.client.post("/api/predire/?expliquer=0", json.dumps(self.normale), content_type="application/json")
        self.assertIsNone(r.json()["explication"])

    def test_colonne_manquante(self):
        incomplete = {k: v for k, v in self.fraude.items() if k != "V14"}
        r = self.predire(incomplete)
        self.assertEqual(r.status_code, 400)
        self.assertIn("V14", r.json()["erreur"])

    def test_valeur_non_numerique(self):
        r = self.predire({**self.fraude, "V3": "abc"})
        self.assertEqual(r.status_code, 400)

    def test_montant_negatif(self):
        self.assertEqual(self.predire({**self.fraude, "Amount": -5}).status_code, 400)

    def test_json_invalide(self):
        self.assertEqual(self.predire("{pas du json", brut=True).status_code, 400)
        self.assertEqual(self.predire([1, 2, 3]).status_code, 400)

    def test_get_interdit_sur_predire(self):
        self.assertEqual(self.client.get("/api/predire/").status_code, 405)

    def test_lot_periode_de_test(self):
        d = self.client.post("/api/lot/", {"source": "test"}).json()
        # mêmes résultats que dans le notebook (phase 5)
        self.assertEqual(d["resume"]["transactions"], 56746)
        self.assertEqual(d["resume"]["fraudes"], 74)
        self.assertEqual(d["resume"]["fraudes_detectees"], 59)
        self.assertEqual(d["resume"]["fausses_alertes"], 52)
        self.assertEqual(len(d["lignes"]), 100)

    def test_lot_fichier_csv(self):
        lignes = modele().donnees_test().head(50)
        fichier = io.BytesIO(lignes.to_csv(index=False).encode())
        fichier.name = "transactions.csv"
        d = self.client.post("/api/lot/", {"fichier": fichier}).json()
        self.assertEqual(d["resume"]["transactions"], 50)
        self.assertEqual(d["source"], "transactions.csv")

    def test_lot_fichier_invalide(self):
        fichier = io.BytesIO(b"a,b\n1,2\n")
        fichier.name = "mauvais.csv"
        r = self.client.post("/api/lot/", {"fichier": fichier})
        self.assertEqual(r.status_code, 400)
        self.assertIn("Colonnes manquantes", r.json()["erreur"])
