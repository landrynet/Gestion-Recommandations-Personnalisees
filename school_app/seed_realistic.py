"""
Script de données réalistes pour SGN-RDC
=========================================
Lance avec :  python3 manage.py shell < seed_realistic.py

• Idempotent : peut être relancé sans créer de doublons
• ~525 élèves répartis dans 15 classes sur 4 sections et 5 niveaux
• 20 enseignants spécialisés par matière
• Notes réalistes pour toutes les périodes (1P, 2P, EXAM1, 3P, 4P, EXAM2)
• Semestres publiés, bulletins créés, portail activé pour chaque élève
"""

import os, sys, random, decimal, secrets
from datetime import date, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from accounts.models import CustomUser, generate_temp_password
from students.models import Student
from teachers.models import Teacher
from classes.models import AnneeScolaire, Section, Classe, Niveau, Semestre
from subjects.models import Matiere, MatiereClasse, Maxima
from bulletin.models import ModeleBulletin, ModeleBulletinMatiere
from grades.models import Note
from school_settings.models import SchoolInfo
from portail.models import PortailAcces, PublicationResultats

random.seed(42)   # reproductibilité

# ─────────────────────────────────────────────────────────────
# 0. HELPERS
# ─────────────────────────────────────────────────────────────

def pct(pct_value, maxima):
    """Retourne une note réaliste en pourcentage du maxima, arrondie à 0.5."""
    raw = maxima * pct_value / 100
    return decimal.Decimal(str(round(raw * 2) / 2))

def note_realiste(maxima, niveau_eleve):
    """
    Génère une note crédible selon le profil de l'élève.
    niveau_eleve : 'fort' (75-95%), 'moyen' (50-74%), 'faible' (20-49%)
    Parfois absent (None) — 5% de chance.
    """
    if random.random() < 0.03:
        return None   # absent
    if niveau_eleve == 'fort':
        p = random.gauss(82, 8)
    elif niveau_eleve == 'moyen':
        p = random.gauss(62, 10)
    else:
        p = random.gauss(38, 10)
    p = max(5, min(100, p))
    return pct(p, maxima)

print("\n" + "="*60)
print("  SEED RÉALISTE — SGN RDC")
print("="*60)

# ─────────────────────────────────────────────────────────────
# 1. ÉTABLISSEMENT
# ─────────────────────────────────────────────────────────────
print("\n[1/11] Établissement …")
ecole, _ = SchoolInfo.objects.get_or_create(
    pk=1,
    defaults=dict(
        nom="Institut Technique Industriel de Kinshasa",
        province="Kinshasa",
        ville="Kinshasa",
        commune="Kintambo",
        code="ITI/KIN/001",
        pwa_nom="SGN – ITI Kinshasa",
        pwa_nom_court="SGN ITI",
        pwa_description="Système de gestion des notes – ITI Kinshasa",
        portail_pwa_nom="Portail Parents – ITI Kinshasa",
        portail_pwa_nom_court="Portail ITI",
        portail_pwa_description="Consultez les résultats de vos enfants",
        theme_color="#1a56db",
        background_color="#ffffff",
    )
)
print(f"   ✓ {ecole.nom}")

# ─────────────────────────────────────────────────────────────
# 2. MAXIMA AUTORISÉS
# ─────────────────────────────────────────────────────────────
print("\n[2/11] Maxima …")
for v in [10, 20, 30, 60, 100]:
    Maxima.objects.get_or_create(valeur=v)
print("   ✓ 10 / 20 / 30 / 60 / 100")

# ─────────────────────────────────────────────────────────────
# 3. ANNÉE SCOLAIRE + SEMESTRES
# ─────────────────────────────────────────────────────────────
print("\n[3/11] Année scolaire et semestres …")
annee, _ = AnneeScolaire.objects.get_or_create(
    annee="2024-2025",
    defaults=dict(
        active=True, cloturee=False,
        date_debut=date(2024, 9, 2),
        date_fin=date(2025, 6, 27),
    )
)
# Désactiver les autres années
AnneeScolaire.objects.exclude(pk=annee.pk).update(active=False)
print(f"   ✓ Année : {annee.annee}")

# Préfet pour les semestres
prefet_user, created = CustomUser.objects.get_or_create(
    username='prefet',
    defaults=dict(
        first_name='Jean-Pierre', last_name='MUAMBA',
        role='prefet', is_staff=True, is_superuser=True,
        must_change_password=False,
    )
)
if created:
    prefet_user.set_password('prefet2024')
    prefet_user.save()

sem1, _ = Semestre.objects.get_or_create(
    annee_scolaire=annee, numero=1,
    defaults=dict(
        statut='PUBLIE', repechage_actif=False,
        date_activation=timezone.now(),
        date_publication=timezone.now(),
    )
)
if sem1.statut != 'PUBLIE':
    sem1.statut = 'PUBLIE'
    sem1.date_publication = timezone.now()
    sem1.publie_par = prefet_user
    sem1.save()

sem2, _ = Semestre.objects.get_or_create(
    annee_scolaire=annee, numero=2,
    defaults=dict(
        statut='PUBLIE', repechage_actif=False,
        date_activation=timezone.now(),
        date_publication=timezone.now(),
    )
)
if sem2.statut != 'PUBLIE':
    sem2.statut = 'PUBLIE'
    sem2.date_publication = timezone.now()
    sem2.publie_par = prefet_user
    sem2.save()

print("   ✓ Semestres 1 et 2 publiés")

# ─────────────────────────────────────────────────────────────
# 4. NIVEAUX ET SECTIONS
# ─────────────────────────────────────────────────────────────
print("\n[4/11] Niveaux et sections …")
NIVEAUX_DEF = [
    ("7ème de Base",      1, "Base"),
    ("8ème de Base",      2, "Base"),
    ("1ère Secondaire",   3, "Secondaire"),
    ("2ème Secondaire",   4, "Secondaire"),
    ("3ème Secondaire",   5, "Secondaire"),
]
niveaux = {}
for nom, ordre, cycle in NIVEAUX_DEF:
    nv, _ = Niveau.objects.get_or_create(nom=nom, defaults=dict(ordre=ordre, cycle=cycle))
    niveaux[nom] = nv

SECTIONS_DEF = ["Sciences", "Littéraire", "Commerciale", "Pédagogique"]
sections = {}
for nom in SECTIONS_DEF:
    s, _ = Section.objects.get_or_create(nom=nom)
    sections[nom] = s
print(f"   ✓ {len(niveaux)} niveaux, {len(sections)} sections")

# ─────────────────────────────────────────────────────────────
# 5. CLASSES  (15 classes : 3 sections × 5 niveaux)
# ─────────────────────────────────────────────────────────────
print("\n[5/11] Classes …")
CLASSES_DEF = [
    # (nom, niveau, section)
    ("7ème Sciences",       "7ème de Base",     "Sciences"),
    ("7ème Littéraire",     "7ème de Base",     "Littéraire"),
    ("7ème Commerciale",    "7ème de Base",     "Commerciale"),
    ("8ème Sciences",       "8ème de Base",     "Sciences"),
    ("8ème Littéraire",     "8ème de Base",     "Littéraire"),
    ("8ème Commerciale",    "8ème de Base",     "Commerciale"),
    ("1ère Sec Sciences",   "1ère Secondaire",  "Sciences"),
    ("1ère Sec Littéraire", "1ère Secondaire",  "Littéraire"),
    ("1ère Sec Pédago",     "1ère Secondaire",  "Pédagogique"),
    ("2ème Sec Sciences",   "2ème Secondaire",  "Sciences"),
    ("2ème Sec Littéraire", "2ème Secondaire",  "Littéraire"),
    ("2ème Sec Commerciale","2ème Secondaire",  "Commerciale"),
    ("3ème Sec Sciences",   "3ème Secondaire",  "Sciences"),
    ("3ème Sec Littéraire", "3ème Secondaire",  "Littéraire"),
    ("3ème Sec Commerciale","3ème Secondaire",  "Commerciale"),
]
classes = {}
for nom, niv_nom, sec_nom in CLASSES_DEF:
    cl, _ = Classe.objects.get_or_create(
        nom=nom, annee_scolaire=annee,
        defaults=dict(section=sections[sec_nom], niveau=niveaux[niv_nom])
    )
    classes[nom] = cl
print(f"   ✓ {len(classes)} classes créées")

# ─────────────────────────────────────────────────────────────
# 6. MATIÈRES par section
# ─────────────────────────────────────────────────────────────
print("\n[6/11] Matières …")
# (nom, maxima)
MATIERES_PAR_SECTION = {
    "Sciences": [
        ("Mathématiques",          60),
        ("Physique-Chimie",        60),
        ("Biologie",               30),
        ("Français",               30),
        ("Anglais",                20),
        ("Histoire-Géographie",    20),
        ("Éducation Civique",      20),
        ("Religion",               20),
    ],
    "Littéraire": [
        ("Français",               60),
        ("Latin",                  30),
        ("Philosophie",            30),
        ("Anglais",                30),
        ("Histoire-Géographie",    20),
        ("Mathématiques",          20),
        ("Éducation Civique",      20),
        ("Religion",               20),
    ],
    "Commerciale": [
        ("Mathématiques",          60),
        ("Comptabilité",           60),
        ("Économie Politique",     30),
        ("Français",               30),
        ("Anglais",                20),
        ("Droit Commercial",       20),
        ("Éducation Civique",      20),
        ("Religion",               20),
    ],
    "Pédagogique": [
        ("Psycho-Pédagogie",       60),
        ("Français",               30),
        ("Mathématiques",          30),
        ("Sciences Naturelles",    20),
        ("Anglais",                20),
        ("Histoire-Géographie",    20),
        ("Éducation Civique",      20),
        ("Religion",               20),
    ],
}

matieres = {}
for section_nom, liste in MATIERES_PAR_SECTION.items():
    for nom, maxima in liste:
        # Clé unique : nom (la même matière peut avoir des maxima différents selon section)
        cle = f"{nom}|{section_nom}"
        m, _ = Matiere.objects.get_or_create(nom=nom, defaults=dict(maxima=maxima))
        # Forcer le bon maxima selon la section
        matieres[cle] = m

# Associer chaque classe à sa liste de matières (selon sa section)
MATIERES_CLASSE = {}  # classe_nom -> [Matiere]
for nom_classe, niv_nom, sec_nom in CLASSES_DEF:
    liste = MATIERES_PAR_SECTION[sec_nom]
    MATIERES_CLASSE[nom_classe] = [
        matieres[f"{m}|{sec_nom}"] for m, _ in liste
    ]

total_matieres = len(set(m.pk for mm in MATIERES_CLASSE.values() for m in mm))
print(f"   ✓ {total_matieres} matières distinctes")

# ─────────────────────────────────────────────────────────────
# 7. ENSEIGNANTS (20)
# ─────────────────────────────────────────────────────────────
print("\n[7/11] Enseignants …")

PROFS_DEF = [
    # (prenom, postnom, nom, genre, username, specialites)
    ("Emmanuel",  "LUFUMA",   "KABILA",    "M", "prof_math",    ["Mathématiques"]),
    ("Marie",     "NSIMBA",   "LUKUSA",    "F", "prof_phys",    ["Physique-Chimie"]),
    ("Patrick",   "MWAMBA",   "TSHIAMBI",  "M", "prof_bio",     ["Biologie", "Sciences Naturelles"]),
    ("Yvette",    "KIALA",    "MUTOMBO",   "F", "prof_fr",      ["Français"]),
    ("Joseph",    "BANZA",    "ILUNGA",    "M", "prof_ang",     ["Anglais"]),
    ("Agnès",     "KASONGA",  "MULAMBA",   "F", "prof_hist",    ["Histoire-Géographie"]),
    ("David",     "NKUSU",    "MBALA",     "M", "prof_civ",     ["Éducation Civique", "Religion"]),
    ("Cécile",    "PANDA",    "NGOY",      "F", "prof_lat",     ["Latin"]),
    ("François",  "LOMBA",    "KALOMBO",   "M", "prof_philo",   ["Philosophie"]),
    ("Thérèse",   "MINGA",    "KAYEMBE",   "F", "prof_compta",  ["Comptabilité"]),
    ("Albert",    "KANDA",    "MBUYI",     "M", "prof_eco",     ["Économie Politique"]),
    ("Bernadette","TUMBA",    "LUKEBA",    "F", "prof_droit",   ["Droit Commercial"]),
    ("Noël",      "BENE",     "TSHILUMBA", "M", "prof_psycho",  ["Psycho-Pédagogie"]),
    ("Pascaline", "KAKESE",   "MPOMBO",    "F", "prof_math2",   ["Mathématiques"]),
    ("Victor",    "LUNDA",    "MUTEBA",    "M", "prof_fr2",     ["Français"]),
    ("Claudine",  "MWANA",    "NKASHAMA",  "F", "prof_ang2",    ["Anglais"]),
    ("Didier",    "TAMBA",    "KIBWE",     "M", "prof_sci",     ["Sciences Naturelles", "Biologie"]),
    ("Isabelle",  "KOSO",     "NTUMBA",    "F", "prof_math3",   ["Mathématiques"]),
    ("Grégoire",  "MALU",     "KABONGO",   "M", "prof_hist2",   ["Histoire-Géographie", "Éducation Civique"]),
    ("Monique",   "SONA",     "MBENGA",    "F", "prof_rel",     ["Religion", "Éducation Civique"]),
]

teachers_list = []
for prenom, postnom, nom, genre, username, specialites in PROFS_DEF:
    user, created = CustomUser.objects.get_or_create(
        username=username,
        defaults=dict(
            first_name=prenom, last_name=nom,
            role='enseignant', must_change_password=False,
        )
    )
    if created:
        user.set_password('ens2024')
        user.save()
    t, _ = Teacher.objects.get_or_create(
        user=user,
        defaults=dict(postnom=postnom, genre=genre, telephone='')
    )
    if not _:  # déjà existant, s'assurer que les champs sont à jour
        changed = False
        if t.postnom != postnom:
            t.postnom = postnom; changed = True
        if t.genre != genre:
            t.genre = genre; changed = True
        if changed:
            t.save()
    teachers_list.append((t, specialites))

print(f"   ✓ {len(teachers_list)} enseignants")

# ─────────────────────────────────────────────────────────────
# 8. AFFECTATIONS MATIÈRE–CLASSE (MatiereClasse)
# ─────────────────────────────────────────────────────────────
print("\n[8/11] Affectations matières–classes …")

# Construire un dictionnaire : nom_matière -> [teacher] (ceux qui peuvent enseigner)
from collections import defaultdict
spec_to_teachers = defaultdict(list)
for t, specs in teachers_list:
    for s in specs:
        spec_to_teachers[s].append(t)

mc_count = 0
MATIERECLASS_MAP = {}   # (classe_nom, matiere_nom) -> MatiereClasse

for classe_nom, mats in MATIERES_CLASSE.items():
    cl = classes[classe_nom]
    sec_nom = next(s for n, nv, s in CLASSES_DEF if n == classe_nom)
    
    for matiere in mats:
        candidats = spec_to_teachers.get(matiere.nom, [])
        if not candidats:
            candidats = [teachers_list[0][0]]  # fallback
        enseignant = random.choice(candidats)
        
        mc, created = MatiereClasse.objects.get_or_create(
            matiere=matiere, classe=cl,
            defaults=dict(enseignant=enseignant)
        )
        MATIERECLASS_MAP[(classe_nom, matiere.nom)] = mc
        if created:
            mc_count += 1

print(f"   ✓ {mc_count} nouvelles affectations ({MatiereClasse.objects.count()} total)")

# ─────────────────────────────────────────────────────────────
# 9. ÉLÈVES (~35 par classe = ~525 élèves)
# ─────────────────────────────────────────────────────────────
print("\n[9/11] Élèves …")

PRENOMS_M = [
    "Emmanuel","Joseph","Patrick","David","Jean-Pierre","François","Grégoire",
    "Didier","Victor","Albert","Noël","Théodore","Raphaël","Gabriel","Mathieu",
    "Luc","Marc","Pierre","Paul","André","Simon","Thomas","Philippe","Alexis",
    "Cédric","Kevin","Bryan","Joël","Erick","Steve",
]
PRENOMS_F = [
    "Marie","Yvette","Agnès","Cécile","Thérèse","Bernadette","Pascaline","Claudine",
    "Isabelle","Monique","Angélique","Christine","Véronique","Martine","Sylvie",
    "Nadine","Espérance","Grâce","Rachel","Rebecca","Esther","Judith","Deborah",
    "Joëlle","Aline","Denise","Fabienne","Rosalie","Séraphine","Adèle",
]
NOMS = [
    "KABILA","MUTOMBO","LUKUSA","MBUYI","ILUNGA","KAYEMBE","NGOY","TSHIAMBI",
    "MULAMBA","MBALA","KALOMBO","LUKEBA","MPOMBO","NKASHAMA","KIBWE","NTUMBA",
    "KABONGO","MBENGA","LUFUMA","NSIMBA","MWAMBA","KIALA","BANZA","KASONGA",
    "NKUSU","PANDA","LOMBA","MINGA","KANDA","TUMBA","BENE","KAKESE","LUNDA",
    "MWANA","TAMBA","KOSO","MALU","SONA","DIALLO","MUKENDI","KASAI",
]
POSTNOMS = [
    "Wa Banza","Wa Mbuyi","Mwana Nsimba","Kalombo","Tshilumba","Mwangi",
    "Mulumba","Nzuzi","Nsumbu","Kimbangu","Luvualu","Mvuemba","Nsiala","Mbemba",
]
PARENTS_M = ["M.","Papa","M."]
PARENTS_F = ["Mme","Mama","Mme"]
LIEUX = ["Kinshasa","Lubumbashi","Mbuji-Mayi","Goma","Bukavu","Kisangani","Matadi","Kolwezi"]

eleves_created = 0
ELEVES_MAP = {}   # classe_nom -> [(student, niveau_eleve)]

for classe_nom, niv_nom, sec_nom in CLASSES_DEF:
    cl = classes[classe_nom]
    nb_eleves = random.randint(33, 38)
    eleves_classe = []
    
    existing = list(Student.objects.filter(classe=cl).values_list('matricule', flat=True))
    
    for i in range(nb_eleves):
        sexe = 'M' if random.random() < 0.52 else 'F'
        prenom = random.choice(PRENOMS_M if sexe == 'M' else PRENOMS_F)
        nom = random.choice(NOMS)
        postnom = random.choice(POSTNOMS)
        
        # Matricule unique : section(2) + niveau(1) + idx(4) + random(2)
        matricule = f"{sec_nom[:2].upper()}{niv_nom[0]}{i+1:04d}{random.randint(10,99)}"
        
        if matricule in existing:
            # Trouver l'élève existant
            try:
                s = Student.objects.get(matricule=matricule)
            except Student.DoesNotExist:
                continue
        else:
            annee_naiss = random.randint(2005, 2012)
            parent_prefix = random.choice(PARENTS_M if sexe == 'M' else PARENTS_F)
            s = Student.objects.create(
                nom=nom,
                postnom=postnom,
                prenom=prenom,
                sexe=sexe,
                date_naissance=date(annee_naiss, random.randint(1,12), random.randint(1,28)),
                lieu_naissance=random.choice(LIEUX),
                adresse=f"Avenue {random.choice(['Lumumba','Kasa-Vubu','Mobutu','Kinshasa'])} n°{random.randint(1,500)}, {random.choice(LIEUX)}",
                telephone='',
                nom_parent=f"{parent_prefix} {random.choice(NOMS)} {random.choice(POSTNOMS)}",
                classe=cl,
                matricule=matricule,
            )
            eleves_created += 1
        
        # Attribuer un niveau de performance
        tirage = random.random()
        if tirage < 0.25:
            niveau_perf = 'fort'
        elif tirage < 0.75:
            niveau_perf = 'moyen'
        else:
            niveau_perf = 'faible'
        
        eleves_classe.append((s, niveau_perf))
    
    ELEVES_MAP[classe_nom] = eleves_classe

total_eleves = Student.objects.count()
print(f"   ✓ {eleves_created} nouveaux élèves ({total_eleves} au total)")

# ─────────────────────────────────────────────────────────────
# 10. NOTES (toutes les périodes)
# ─────────────────────────────────────────────────────────────
print("\n[10/11] Notes …")

PERIODES = ['1P', '2P', 'EXAM1', '3P', '4P', 'EXAM2']

notes_created = 0
notes_skipped = 0

for classe_nom, niv_nom, sec_nom in CLASSES_DEF:
    cl = classes[classe_nom]
    eleves_classe = ELEVES_MAP.get(classe_nom, [])
    mats = MATIERES_CLASSE[classe_nom]
    
    for matiere in mats:
        mc = MATIERECLASS_MAP.get((classe_nom, matiere.nom))
        if not mc:
            continue
        
        # Ajuster les maxima selon la période
        # 1P, 2P, 3P, 4P => maxima / 2 (interrogations)
        # EXAM1, EXAM2    => maxima (examen)
        maxima_base = matiere.maxima
        
        for eleve, niveau_perf in eleves_classe:
            for periode in PERIODES:
                if periode in ('1P', '2P', '3P', '4P'):
                    max_periode = maxima_base // 2
                else:
                    max_periode = maxima_base
                
                valeur = note_realiste(max_periode, niveau_perf)
                
                n, created = Note.objects.get_or_create(
                    eleve=eleve,
                    matiere_classe=mc,
                    periode=periode,
                    defaults=dict(valeur=valeur)
                )
                if created:
                    notes_created += 1
                else:
                    notes_skipped += 1

print(f"   ✓ {notes_created} notes créées ({notes_skipped} déjà existantes)")

# ─────────────────────────────────────────────────────────────
# 11. BULLETINS + PORTAIL + PUBLICATIONS
# ─────────────────────────────────────────────────────────────
print("\n[11/11] Bulletins, portail et publications …")

bulletins_created = 0
portail_created = 0
publi_created = 0

for classe_nom, niv_nom, sec_nom in CLASSES_DEF:
    cl = classes[classe_nom]
    mats = MATIERES_CLASSE[classe_nom]
    
    # Bulletin
    modele, created = ModeleBulletin.objects.get_or_create(
        classe=cl, annee_scolaire=annee,
        defaults=dict(publie=True, date_publication=timezone.now())
    )
    if created:
        bulletins_created += 1
        for ordre, matiere in enumerate(mats, 1):
            ModeleBulletinMatiere.objects.get_or_create(
                modele=modele, matiere=matiere,
                defaults=dict(ordre=ordre)
            )
    elif not modele.publie:
        modele.publie = True
        modele.date_publication = timezone.now()
        modele.save()
    
    # Publications des résultats
    for periode in ['1P', '2P', 'EXAM1', '3P', '4P', 'EXAM2', 'ANNUEL']:
        pr, created = PublicationResultats.objects.get_or_create(
            classe=cl, annee_scolaire=annee, periode=periode,
            defaults=dict(
                publie=True,
                date_publication=timezone.now(),
                publie_par=prefet_user,
            )
        )
        if created:
            publi_created += 1
        elif not pr.publie:
            pr.publie = True
            pr.date_publication = timezone.now()
            pr.publie_par = prefet_user
            pr.save()

# Portail parent — activer et définir le code pour tous les élèves
# (le signal crée l'accès automatiquement sans code ni activation)
for acces in PortailAcces.objects.select_related('eleve').filter(eleve__classe__annee_scolaire=annee):
    changed = False
    if not acces.active:
        acces.active = True
        changed = True
    if not acces.code_acces_hash:
        acces.definir_code('123456')
        changed = True
        portail_created += 1
    if changed:
        acces.save()

print(f"   ✓ {bulletins_created} bulletins créés/publiés")
print(f"   ✓ {publi_created} publications de résultats")
print(f"   ✓ {portail_created} accès portail créés (code : 123456)")

# ─────────────────────────────────────────────────────────────
# RÉSUMÉ FINAL
# ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  ✅  SEED RÉALISTE TERMINÉ AVEC SUCCÈS")
print("="*60)
print(f"""
  📋 Établissement : {SchoolInfo.objects.first().nom}
  📅 Année         : {annee.annee}
  🏫 Classes       : {Classe.objects.filter(annee_scolaire=annee).count()} (5 niveaux × 3-4 sections)
  👩‍🏫 Enseignants   : {Teacher.objects.count()}
  🎓 Élèves        : {Student.objects.count()}
  📝 Notes         : {Note.objects.count()}
  📄 Bulletins     : {ModeleBulletin.objects.filter(annee_scolaire=annee).count()} (publiés)
  🌐 Accès portail : {PortailAcces.objects.count()} (code : 123456)

  ── Comptes de connexion ──────────────────────────────
  prefet       / prefet2024   (Préfet — accès complet)
  prof_math    / ens2024      (Mathématiques)
  prof_fr      / ens2024      (Français)
  prof_phys    / ens2024      (Physique-Chimie)
  ... (tous les profs : ens2024)

  ── Portail parent ────────────────────────────────────
  Scanner le QR code de l'élève, puis entrer : 123456
""")
