import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import csv

# Nom de la base de données SQLite
BASE_DONNEES = "inventaire.db"


def init_db():
    """Initialiser la base de données SQLite et créer la table materiel si elle n'existe pas.

    Cette fonction établit une connexion à la base de données 'inventaire.db' en utilisant
    un gestionnaire de contexte (with sqlite3.connect...), ce qui garantit que la connexion
    est automatiquement fermée même en cas d'erreur. Elle utilise la commande SQL
    CREATE TABLE IF NOT EXISTS pour créer la table 'materiel' avec les colonnes suivantes :
    - id_materiel : clé primaire auto-incrémentée (INTEGER PRIMARY KEY AUTOINCREMENT),
      ce qui signifie que SQLite génère automatiquement un numéro unique pour chaque nouvel enregistrement.
    - designation : texte non nul pour la désignation du matériel.
    - categorie : texte non nul pour la catégorie (PC, Tablette, Réseau).
    - etat : texte non nul pour l'état (Neuf, Utilisé, Maintenance).
    - date_ajout : texte non nul pour la date d'ajout au format ISO (YYYY-MM-DDTHH:MM:SS).

    Après l'exécution de la requête, conn.commit() valide les changements dans la base de données.
    Le with ferme automatiquement la connexion.
    """
    with sqlite3.connect(BASE_DONNEES) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materiel (
                id_materiel INTEGER PRIMARY KEY AUTOINCREMENT,
                designation TEXT NOT NULL,
                categorie TEXT NOT NULL,
                etat TEXT NOT NULL,
                date_ajout TEXT NOT NULL
            )
        """)
        conn.commit()


def charger_inventaire():
    """Charger tous les matériels depuis la base de données SQLite, triés par id_materiel décroissant.

    Cette fonction se connecte à la base de données en utilisant un gestionnaire de contexte,
    exécute une requête SELECT * FROM materiel ORDER BY id_materiel DESC pour récupérer
    toutes les lignes triées (les plus récents en premier). La commande cursor.execute() prépare
    et exécute la requête SQL. Ensuite, cursor.fetchall() récupère toutes les lignes résultantes
    sous forme de liste de tuples. Le with ferme automatiquement la connexion.
    """
    with sqlite3.connect(BASE_DONNEES) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM materiel ORDER BY id_materiel DESC")
        rows = cursor.fetchall()
    return rows


def rechercher_materiels(query):
    """Rechercher les matériels dont la désignation contient la chaîne query, triés par id_materiel décroissant.

    Cette fonction utilise une requête SELECT avec LIKE pour filtrer sur la désignation.
    Le paramètre query est entouré de % pour une recherche partielle (contient).
    Utilise un gestionnaire de contexte pour la connexion.
    """
    with sqlite3.connect(BASE_DONNEES) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM materiel WHERE designation LIKE ? ORDER BY id_materiel DESC", ('%' + query + '%',))
        rows = cursor.fetchall()
    return rows


def actualiser_liste(rows=None):
    """Mettre à jour l'affichage du Treeview avec les éléments fournis ou tous si None.

    Cette fonction vide d'abord le Treeview avec tree.delete(*tree.get_children()),
    puis insère chaque ligne. Pour la date, elle convertit le format ISO en 'JJ/MM/AAAA HH:mm'
    en utilisant datetime.fromisoformat() et strftime(). Chaque 'row' est un tuple
    (id, designation, categorie, etat, date_ajout).
    """
    for item in tree.get_children():
        tree.delete(item)
    if rows is None:
        rows = charger_inventaire()
    for row in rows:
        id_m, designation, categorie, etat, date_iso = row
        # Formater la date lisible
        try:
            date_obj = datetime.datetime.fromisoformat(date_iso)
            date_lisible = date_obj.strftime('%d/%m/%Y %H:%M')
        except ValueError:
            date_lisible = date_iso  # Si format invalide, garder brut
        tree.insert("", "end", values=(id_m, designation, categorie, etat, date_lisible))


def ajouter_materiel():
    """Ajouter un nouveau matériel à la base de données.

    On récupère les valeurs des champs de saisie, on vérifie que la désignation n'est pas vide.
    On obtient la date actuelle avec datetime.datetime.now().isoformat() pour la date_ajout.
    On utilise un gestionnaire de contexte pour la connexion DB, on exécute une requête
    INSERT INTO materiel (designation, categorie, etat, date_ajout) VALUES (?, ?, ?, ?)
    en utilisant des paramètres pour éviter les injections SQL. cursor.execute() prépare
    la requête avec les placeholders ?, puis les valeurs sont passées en tuple.
    conn.commit() valide l'insertion. Le with ferme automatiquement la connexion.
    Enfin, on actualise la liste et on réinitialise les champs.
    """
    designation = entree_designation.get().strip()
    categorie = variable_categorie.get()
    etat = variable_etat.get()

    if not designation:
        messagebox.showwarning("Champ vide", "Veuillez saisir une désignation de matériel.")
        return

    date_ajout = datetime.datetime.now().isoformat()

    with sqlite3.connect(BASE_DONNEES) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO materiel (designation, categorie, etat, date_ajout)
            VALUES (?, ?, ?, ?)
        """, (designation, categorie, etat, date_ajout))
        conn.commit()

    actualiser_liste()

    entree_designation.delete(0, tk.END)
    variable_categorie.set("PC")
    variable_etat.set("Neuf")


def supprimer_element():
    """Supprimer le matériel sélectionné dans le Treeview.

    Cette fonction permet de supprimer un élément de la base de données en récupérant l'ID
    de la ligne sélectionnée dans le Treeview. Elle inclut une confirmation pour éviter
    les suppressions accidentelles.

    Étapes détaillées :
    1. Récupération de la sélection : tree.selection() retourne une liste des IDs des éléments
       sélectionnés dans le Treeview. Si aucune ligne n'est sélectionnée, on affiche un message
       d'information et on quitte la fonction.
    2. Extraction de l'ID : Pour la première sélection (selection[0]), on utilise tree.item()
       pour obtenir les détails de l'élément, puis item['values'][0] donne la valeur de la
       première colonne, qui est l'id_materiel (clé primaire).
    3. Confirmation utilisateur : On affiche une boîte de dialogue de confirmation avec
       messagebox.askyesno(). Si l'utilisateur annule, on quitte sans supprimer.
    4. Connexion à la base de données : On ouvre une connexion SQLite avec sqlite3.connect(BASE_DONNEES).
    5. Exécution de la requête SQL : cursor.execute("DELETE FROM materiel WHERE id_materiel = ?", (id_materiel,))
       prépare et exécute la requête DELETE. Le placeholder ? est remplacé par id_materiel pour
       éviter les injections SQL. Cette commande supprime la ligne correspondante dans la table 'materiel'.
    6. Validation des changements : conn.commit() est essentiel pour appliquer la suppression
       de manière permanente dans le fichier de base de données SQLite. Sans commit, les changements
       ne seraient pas sauvegardés.
    7. Fermeture de la connexion : conn.close() libère les ressources.
    8. Rafraîchissement de l'affichage : actualiser_liste() vide le Treeview (tree.delete(*tree.get_children()))
       et recharge toutes les données depuis la base avec charger_inventaire(), puis insère les lignes
       mises à jour dans le Treeview avec tree.insert().
    """
    # Étape 1 : Vérifier s'il y a une sélection
    selection = tree.selection()
    if not selection:
        messagebox.showinfo("Aucune sélection", "Veuillez sélectionner un matériel à supprimer.")
        return

    # Étape 2 : Récupérer l'ID de la ligne sélectionnée
    item = tree.item(selection[0])
    id_materiel = item['values'][0]  # values[0] correspond à la colonne ID

    # Étape 3 : Demander confirmation à l'utilisateur
    confirmation = messagebox.askyesno(
        "Confirmer la suppression",
        "Voulez-vous vraiment supprimer le matériel sélectionné ?"
    )
    if not confirmation:
        return

    # Étape 4 : Se connecter à la base de données avec gestionnaire de contexte
    with sqlite3.connect(BASE_DONNEES) as conn:
        cursor = conn.cursor()

        # Étape 5 : Exécuter la requête DELETE
        cursor.execute("DELETE FROM materiel WHERE id_materiel = ?", (id_materiel,))

        # Étape 6 : Valider les changements dans la base de données
        conn.commit()

    # Étape 7 : Fermeture automatique avec with
    # Étape 8 : Rafraîchir l'affichage du Treeview
    actualiser_liste()


def export_csv():
    """Exporter le contenu actuel de la base de données vers un fichier CSV.

    Cette fonction charge tous les matériels, ouvre un fichier 'inventaire_export.csv'
    en mode écriture, et utilise csv.writer pour écrire les en-têtes puis les lignes.
    Le fichier est compatible avec Excel.
    """
    rows = charger_inventaire()
    with open("inventaire_export.csv", "w", newline="", encoding="utf-8") as fichier_csv:
        writer = csv.writer(fichier_csv)
        # Écrire les en-têtes
        writer.writerow(["ID", "Désignation", "Catégorie", "État", "Date ajout"])
        # Écrire les données
        for row in rows:
            writer.writerow(row)
    messagebox.showinfo("Export réussi", "Le fichier 'inventaire_export.csv' a été créé.")


def rechercher(event=None):
    """Fonction appelée lors de la frappe dans la barre de recherche.

    Récupère le texte de l'Entry, appelle rechercher_materiels, puis actualiser_liste avec les résultats filtrés.
    """
    query = entree_recherche.get().strip()
    if query:
        rows = rechercher_materiels(query)
    else:
        rows = None  # Charger tous
    actualiser_liste(rows)


# Création de la fenêtre principale Tkinter
fenetre = tk.Tk()
fenetre.title("Gestion de patrimoine informatique")
fenetre.geometry("800x650")  # Hauteur augmentée pour afficher tous les éléments
fenetre.resizable(True, True)  # Permettre le redimensionnement manuel avec la souris

# Cadre principal pour organiser les widgets
cadre_principal = tk.Frame(fenetre, padx=10, pady=10)
cadre_principal.pack(fill=tk.BOTH, expand=True)

# --- Zone de saisie du matériel ---
label_titre = tk.Label(cadre_principal, text="Ajouter un nouveau matériel", font=("Arial", 14, "bold"))
label_titre.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

label_designation = tk.Label(cadre_principal, text="Désignation :")
label_designation.grid(row=1, column=0, sticky="w", pady=5)
entree_designation = tk.Entry(cadre_principal, width=40)
entree_designation.grid(row=1, column=1, sticky="w", pady=5)

label_categorie = tk.Label(cadre_principal, text="Catégorie :")
label_categorie.grid(row=2, column=0, sticky="w", pady=5)
variable_categorie = tk.StringVar(value="PC")
option_categorie = tk.OptionMenu(cadre_principal, variable_categorie, "PC", "Tablette", "Réseau")
option_categorie.config(width=15)
option_categorie.grid(row=2, column=1, sticky="w", pady=5)

label_etat = tk.Label(cadre_principal, text="État :")
label_etat.grid(row=3, column=0, sticky="w", pady=5)
variable_etat = tk.StringVar(value="Neuf")
option_etat = tk.OptionMenu(cadre_principal, variable_etat, "Neuf", "Utilisé", "Maintenance")
option_etat.config(width=15)
option_etat.grid(row=3, column=1, sticky="w", pady=5)

bouton_ajouter = tk.Button(cadre_principal, text="Ajouter", width=15, command=ajouter_materiel)
bouton_ajouter.grid(row=4, column=0, columnspan=2, pady=15)

# --- Barre de recherche ---
label_recherche = tk.Label(cadre_principal, text="Rechercher par désignation :")
label_recherche.grid(row=5, column=0, sticky="w", pady=5)
entree_recherche = tk.Entry(cadre_principal, width=40)
entree_recherche.grid(row=5, column=1, sticky="w", pady=5)
entree_recherche.bind("<KeyRelease>", rechercher)

# --- Zone d'affichage de l'inventaire ---
label_inventaire = tk.Label(cadre_principal, text="Inventaire du matériel", font=("Arial", 14, "bold"))
label_inventaire.grid(row=6, column=0, columnspan=2, sticky="w", pady=(20, 10))

# Treeview pour afficher le tableau avec colonnes
tree = ttk.Treeview(cadre_principal, columns=("ID", "Désignation", "Catégorie", "État", "Date ajout"), show="headings", height=12)
tree.heading("ID", text="ID")
tree.heading("Désignation", text="Désignation")
tree.heading("Catégorie", text="Catégorie")
tree.heading("État", text="État")
tree.heading("Date ajout", text="Date ajout")

# Définir la largeur des colonnes
tree.column("ID", width=50, anchor="center")
tree.column("Désignation", width=200, anchor="w")
tree.column("Catégorie", width=100, anchor="center")
tree.column("État", width=100, anchor="center")
tree.column("Date ajout", width=150, anchor="center")

tree.grid(row=7, column=0, columnspan=2, sticky="w", pady=5)

# Scrollbar pour le Treeview
scrollbar = ttk.Scrollbar(cadre_principal, orient=tk.VERTICAL, command=tree.yview)
scrollbar.grid(row=7, column=2, sticky="ns", pady=5)
tree.configure(yscrollcommand=scrollbar.set)

bouton_supprimer = tk.Button(cadre_principal, text="Supprimer sélection", width=20, command=supprimer_element)
bouton_supprimer.grid(row=8, column=0, pady=15)

bouton_exporter = tk.Button(cadre_principal, text="Exporter en CSV", width=20, command=export_csv)
bouton_exporter.grid(row=8, column=1, pady=15)

# Initialisation de la base de données et chargement initial
init_db()
actualiser_liste()

# Boucle principale de l'interface graphique
fenetre.mainloop()
