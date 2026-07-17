# Guide de déploiement sur PythonAnywhere

## Système de Gestion des Notes (SGN-RDC)

---

## Prérequis

- Compte PythonAnywhere (gratuit ou payant)
- Python 3.11+ disponible
- Accès à un compte GitHub avec ce dépôt

---

## Étape 1 : Cloner le projet

Depuis la **console Bash** de PythonAnywhere :

```bash
cd ~
git clone https://github.com/landkay2004/Gestion-Recommandations-Personnalisees.git sgn
cd sgn
```

---

## Étape 2 : Créer un environnement virtuel

```bash
python3.11 -m venv venv
source venv/bin/activate
```

---

## Étape 3 : Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> Les packages installés : Django, Pillow, ReportLab, WhiteNoise

---

## Étape 4 : Configurer les variables d'environnement

**Ne pas modifier `settings.py` directement.** Utilise plutôt des variables d'environnement
dans le fichier `~/.env` ou via le panneau PythonAnywhere.

Depuis la console Bash PythonAnywhere, ajoute ces lignes à la fin de `~/.bashrc` :

```bash
export DJANGO_SECRET_KEY='remplace-par-une-cle-secrete-longue-et-aleatoire'
export DJANGO_DEBUG='False'
export DJANGO_SITE_URL='https://educ.pythonanywhere.com'
```

Puis recharge :

```bash
source ~/.bashrc
```

> **Important :** `DJANGO_SITE_URL` doit commencer par `https://`. Si tu l'oublies,
> Django l'ajoute automatiquement — mais mets-le quand même pour être explicite.

Pour générer une clé secrète sécurisée :

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

**Dans le fichier WSGI** (`/var/www/educ_pythonanywhere_com_wsgi.py`),
ajoute aussi ces lignes **avant** l'import Django :

```python
import os
os.environ['DJANGO_SECRET_KEY'] = 'ta-cle-secrete'
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_SITE_URL'] = 'https://educ.pythonanywhere.com'
```

---

## Étape 5 : Appliquer les migrations et collecter les fichiers statiques

```bash
cd ~/sgn/school_app
python manage.py migrate
python manage.py collectstatic --noinput
```

---

## Étape 6 : Créer le compte administrateur (Préfet)

```bash
python manage.py shell
```

Dans le shell Python :

```python
from accounts.models import CustomUser

# Créer le compte préfet
u = CustomUser.objects.create_superuser('prefet', 'email@exemple.com', 'VotreMotDePasse2024')
u.role = 'prefet'
u.save()

# Créer un enseignant test
u2 = CustomUser.objects.create_user('enseignant1', '', 'MotDePasse2024')
u2.role = 'enseignant'
u2.save()

exit()
```

---

## Étape 7 : Configurer l'application Web sur PythonAnywhere

### 7.1 — Créer l'application Web

1. Aller sur **Web** dans le tableau de bord PythonAnywhere
2. Cliquer **Add a new web app**
3. Choisir votre domaine : `votrenom.pythonanywhere.com`
4. Sélectionner **Manual configuration**
5. Choisir **Python 3.11**

---

### 7.2 — Configurer le fichier WSGI

Cliquer sur le lien du fichier WSGI (ex: `/var/www/votrenom_pythonanywhere_com_wsgi.py`)

Remplacer **tout le contenu** par :

```python
import os
import sys

# Ajouter le chemin du projet
path = '/home/votrenom/sgn/school_app'
if path not in sys.path:
    sys.path.insert(0, path)

path2 = '/home/votrenom/sgn'
if path2 not in sys.path:
    sys.path.insert(0, path2)

os.environ['DJANGO_SETTINGS_MODULE'] = 'school_app.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

> **Remplacer `votrenom`** par votre nom d'utilisateur PythonAnywhere.

---

### 7.3 — Configurer l'environnement virtuel

Dans la section **Virtualenv** de la page Web :

```
/home/votrenom/sgn/venv
```

---

### 7.4 — Configurer les fichiers statiques

Dans la section **Static files** :

| URL        | Directory                                      |
|------------|------------------------------------------------|
| `/static/` | `/home/votrenom/sgn/school_app/staticfiles/`   |
| `/media/`  | `/home/votrenom/sgn/school_app/media/`         |

---

## Étape 8 : Recharger l'application

Cliquer le bouton **Reload** (vert) sur la page Web.

Accéder à : `https://votrenom.pythonanywhere.com`

---

## Étape 9 : Charger des données de test (optionnel)

```bash
cd ~/sgn/school_app
python manage.py shell < ../seed_data.py
```

---

## Mises à jour futures

Pour mettre à jour le projet après des modifications :

```bash
cd ~/sgn
git pull origin main
source venv/bin/activate
cd school_app
python manage.py migrate
python manage.py collectstatic --noinput
```

Puis cliquer **Reload** sur PythonAnywhere.

---

## Structure du projet Django

```
school_app/
├── manage.py
├── school_app/          ← Configuration principale (settings, urls, wsgi)
├── accounts/            ← Gestion des utilisateurs (CustomUser, login)
├── dashboard/           ← Tableau de bord préfet / enseignant
├── students/            ← Gestion des élèves
├── teachers/            ← Gestion des enseignants
├── classes/             ← Classes, sections, années scolaires
├── subjects/            ← Matières et affectations
├── bulletin/            ← Bulletins + export PDF (format IGE/P.S/005)
├── grades/              ← Saisie et consultation des notes
├── reports/             ← Rapports statistiques
├── school_settings/     ← Paramètres de l'école
├── static/              ← CSS, images (drapeau, armoiries)
├── templates/           ← Templates HTML
└── db.sqlite3           ← Base de données (SQLite)
```

---

## Comptes par défaut (après seed_data.py)

| Identifiant   | Mot de passe  | Rôle                    |
|---------------|---------------|-------------------------|
| `prefet`      | `prefet2024`  | Préfet (accès complet)  |
| `enseignant1` | `ens2024`     | Enseignant              |
| `prof_math`   | `ens123`      | Prof Maths/Physique     |
| `prof_fr`     | `ens123`      | Prof Français/Anglais   |
| `prof_bio`    | `ens123`      | Prof Biologie           |
| `prof_chimie` | `ens123`      | Prof Chimie             |
| `prof_hist`   | `ens123`      | Prof Histoire-Géo       |

---

## Règles métier importantes (ne pas modifier)

- **MAXIMA 20** → TG max = 160 (×8 périodes)
- **MAXIMA 30** → TG max = 240
- **MAXIMA 60** → TG max = 480
- Les maxima sont fixes — règle officielle RDC, non modifiable

---

## Dépannage

### Erreur 500 après déploiement
```bash
# Vérifier les logs d'erreur
cat /var/log/votrenom.pythonanywhere.com.error.log | tail -50
```

### Fichiers statiques manquants (CSS absent)
```bash
cd ~/sgn/school_app
source ~/sgn/venv/bin/activate
python manage.py collectstatic --noinput
```

### Base de données vide
```bash
cd ~/sgn/school_app
python manage.py migrate
python manage.py shell < ../seed_data.py
```

---

*Généré pour le projet SGN-RDC — Institut Technique Industriel KINSHASA*
