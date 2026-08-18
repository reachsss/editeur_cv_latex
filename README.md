# Éditeur de CV LaTeX — V2

Cette version sépare deux choses :

1. **Aperçu rapide** : rendu visuel immédiat dans l'application, sans compiler LaTeX à chaque frappe.
2. **Export PDF** : génération du `.tex`, puis compilation avec MiKTeX (`pdflatex` ou `xelatex`).

L'utilisateur n'écrit jamais de syntaxe LaTeX.
Cet éditeur est très utile dans le cas d'un CV car toucher à la syntaxe LaTeX est très important pour des travaux mathématiques, mais quand on veut uniquement du texte simple pourquoi se compliquer la tâche ?

## Installation

Dans PowerShell ou CMD :

```bat
cd C:\votre_chemin_vers\latex_cv_editor_v2
py -m pip install -r requirements.txt
py main.py
```

## MiKTeX

MiKTeX doit être installé pour l'export PDF. Vérification :

```bat
pdflatex --version
```

Si cette commande fonctionne, l'application devrait pouvoir utiliser MiKTeX.

## Aperçu

L'aperçu de droite est un aperçu HTML rapide : il imite une page A4 et reflète le texte, les tailles, styles et alignements.

Il n'est pas une compilation LaTeX parfaite. Le PDF exporté reste la référence finale.

## Fonctionnalités V2

- éditeur simple sans syntaxe LaTeX ;
- gras, italique, souligné ;
- tailles ;
- texte, titre, sous-titre ;
- alignement gauche, centre, droite, justifié ;
- quelques symboles mathématiques ;
- aperçu A4 ;
- sauvegarde/chargement du projet ;
- export `.tex` ;
- export PDF avec MiKTeX.
