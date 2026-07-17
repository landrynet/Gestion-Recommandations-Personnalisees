---
name: SGN PDF et Rapports
description: Export PDF bulletin IGE/P.S/005 avec ReportLab + rapports enrichis avec statistiques de classe.
---

## PDF Export (bulletin/pdf_views.py)
- ReportLab 5.0.0 est déjà disponible dans l'environnement Nix — pas besoin de pip install.
- Vue `bulletin_eleve_pdf` dans `bulletin/pdf_views.py` (séparé de views.py pour clarté).
- URL : `bulletins/<pk>/eleve/<eleve_pk>/pdf/` → name=`bulletin_eleve_pdf`
- Format A4 portrait, marges 1.2cm, reproduit fidèlement le tableau IGE/P.S/005.
- Colonnes : Branches | 1P | 2P | EXAM | TOT.S1 | 3P | 4P | EXAM | TOT.S2 | TG | Repêchage | Sign.
- Lignes MAXIMA auto-calculées (mx, mx, mx*2, mx*4 pour chaque groupe).
- Bilan : MAXIMA GÉNÉRAUX, TOTAUX, POURCENTAGE, MENTION, PLACE/NBRE ÉLÈVES, APPLICATION, CONDUITE, SIGN.
- Utilise `school_settings.SchoolInfo.get_info()` directement (pas le context processor).
- Content-Disposition: inline → s'ouvre dans le navigateur, pas téléchargement forcé.

**Why:** Le context processor `school_info` est uniquement pour les templates Django, pas utilisable dans les vues PDF.

## Totaux automatiques (bulletin_eleve)
- `tot_s1` et `tot_s2` sont maintenant `None` si aucune note de ce semestre (au lieu de 0).
- Le template affiche les totaux seulement si not None → évite d'afficher "0" pour des semestres vides.
- Sous-totaux par groupe de maxima ajoutés dans le template HTML (ligne S/TOTAL MAX.XX).
- `total_max` est la somme des `maxima * 8` pour toutes les matières du bulletin.

## Rapports enrichis (reports/views.py)
- `rapport_resultats` passe maintenant `stats` (nb, nb_admis, nb_echec, pct_reuss, moy_classe, mentions).
- `rapport_resultats` passe aussi `modele` (objet complet) pour les liens bulletin_eleve et bulletin_eleve_pdf.
- Supprimé le `__import__` laid → remplacé par `from django.db.models import Sum`.
- Template : 5 cartes stats, répartition des mentions en badges, liens 👁 et 📄 par élève.

**How to apply:** Toute nouvelle colonne dans le rapport résultats doit être ajoutée aux deux côtés (vue + template). Le `modele_id` reste une string dans le template pour la comparaison `== b.pk|stringformat:"s"`.
