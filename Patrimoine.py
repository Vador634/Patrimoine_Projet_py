"""
PyAsset — gestion du patrimoine informatique.

Application de bureau (Tkinter + SQLite) pour inventorier le matériel d'une
organisation : ajout, modification, suppression, recherche, filtre par
catégorie, tri des colonnes et export CSV compatible Excel.

Le fichier est organisé en deux parties :
  1. Accès aux données : fonctions indépendantes de l'interface (testables).
  2. Interface graphique : classe Application.

Lancement : python Patrimoine.py
"""

import csv
import datetime
import sqlite3
import tkinter as tk
import unicodedata
from contextlib import closing
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

# La base est créée à côté du script, quel que soit le dossier de lancement.
BASE_DONNEES = Path(__file__).resolve().parent / "inventaire.db"

CATEGORIES = ("PC", "Portable", "Tablette", "Réseau", "Imprimante", "Autre")
ETATS = ("Neuf", "Utilisé", "Maintenance", "Hors service")
LONGUEUR_MAX_DESIGNATION = 100


# =====================================================================
# 1. ACCÈS AUX DONNÉES
# =====================================================================

def connexion(chemin=BASE_DONNEES):
    """Ouvre une connexion SQLite qui sera fermée à la sortie du bloc `with`.

    Attention : `with sqlite3.connect(...)` seul valide ou annule la
    transaction mais ne ferme PAS la connexion. `closing()` garantit la
    fermeture (important sous Windows, où un fichier ouvert reste verrouillé).
    """
    return closing(sqlite3.connect(chemin))


def init_db(chemin=BASE_DONNEES):
    """Crée la table `materiel` si elle n'existe pas encore."""
    with connexion(chemin) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS materiel (
                id_materiel INTEGER PRIMARY KEY AUTOINCREMENT,
                designation TEXT NOT NULL,
                categorie   TEXT NOT NULL,
                etat        TEXT NOT NULL,
                date_ajout  TEXT NOT NULL
            )
        """)


def _echapper_like(texte):
    """Échappe les caractères spéciaux de LIKE (% et _) saisis par l'utilisateur."""
    return texte.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def charger_inventaire(recherche="", categorie=None, chemin=BASE_DONNEES):
    """Retourne les matériels (du plus récent au plus ancien).

    - recherche : texte contenu dans la désignation (insensible à la casse)
    - categorie : ne garder qu'une catégorie (None = toutes)
    Chaque ligne est un tuple (id, designation, categorie, etat, date_ajout).
    """
    requete = "SELECT id_materiel, designation, categorie, etat, date_ajout FROM materiel WHERE 1 = 1"
    parametres = []
    if recherche.strip():
        requete += " AND designation LIKE ? ESCAPE '\\'"
        parametres.append(f"%{_echapper_like(recherche.strip())}%")
    if categorie:
        requete += " AND categorie = ?"
        parametres.append(categorie)
    requete += " ORDER BY id_materiel DESC"

    with connexion(chemin) as conn:
        return conn.execute(requete, parametres).fetchall()


def _valider(designation, categorie, etat):
    """Vérifie les champs saisis et retourne la désignation nettoyée."""
    designation = (designation or "").strip()
    if not designation:
        raise ValueError("Veuillez saisir une désignation de matériel.")
    if len(designation) > LONGUEUR_MAX_DESIGNATION:
        raise ValueError(f"La désignation ne doit pas dépasser {LONGUEUR_MAX_DESIGNATION} caractères.")
    if categorie not in CATEGORIES:
        raise ValueError(f"Catégorie inconnue : {categorie}")
    if etat not in ETATS:
        raise ValueError(f"État inconnu : {etat}")
    return designation


def ajouter_materiel(designation, categorie, etat, chemin=BASE_DONNEES):
    """Ajoute un matériel et retourne son identifiant (requête paramétrée)."""
    designation = _valider(designation, categorie, etat)
    date_ajout = datetime.datetime.now().isoformat(timespec="seconds")
    with connexion(chemin) as conn, conn:
        curseur = conn.execute(
            "INSERT INTO materiel (designation, categorie, etat, date_ajout) VALUES (?, ?, ?, ?)",
            (designation, categorie, etat, date_ajout),
        )
        return curseur.lastrowid


def modifier_materiel(id_materiel, designation, categorie, etat, chemin=BASE_DONNEES):
    """Met à jour un matériel. Retourne True si une ligne a été modifiée."""
    designation = _valider(designation, categorie, etat)
    with connexion(chemin) as conn, conn:
        curseur = conn.execute(
            "UPDATE materiel SET designation = ?, categorie = ?, etat = ? WHERE id_materiel = ?",
            (designation, categorie, etat, id_materiel),
        )
        return curseur.rowcount == 1


def supprimer_materiels(ids, chemin=BASE_DONNEES):
    """Supprime plusieurs matériels en une transaction. Retourne le nombre supprimé."""
    ids = [int(i) for i in ids]
    if not ids:
        return 0
    with connexion(chemin) as conn, conn:
        curseur = conn.executemany("DELETE FROM materiel WHERE id_materiel = ?", [(i,) for i in ids])
        return curseur.rowcount


def cle_tri(valeur):
    """Clé de tri insensible à la casse et aux accents ("Écran" est rangé avec les "E")."""
    if isinstance(valeur, (int, float)):
        return (0, valeur, "")
    texte = unicodedata.normalize("NFD", str(valeur).lower())
    return (1, 0, "".join(c for c in texte if not unicodedata.combining(c)))


def formater_date(date_iso):
    """'2026-05-04T14:26:49' -> '04/05/2026 14:26' (texte brut si format inconnu)."""
    try:
        return datetime.datetime.fromisoformat(date_iso).strftime("%d/%m/%Y %H:%M")
    except (TypeError, ValueError):
        return date_iso


def exporter_csv(lignes, fichier):
    """Écrit les lignes dans un CSV lisible directement par Excel en français.

    - encodage utf-8-sig : le BOM permet à Excel d'afficher les accents
    - séparateur ';' : séparateur attendu par Excel en paramètres régionaux français
    """
    with open(fichier, "w", newline="", encoding="utf-8-sig") as fichier_csv:
        writer = csv.writer(fichier_csv, delimiter=";")
        writer.writerow(["ID", "Désignation", "Catégorie", "État", "Date d'ajout"])
        for id_m, designation, categorie, etat, date_iso in lignes:
            writer.writerow([id_m, designation, categorie, etat, formater_date(date_iso)])
    return len(lignes)


# =====================================================================
# 2. INTERFACE GRAPHIQUE
# =====================================================================

class Application(tk.Tk):
    COLONNES = ("ID", "Désignation", "Catégorie", "État", "Date d'ajout")
    TOUTES = "Toutes les catégories"

    def __init__(self, chemin=BASE_DONNEES):
        super().__init__()
        self.chemin = chemin
        self.id_en_edition = None          # id du matériel chargé dans le formulaire
        self.tri = ("ID", True)            # colonne et ordre décroissant

        self.title("PyAsset — Gestion du patrimoine informatique")
        self.geometry("860x640")
        self.minsize(720, 520)

        init_db(self.chemin)
        self._construire_formulaire()
        self._construire_recherche()
        self._construire_tableau()
        self._construire_boutons()
        self.actualiser()
        self.entree_designation.focus_set()

    # ---------- Construction de l'interface ----------

    def _construire_formulaire(self):
        cadre = ttk.LabelFrame(self, text="Matériel", padding=10)
        cadre.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(cadre, text="Désignation :").grid(row=0, column=0, sticky="w", pady=4)
        self.entree_designation = ttk.Entry(cadre, width=45)
        self.entree_designation.grid(row=0, column=1, columnspan=3, sticky="we", pady=4)
        self.entree_designation.bind("<Return>", lambda e: self.valider_formulaire())

        ttk.Label(cadre, text="Catégorie :").grid(row=1, column=0, sticky="w", pady=4)
        self.variable_categorie = tk.StringVar(value=CATEGORIES[0])
        ttk.Combobox(cadre, textvariable=self.variable_categorie, values=CATEGORIES,
                     state="readonly", width=18).grid(row=1, column=1, sticky="w", pady=4)

        ttk.Label(cadre, text="État :").grid(row=1, column=2, sticky="e", padx=(15, 5), pady=4)
        self.variable_etat = tk.StringVar(value=ETATS[0])
        ttk.Combobox(cadre, textvariable=self.variable_etat, values=ETATS,
                     state="readonly", width=18).grid(row=1, column=3, sticky="w", pady=4)

        self.bouton_valider = ttk.Button(cadre, text="Ajouter", command=self.valider_formulaire)
        self.bouton_valider.grid(row=0, column=4, rowspan=2, padx=(15, 5), sticky="ns")
        self.bouton_annuler = ttk.Button(cadre, text="Nouveau", command=self.vider_formulaire)
        self.bouton_annuler.grid(row=0, column=5, rowspan=2, sticky="ns")
        cadre.columnconfigure(1, weight=1)

    def _construire_recherche(self):
        cadre = ttk.Frame(self, padding=(10, 5))
        cadre.pack(fill=tk.X)
        ttk.Label(cadre, text="Rechercher :").pack(side=tk.LEFT)
        self.variable_recherche = tk.StringVar()
        self.variable_recherche.trace_add("write", lambda *a: self.actualiser())
        ttk.Entry(cadre, textvariable=self.variable_recherche, width=35).pack(side=tk.LEFT, padx=5)

        self.variable_filtre = tk.StringVar(value=self.TOUTES)
        filtre = ttk.Combobox(cadre, textvariable=self.variable_filtre, values=(self.TOUTES,) + CATEGORIES,
                              state="readonly", width=22)
        filtre.pack(side=tk.LEFT, padx=5)
        filtre.bind("<<ComboboxSelected>>", lambda e: self.actualiser())

    def _construire_tableau(self):
        cadre = ttk.Frame(self, padding=(10, 0))
        cadre.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(cadre, columns=self.COLONNES, show="headings", selectmode="extended")
        largeurs = {"ID": 60, "Désignation": 300, "Catégorie": 120, "État": 120, "Date d'ajout": 140}
        for colonne in self.COLONNES:
            self.tree.heading(colonne, text=colonne, command=lambda c=colonne: self.trier_par(c))
            self.tree.column(colonne, width=largeurs[colonne], anchor="w" if colonne == "Désignation" else "center")
        self.tree.tag_configure("maintenance", foreground="#b45309")
        self.tree.tag_configure("hors_service", foreground="#b91c1c")

        barre = ttk.Scrollbar(cadre, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=barre.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barre.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.charger_selection)
        self.tree.bind("<Delete>", lambda e: self.supprimer_selection())

    def _construire_boutons(self):
        cadre = ttk.Frame(self, padding=10)
        cadre.pack(fill=tk.X)
        ttk.Button(cadre, text="Supprimer la sélection", command=self.supprimer_selection).pack(side=tk.LEFT)
        ttk.Button(cadre, text="Exporter en CSV", command=self.exporter).pack(side=tk.LEFT, padx=10)
        self.statut = ttk.Label(cadre, text="")
        self.statut.pack(side=tk.RIGHT)

    # ---------- Affichage ----------

    def lignes_affichees(self):
        filtre = self.variable_filtre.get()
        return charger_inventaire(self.variable_recherche.get(), None if filtre == self.TOUTES else filtre, self.chemin)

    def actualiser(self):
        """Recharge le tableau en conservant la recherche, le filtre et le tri."""
        lignes = self.lignes_affichees()
        colonne, decroissant = self.tri
        index = self.COLONNES.index(colonne)
        lignes.sort(key=lambda l: cle_tri(l[index]), reverse=decroissant)

        self.tree.delete(*self.tree.get_children())
        for id_m, designation, categorie, etat, date_iso in lignes:
            tag = {"Maintenance": "maintenance", "Hors service": "hors_service"}.get(etat, "")
            self.tree.insert("", tk.END, iid=str(id_m), tags=(tag,),
                             values=(id_m, designation, categorie, etat, formater_date(date_iso)))

        total = len(charger_inventaire(chemin=self.chemin))
        en_maintenance = sum(1 for l in lignes if l[3] == "Maintenance")
        self.statut.config(text=f"{len(lignes)} affiché(s) sur {total} · {en_maintenance} en maintenance")

    def trier_par(self, colonne):
        colonne_actuelle, decroissant = self.tri
        self.tri = (colonne, not decroissant if colonne == colonne_actuelle else False)
        for c in self.COLONNES:
            fleche = (" ▼" if self.tri[1] else " ▲") if c == colonne else ""
            self.tree.heading(c, text=c + fleche)
        self.actualiser()

    # ---------- Actions ----------

    def charger_selection(self, event=None):
        """Une seule ligne sélectionnée : ses valeurs passent dans le formulaire pour modification."""
        selection = self.tree.selection()
        if len(selection) != 1:
            return
        id_m, designation, categorie, etat, _ = self.tree.item(selection[0], "values")
        self.id_en_edition = int(id_m)
        self.entree_designation.delete(0, tk.END)
        self.entree_designation.insert(0, designation)
        self.variable_categorie.set(categorie if categorie in CATEGORIES else CATEGORIES[-1])
        self.variable_etat.set(etat if etat in ETATS else ETATS[0])
        self.bouton_valider.config(text="Enregistrer")
        self.bouton_annuler.config(text="Annuler")

    def vider_formulaire(self):
        self.id_en_edition = None
        self.entree_designation.delete(0, tk.END)
        self.variable_categorie.set(CATEGORIES[0])
        self.variable_etat.set(ETATS[0])
        self.bouton_valider.config(text="Ajouter")
        self.bouton_annuler.config(text="Nouveau")
        self.tree.selection_remove(*self.tree.selection())
        self.entree_designation.focus_set()

    def valider_formulaire(self):
        """Ajoute un matériel, ou enregistre la modification du matériel sélectionné."""
        valeurs = (self.entree_designation.get(), self.variable_categorie.get(), self.variable_etat.get())
        try:
            if self.id_en_edition is None:
                ajouter_materiel(*valeurs, chemin=self.chemin)
            else:
                modifier_materiel(self.id_en_edition, *valeurs, chemin=self.chemin)
        except ValueError as erreur:
            messagebox.showwarning("Saisie invalide", str(erreur), parent=self)
            return
        except sqlite3.Error as erreur:
            messagebox.showerror("Base de données", f"Enregistrement impossible : {erreur}", parent=self)
            return
        self.vider_formulaire()
        self.actualiser()

    def supprimer_selection(self):
        ids = [int(i) for i in self.tree.selection()]
        if not ids:
            messagebox.showinfo("Aucune sélection", "Sélectionnez un ou plusieurs matériels à supprimer.", parent=self)
            return
        if not messagebox.askyesno("Confirmer la suppression",
                                   f"Supprimer définitivement {len(ids)} matériel(s) ?", parent=self):
            return
        supprimer_materiels(ids, self.chemin)
        self.vider_formulaire()
        self.actualiser()

    def exporter(self):
        """Exporte les lignes actuellement affichées (recherche et filtre appliqués)."""
        fichier = filedialog.asksaveasfilename(
            parent=self, title="Exporter l'inventaire", defaultextension=".csv",
            initialfile=f"inventaire_{datetime.date.today():%Y-%m-%d}.csv",
            filetypes=[("Fichier CSV", "*.csv")],
        )
        if not fichier:
            return
        try:
            nombre = exporter_csv(self.lignes_affichees(), fichier)
        except OSError as erreur:
            messagebox.showerror("Export impossible", str(erreur), parent=self)
            return
        messagebox.showinfo("Export réussi", f"{nombre} matériel(s) exporté(s) dans :\n{fichier}", parent=self)


def main():
    Application().mainloop()


if __name__ == "__main__":
    main()
