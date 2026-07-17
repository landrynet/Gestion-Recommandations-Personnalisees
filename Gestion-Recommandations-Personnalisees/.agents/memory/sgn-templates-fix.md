---
name: SGN Templates fix
description: Templates et vues corrigés lors de la 3ème session SGN (rôles, affectations par classe, dashboard).
---

## Ce qui a été corrigé / livré

### subjects/views.py
- Remplacé les `__import__` laids par un vrai `from django.urls import reverse`.
- `affectation_list` passe `matieres_non_20/30/60` (non encore affectées à la classe sélectionnée).

### subjects/affectation_list.html
- Vue entièrement centrée-classe : panneau gauche = liste des classes avec badge count; panneau droit = table des affectations + quick-add panel (checkboxes par maxima).

### subjects/matiere_list.html
- Attend `matieres_20`, `matieres_30`, `matieres_60` (QuerySets), plus `classes` et `annee`.
- Tableau récapitulatif par classe en bas.

### grades/templatetags/grades_tags.py
- Ajout du filtre `get_item` (dict[key]) utilisé dans consulter_notes.html.
- Garde le filtre `get_field` pour saisie_notes.html.

### grades/views.py
- `saisie_notes` : redirige le préfet vers `consulter_notes`; enseignant ne voit que ses MatiereClasse.
- Redirect utilisait une string hardcodée → remplacé par URL absolue propre.
- `consulter_notes` : vue lecture seule, préfet voit tout, enseignant filtre par teacher_profile.

### dashboard/index.html
- Fichier gardé comme stub (auto-redirect JS) car les vues renvoient directement index_prefet/index_enseignant.

**Why:** Les vues avaient été réécrites en session 2 mais les templates n'avaient pas suivi → page cassée au rendu.
**How to apply:** Toute modification future des vues subjects/ ou grades/ doit vérifier les noms de variables de contexte dans les templates correspondants.
