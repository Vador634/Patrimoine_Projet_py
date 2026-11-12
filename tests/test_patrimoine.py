"""Tests de la couche d'accès aux données (sans interface graphique).

Lancement : python -m unittest discover -s tests
"""
import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import Patrimoine as p  # noqa: E402


class TestPatrimoine(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.db = Path(self.dossier.name) / "test.db"
        p.init_db(self.db)

    def tearDown(self):
        # Échoue sous Windows si une connexion était restée ouverte
        self.dossier.cleanup()

    def test_ajout_et_lecture(self):
        id_m = p.ajouter_materiel("  Poste-01  ", "PC", "Neuf", chemin=self.db)
        lignes = p.charger_inventaire(chemin=self.db)
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes[0][:4], (id_m, "Poste-01", "PC", "Neuf"))

    def test_validation(self):
        with self.assertRaises(ValueError):
            p.ajouter_materiel("   ", "PC", "Neuf", chemin=self.db)
        with self.assertRaises(ValueError):
            p.ajouter_materiel("Poste", "Grille-pain", "Neuf", chemin=self.db)
        with self.assertRaises(ValueError):
            p.ajouter_materiel("x" * 101, "PC", "Neuf", chemin=self.db)

    def test_modification(self):
        id_m = p.ajouter_materiel("Borne Wi-Fi", "Réseau", "Neuf", chemin=self.db)
        self.assertTrue(p.modifier_materiel(id_m, "Borne Wi-Fi 6", "Réseau", "Maintenance", chemin=self.db))
        self.assertEqual(p.charger_inventaire(chemin=self.db)[0][1:4], ("Borne Wi-Fi 6", "Réseau", "Maintenance"))
        self.assertFalse(p.modifier_materiel(9999, "X", "PC", "Neuf", chemin=self.db))

    def test_suppression_multiple(self):
        ids = [p.ajouter_materiel(f"Poste-{i}", "PC", "Neuf", chemin=self.db) for i in range(3)]
        self.assertEqual(p.supprimer_materiels(ids[:2], chemin=self.db), 2)
        self.assertEqual([l[0] for l in p.charger_inventaire(chemin=self.db)], [ids[2]])

    def test_recherche_et_filtre(self):
        p.ajouter_materiel("Tablette accueil", "Tablette", "Utilisé", chemin=self.db)
        p.ajouter_materiel("Poste compta", "PC", "Neuf", chemin=self.db)
        p.ajouter_materiel("Poste 100% neuf", "PC", "Neuf", chemin=self.db)
        self.assertEqual(len(p.charger_inventaire("poste", chemin=self.db)), 2)
        self.assertEqual(len(p.charger_inventaire(categorie="Tablette", chemin=self.db)), 1)
        # "%" saisi par l'utilisateur est cherché littéralement, pas comme joker
        self.assertEqual([l[1] for l in p.charger_inventaire("100%", chemin=self.db)], ["Poste 100% neuf"])
        self.assertEqual(p.charger_inventaire("_", chemin=self.db), [])

    def test_injection_sql_sans_effet(self):
        p.ajouter_materiel("Poste", "PC", "Neuf", chemin=self.db)
        p.charger_inventaire("'; DROP TABLE materiel; --", chemin=self.db)
        self.assertEqual(len(p.charger_inventaire(chemin=self.db)), 1)

    def test_export_csv_excel(self):
        p.ajouter_materiel("Imprimante étage", "Imprimante", "Hors service", chemin=self.db)
        fichier = Path(self.dossier.name) / "export.csv"
        self.assertEqual(p.exporter_csv(p.charger_inventaire(chemin=self.db), fichier), 1)
        contenu = fichier.read_bytes()
        self.assertTrue(contenu.startswith(b"\xef\xbb\xbf"), "BOM UTF-8 attendu pour Excel")
        with open(fichier, encoding="utf-8-sig", newline="") as f:
            lignes = list(csv.reader(f, delimiter=";"))
        self.assertEqual(lignes[0][1], "Désignation")
        self.assertEqual(lignes[1][1:4], ["Imprimante étage", "Imprimante", "Hors service"])

    def test_formater_date(self):
        self.assertEqual(p.formater_date("2026-05-04T14:26:49.051120"), "04/05/2026 14:26")
        self.assertEqual(p.formater_date("pas une date"), "pas une date")

    def test_tri_sans_accents(self):
        noms = ["Tablette", "écran", "Borne", "Écran 2"]
        self.assertEqual(sorted(noms, key=p.cle_tri), ["Borne", "écran", "Écran 2", "Tablette"])

    def test_base_a_cote_du_script(self):
        self.assertEqual(p.BASE_DONNEES.parent, Path(p.__file__).resolve().parent)


if __name__ == "__main__":
    unittest.main()
