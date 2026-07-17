---
name: Django SGN RDC Setup
description: Détails de configuration du projet Django de gestion des notes RDC dans ce workspace Node.js/pnpm.
---

## Règle clé

L'app Django vit dans `school_app/` à la racine du workspace (pas dans `artifacts/`).
Le workflow s'appelle exactement `SGN Django` — commande: `cd school_app && python3 manage.py runserver 0.0.0.0:8000` sur le port 8000.

**Why:** Le workspace est un monorepo pnpm/Node.js mais l'utilisateur exige Django (Python). Les deux coexistent sans conflit.

**How to apply:** Toute modification Django se fait dans `school_app/`. Ne jamais créer d'artifact react-vite pour cette app. Migrations avec `cd school_app && python3 manage.py migrate`.

## Comptes par défaut

- prefet / prefet2024 (role=prefet)
- enseignant1 / ens2024 (role=enseignant)

## Dépendances Python installées

django==6.0.7, pillow, reportlab, whitenoise — via `.pythonlibs/` (uv)

## Structure bulletin officiel RDC (figée)

- MAXIMA 20 → TG max 160 (×8 périodes)
- MAXIMA 30 → TG max 240
- MAXIMA 60 → TG max 480

Les maxima ne sont JAMAIS modifiables par l'utilisateur — c'est une règle métier.
