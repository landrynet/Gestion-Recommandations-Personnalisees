---
name: Django SGN setup
description: How the SGN RDC Django school app is set up and run on Replit.
---

# Django SGN RDC — Setup

**Why:** The app uses a custom Python environment (uv/pip managed globally, no venv). Django must be installed via `installLanguagePackages({ language: "python", packages: [...] })` if missing.

**Run command:** `cd /home/runner/workspace/school_app && python manage.py runserver 0.0.0.0:8000 --noreload`

**How to apply:** The workflow `SGN Django` manages this. To run management commands: `cd /home/runner/workspace/school_app && python manage.py <command>`.

**Packages required:** django>=6.0.7, pillow, reportlab, whitenoise, qrcode, openpyxl — declared in `/home/runner/workspace/pyproject.toml`.

**DB:** SQLite at `school_app/db.sqlite3`. Seed: `python manage.py shell < reset_and_seed.py`.

**Preview path:** Routes to `localhost:8000` via Replit proxy. Screenshot tool requires a registered artifact — app not yet registered as artifact.
