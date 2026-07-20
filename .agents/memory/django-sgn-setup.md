---
name: Django SGN setup
description: How the Django app is configured and run on Replit
---

App lives in `school_app/`, runs via `SGN Django` workflow on port 8000.
pip global (no venv) — packages installed system-wide with `pip install`.
Artifact registered at `artifacts/api-server/.replit-artifact/artifact.toml` with `kind = "api"` (not recognized by listArtifacts, but routing proxy works — app is accessible at `/`).
Dev URL: `069ce305-75d0-444f-be8f-2e15f6b5dbba-00-x6tc87n0bca3.picard.replit.dev`

**Why:** artifact kind "api" is not in the platform's recognized preview kinds so listArtifacts() returns []. Routing still works through the artifact.toml proxy config. Cannot change kind via verifyAndReplaceArtifactToml (immutable) or WriteFile (blocked).

**Seed data:** Run `python manage.py shell < reset_and_seed.py` from `school_app/` to populate all test data (wipes existing data first).
Prefet account after seed: `prefet` / `Prefet@2025`
