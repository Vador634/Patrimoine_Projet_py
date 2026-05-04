import json
import os
import tkinter as tk
from tkinter import messagebox

# Nom du fichier local pour stocker l'inventaire
FICHIER_INVENTAIRE = "inventaire.json"

# Liste globale qui contiendra tous les matériels chargés depuis le fichier JSON
inventaire = []


def charger_inventaire():
    """Charger les données depuis le fichier inventaire.json.

    Si le fichier n'existe pas, on le crée avec une liste vide.
    Retourne une liste de dictionnaires représentant le matériel.
    """
    # Si le fichier n'existe pas encore, on le crée immédiatement
    if not os.path.exists(FICHIER_INVENTAIRE):
        with open(FICHIER_INVENTAIRE, "w", encoding="utf-8") as fichier:
            json.dump([], fichier, indent=2, ensure_ascii=False)
        return []

    # Si le fichier existe, on lit son contenu JSON
    with open(FICHIER_INVENTAIRE, "r", encoding="utf-8") as fichier:
        try:
            donnees = json.load(fichier)
            if isinstance(donnees, list):
                return donnees
            # En cas de contenu inattendu, on réinitialise le fichier
            return []
        except json.JSONDecodeError:
            # Si le JSON est invalide, on réinitialise en liste vide
            return []


def sauvegarder_inventaire():
    """Sauvegarder la liste globale inventaire dans le fichier JSON.

    Cette fonction est appelée à chaque modification de l'inventaire.
    """
    with open(FICHIER_INVENTAIRE, "w", encoding="utf-8") as fichier:
        json.dump(inventaire, fichier, indent=2, ensure_ascii=False)


def actualiser_liste():
    """Mettre à jour l'affichage du Listbox avec les éléments actuels.

    Cette fonction réinitialise le contenu visible et ré-affiche tout.
    """
    liste_matériel.delete(0, tk.END)
    for index, materiel in enumerate(inventaire, start=1):
        ligne = f"{index}. {materiel['designation']} - {materiel['categorie']} - {materiel['etat']}"
        liste_matériel.insert(tk.END, ligne)


def ajouter_materiel():
    """Ajouter un nouveau matériel à l'inventaire.

    On vérifie que la désignation n'est pas vide, puis on ajoute l'élément.
    """
    designation = entree_designation.get().strip()
    categorie = variable_categorie.get()
    etat = variable_etat.get()

    if not designation:
        messagebox.showwarning("Champ vide", "Veuillez saisir une désignation de matériel.")
        return

    nouvel_element = {
        "designation": designation,
        "categorie": categorie,
        "etat": etat,
    }

    inventaire.append(nouvel_element)
    sauvegarder_inventaire()
    actualiser_liste()

    entree_designation.delete(0, tk.END)
    variable_categorie.set("PC")
    variable_etat.set("Neuf")


def supprimer_materiel():
    """Supprimer le matériel sélectionné dans la liste.

    On enlève l'élément choisi et on sauvegarde immédiatement.
    """
    selection = liste_matériel.curselection()
    if not selection:
        messagebox.showinfo("Aucune sélection", "Veuillez sélectionner un matériel à supprimer.")
        return

    index_selection = selection[0]
    confirmation = messagebox.askyesno(
        "Confirmer la suppression",
        "Voulez-vous vraiment supprimer le matériel sélectionné ?"
    )
    if not confirmation:
        return

    inventaire.pop(index_selection)
    sauvegarder_inventaire()
    actualiser_liste()


# Création de la fenêtre principale Tkinter
fenetre = tk.Tk()
fenetre.title("Gestion de patrimoine informatique")
fenetre.geometry("650x420")
fenetre.resizable(False, False)

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

# --- Zone d'affichage de l'inventaire ---
label_inventaire = tk.Label(cadre_principal, text="Inventaire du matériel", font=("Arial", 14, "bold"))
label_inventaire.grid(row=5, column=0, columnspan=2, sticky="w", pady=(20, 10))

liste_matériel = tk.Listbox(cadre_principal, height=12, width=80)
liste_matériel.grid(row=6, column=0, columnspan=2, sticky="w", pady=5)

scrollbar = tk.Scrollbar(cadre_principal, orient=tk.VERTICAL, command=liste_matériel.yview)
scrollbar.grid(row=6, column=2, sticky="ns", pady=5)
liste_matériel.config(yscrollcommand=scrollbar.set)

bouton_supprimer = tk.Button(cadre_principal, text="Supprimer sélection", width=20, command=supprimer_materiel)
bouton_supprimer.grid(row=7, column=0, columnspan=2, pady=15)

# On charge l'inventaire au démarrage et on affiche immédiatement les éléments
inventaire = charger_inventaire()
actualiser_liste()

# Boucle principale de l'interface graphique
fenetre.mainloop()
