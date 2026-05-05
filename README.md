---

# 🖥️ PyAsset - Gestionnaire de Patrimoine Informatique

![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite)
![Interface](https://img.shields.io/badge/Interface-Tkinter-red?style=for-the-badge)

**PyAsset** est une application de bureau légère développée en **Python** permettant aux administrateurs systèmes ou techniciens de proximité de suivre l'inventaire du matériel informatique au sein d'une organisation[cite: 4].

---

## 📸 Captures d'écran

<img width="801" height="679" alt="image" src="https://github.com/user-attachments/assets/5937a0e4-a526-474e-be63-07b3768d4037" />

![Interface Principale](assets/main_ui.png)  
*Interface de gestion avec le tableau de bord et le formulaire d'ajout.*

---

## 📋 Présentation du projet
Ce projet a été réalisé dans le cadre du **BTS SIO (Services Informatiques aux Organisations)** pour valider les compétences liées à la gestion du patrimoine et au développement d'applications[cite: 4]. 

L'application permet de centraliser les informations relatives aux équipements (PC, Tablettes, Bornes réseau) dans une base de données locale sécurisée[cite: 4].

---

## ✨ Fonctionnalités
*   **🔍 Recherche dynamique :** Filtrage en temps réel des équipements par leur désignation[cite: 4].
*   **📊 Inventaire complet :** Affichage de tous les équipements dans un tableau dynamique (Treeview)[cite: 4].
*   **⚙️ Gestion CRUD :** Ajout et suppression de matériel avec mise à jour instantanée de la base de données[cite: 4].
*   **📄 Exportation de données :** Possibilité d'exporter l'inventaire au format **CSV** pour une exploitation sous Excel[cite: 4].
*   **💾 Persistance des données :** Utilisation de **SQLite** pour un stockage fiable sans configuration complexe[cite: 4].

---

## 🛠️ Technologies utilisées
*   **Langage :** Python 3.x[cite: 4]
*   **Interface Graphique :** Tkinter[cite: 4]
*   **Base de Données :** SQLite3 (base de données relationnelle embarquée)[cite: 4]
*   **Format d'export :** CSV[cite: 4]

---

## 🚀 Installation et Utilisation

### 1. Cloner le dépôt
```bash
git clone https://github.com/Vador634/Patrimoine_Projet_py.git
cd Patrimoine_Projet_py
```

### 2. Lancer l'application
```bash
python Jeux.py
```
> **Note :** Le script crée automatiquement le fichier `inventaire.db` au premier lancement si celui-ci n'existe pas[cite: 4].

---

## 📂 Structure de la Base de Données
Le projet s'appuie sur une table `materiel` structurée comme suit[cite: 3, 4] :

| Colonne | Type | Description |
| :--- | :--- | :--- |
| **id_materiel** | INTEGER | Clé primaire auto-incrémentée[cite: 3, 4] |
| **designation** | TEXT | Nom ou modèle de l'équipement[cite: 3, 4] |
| **categorie** | TEXT | Type de matériel (PC, Réseau, etc.)[cite: 3, 4] |
| **etat** | TEXT | État de fonctionnement (Neuf, Maintenance, etc.)[cite: 3, 4] |
| **date_ajout** | TEXT | Date d'enregistrement automatique[cite: 3, 4] |

---

## 🛡️ Sécurité
*   **Injections SQL :** Protection via l'utilisation systématique de requêtes paramétrées (placeholders `?`)[cite: 4].
*   **Gestion des ressources :** Utilisation de **Context Managers** (`with sqlite3.connect...`) pour garantir la fermeture propre de la base de données même en cas d'erreur[cite: 4].

---

## 💡 Où inclure des captures d'écran ?

Pour un rendu professionnel, je te conseille d'inclure des captures aux endroits suivants :

1.  **Sous le titre (Section "Captures d'écran") :** Mets une image de la fenêtre principale avec des données déjà saisies. C'est ce qui donne envie d'utiliser l'outil.
2.  **Dans la section "Fonctionnalités" :** Tu peux ajouter des petites captures spécifiques :
    *   Une image montrant la **barre de recherche** filtrant un élément.
    *   Une image de la **boîte de dialogue de confirmation** lors de la suppression.
3.  **Dans la section "Installation" :** Si tu as un message de succès lors de l'export CSV, mets une capture de l'explorateur de fichiers montrant le fichier `inventaire_export.csv` créé.
