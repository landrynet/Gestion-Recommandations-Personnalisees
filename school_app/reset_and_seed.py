"""
Script de remise à zéro + données de test complètes pour SGN RDC
Usage : python manage.py shell < reset_and_seed.py
"""
import django, os, datetime, random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_app.settings')

# ══════════════════════════════════════════════════════════════════
#  0. FLUSH COMPLET
# ══════════════════════════════════════════════════════════════════
print("🗑️  Suppression de toutes les données existantes...")

from grades.models import Note
from bulletin.models import ModeleBulletin, ModeleBulletinMatiere
from portail.models import PortailAcces, PublicationResultats, PortailConfig
from subjects.models import MatiereClasse, Matiere
from students.models import Student
from teachers.models import Teacher
from accounts.models import CustomUser
from classes.models import Classe, Section, AnneeScolaire
from school_settings.models import SchoolInfo

Note.objects.all().delete()
ModeleBulletinMatiere.objects.all().delete()
ModeleBulletin.objects.all().delete()
PublicationResultats.objects.all().delete()
PortailAcces.objects.all().delete()
MatiereClasse.objects.all().delete()
Student.objects.all().delete()
Teacher.objects.all().delete()
CustomUser.objects.all().delete()
Classe.objects.all().delete()
Section.objects.all().delete()
AnneeScolaire.objects.all().delete()
Matiere.objects.all().delete()
SchoolInfo.objects.all().delete()
PortailConfig.objects.all().delete()
print("  ✓ Base vidée\n")

random.seed(2025)

# ══════════════════════════════════════════════════════════════════
#  1. INFOS DE L'ÉCOLE
# ══════════════════════════════════════════════════════════════════
info = SchoolInfo.objects.create(
    pk=1,
    nom='Complexe Scolaire Protestant de BUNGULU',
    province='Nord-Kivu',
    ville='Beni',
    commune='Bungulu',
    code='62024 / 101 / 03 / 1',
    pwa_nom='Système de Gestion Scolaire',
    pwa_nom_court='SGS',
    pwa_description='Plateforme de gestion scolaire — CSP Bungulu',
    portail_pwa_nom='Portail Parents CSP',
    portail_pwa_nom_court='Parent',
    theme_color='#1E293B',
    background_color='#0f172a',
)
print(f"🏫 École : {info.nom}")

# ══════════════════════════════════════════════════════════════════
#  2. PORTAIL CONFIG
# ══════════════════════════════════════════════════════════════════
PortailConfig.objects.create(
    pk=1,
    nom_portail='Portail des Résultats — CSP Bungulu',
    texte_accueil='Bienvenue sur le Portail des Résultats du Complexe Scolaire Protestant de Bungulu. Consultez les résultats de votre enfant en toute sécurité.',
    couleur_primaire='#2563EB',
    couleur_secondaire='#1E293B',
)

# ══════════════════════════════════════════════════════════════════
#  3. ANNÉE SCOLAIRE
# ══════════════════════════════════════════════════════════════════
annee = AnneeScolaire.objects.create(annee='2024-2025', active=True)
print(f"📅 Année scolaire : {annee.annee}")

# ══════════════════════════════════════════════════════════════════
#  4. SECTIONS
# ══════════════════════════════════════════════════════════════════
sec_sc   = Section.objects.create(nom='Sciences')
sec_lit  = Section.objects.create(nom='Littéraire')
sec_comm = Section.objects.create(nom='Commerciale & Gestion')
print("📚 Sections : Sciences | Littéraire | Commerciale & Gestion")

# ══════════════════════════════════════════════════════════════════
#  5. CLASSES
# ══════════════════════════════════════════════════════════════════
def mk_classe(nom, section):
    return Classe.objects.create(nom=nom, section=section, annee_scolaire=annee)

classes = {
    '4SC':  mk_classe('4ème', sec_sc),
    '5SC':  mk_classe('5ème', sec_sc),
    '6SC':  mk_classe('6ème', sec_sc),
    '4LIT': mk_classe('4ème', sec_lit),
    '5LIT': mk_classe('5ème', sec_lit),
    '4CG':  mk_classe('4ème', sec_comm),
}
print(f"🏛️  {len(classes)} classes créées")

# ══════════════════════════════════════════════════════════════════
#  6. COMPTES UTILISATEURS
# ══════════════════════════════════════════════════════════════════
# — Préfet —
prefet = CustomUser.objects.create_user(
    username='prefet',
    email='prefet@cspbungulu.cd',
    password='Prefet@2025',
    first_name='Kayoyo',
    last_name='Landry',
    role='prefet',
    must_change_password=False,
)
print(f"\n👤 Préfet créé")
print(f"   username : prefet")
print(f"   password : Prefet@2025")

# — Enseignants —
ens_data = [
    ('prof_math',   'Math@2025',  'Mutombo',   'Jean-Pierre',  'jean.mutombo@cspbungulu.cd',  '+243810001001'),
    ('prof_fr',     'Franc@2025', 'Kabila',    'Marie-Claire', 'marie.kabila@cspbungulu.cd',   '+243810001002'),
    ('prof_bio',    'Bio@2025',   'Lukusa',    'David',        'david.lukusa@cspbungulu.cd',   '+243810001003'),
    ('prof_chimie', 'Chim@2025',  'Nzuzi',     'Espoir',       'espoir.nzuzi@cspbungulu.cd',  '+243810001004'),
    ('prof_hist',   'Hist@2025',  'Mbemba',    'Sylvie',       'sylvie.mbemba@cspbungulu.cd', '+243810001005'),
    ('prof_phys',   'Phys@2025',  'Kabasele',  'Albert',       'albert.kabasele@cspbungulu.cd','+243810001006'),
    ('prof_angl',   'Angl@2025',  'Ngandu',    'Chantal',      'chantal.ngandu@cspbungulu.cd','+243810001007'),
]
teachers = {}
print("\n👨‍🏫 Enseignants créés :")
for username, pwd, last, first, email, tel in ens_data:
    u = CustomUser.objects.create_user(
        username=username, email=email, password=pwd,
        first_name=first, last_name=last,
        role='enseignant', must_change_password=False,
    )
    t = Teacher.objects.create(user=u, telephone=tel)
    teachers[username] = t
    print(f"   {username:15s} / {pwd}")

# ══════════════════════════════════════════════════════════════════
#  7. MATIÈRES
# ══════════════════════════════════════════════════════════════════
matieres_data = [
    # Maxima 60
    ('Mathématiques',           60),
    ('Français',                60),
    ('Biologie',                60),
    ('Chimie',                  60),
    ('Physique',                60),
    # Maxima 30
    ('Histoire-Géographie',     30),
    ('Éducation Civique',       30),
    ('Anglais',                 30),
    ('Sciences Commerciales',   30),
    ('Économie Politique',      30),
    # Maxima 20
    ('Éducation Physique',      20),
    ('Religion',                20),
    ('Dessin Technique',        20),
]
matieres = {}
for nom, maxima in matieres_data:
    matieres[nom] = Matiere.objects.create(nom=nom, maxima=maxima)
print(f"\n📖 {len(matieres)} matières créées")

# ══════════════════════════════════════════════════════════════════
#  8. AFFECTATIONS MATIÈRES → CLASSES
# ══════════════════════════════════════════════════════════════════
M = matieres
T = teachers

aff_data = {
    '4SC': [
        (M['Mathématiques'],        T['prof_math']),
        (M['Français'],             T['prof_fr']),
        (M['Biologie'],             T['prof_bio']),
        (M['Chimie'],               T['prof_chimie']),
        (M['Histoire-Géographie'],  T['prof_hist']),
        (M['Éducation Civique'],    T['prof_hist']),
        (M['Anglais'],              T['prof_angl']),
        (M['Éducation Physique'],   None),
        (M['Religion'],             None),
    ],
    '5SC': [
        (M['Mathématiques'],        T['prof_math']),
        (M['Français'],             T['prof_fr']),
        (M['Biologie'],             T['prof_bio']),
        (M['Chimie'],               T['prof_chimie']),
        (M['Physique'],             T['prof_phys']),
        (M['Histoire-Géographie'],  T['prof_hist']),
        (M['Anglais'],              T['prof_angl']),
        (M['Éducation Physique'],   None),
        (M['Religion'],             None),
    ],
    '6SC': [
        (M['Mathématiques'],        T['prof_math']),
        (M['Français'],             T['prof_fr']),
        (M['Biologie'],             T['prof_bio']),
        (M['Chimie'],               T['prof_chimie']),
        (M['Physique'],             T['prof_phys']),
        (M['Histoire-Géographie'],  T['prof_hist']),
        (M['Anglais'],              T['prof_angl']),
        (M['Éducation Physique'],   None),
        (M['Religion'],             None),
    ],
    '4LIT': [
        (M['Français'],             T['prof_fr']),
        (M['Histoire-Géographie'], T['prof_hist']),
        (M['Éducation Civique'],    T['prof_hist']),
        (M['Anglais'],              T['prof_angl']),
        (M['Mathématiques'],        T['prof_math']),
        (M['Biologie'],             T['prof_bio']),
        (M['Éducation Physique'],   None),
        (M['Religion'],             None),
    ],
    '5LIT': [
        (M['Français'],             T['prof_fr']),
        (M['Histoire-Géographie'], T['prof_hist']),
        (M['Éducation Civique'],    T['prof_hist']),
        (M['Anglais'],              T['prof_angl']),
        (M['Mathématiques'],        T['prof_math']),
        (M['Biologie'],             T['prof_bio']),
        (M['Éducation Physique'],   None),
        (M['Religion'],             None),
    ],
    '4CG': [
        (M['Mathématiques'],        T['prof_math']),
        (M['Français'],             T['prof_fr']),
        (M['Sciences Commerciales'],None),
        (M['Économie Politique'],   None),
        (M['Histoire-Géographie'],  T['prof_hist']),
        (M['Anglais'],              T['prof_angl']),
        (M['Éducation Civique'],    T['prof_hist']),
        (M['Éducation Physique'],   None),
        (M['Religion'],             None),
    ],
}

mc_map = {}
for cl_key, affectations in aff_data.items():
    cl = classes[cl_key]
    for mat, ens in affectations:
        mc = MatiereClasse.objects.create(matiere=mat, classe=cl, enseignant=ens)
        mc_map[(cl.pk, mat.pk)] = mc

print(f"🔗 {len(mc_map)} affectations matières-classes créées")

# ══════════════════════════════════════════════════════════════════
#  9. ÉLÈVES
# ══════════════════════════════════════════════════════════════════
eleves_data = [
    # ── 4ème Sciences (10 élèves)
    ('4SC','KASONGO',   'Trésor',    'Bienvenu', 'M','2008-03-15','Beni',       'CSP-4SC-001','Parent Kasongo','0978001001'),
    ('4SC','MWAMBA',    'Grâce',     'Esther',   'F','2008-07-22','Butembo',    'CSP-4SC-002','Parent Mwamba', '0978001002'),
    ('4SC','NTUMBA',    'Patrick',   'Luc',      'M','2007-11-05','Beni',       'CSP-4SC-003','Parent Ntumba', '0978001003'),
    ('4SC','ILUNGA',    'Patience',  'Marie',    'F','2008-01-30','Beni',       'CSP-4SC-004','Parent Ilunga', '0978001004'),
    ('4SC','KALALA',    'Joël',      'Émile',    'M','2009-05-10','Oicha',      'CSP-4SC-005','Parent Kalala', '0978001005'),
    ('4SC','MUKENDI',   'Espoir',    'Rachel',   'F','2008-09-14','Beni',       'CSP-4SC-006','Parent Mukendi','0978001006'),
    ('4SC','TSHISUAKA', 'Aaron',     'Daniel',   'M','2007-12-20','Beni',       'CSP-4SC-007','Parent Tshisuaka','0978001007'),
    ('4SC','BANZA',     'Joëlle',    'Ruth',     'F','2008-04-08','Butembo',    'CSP-4SC-008','Parent Banza',  '0978001008'),
    ('4SC','KAHINDO',   'Blaise',    'Emmanuel', 'M','2008-06-30','Beni',       'CSP-4SC-009','Parent Kahindo','0978001009'),
    ('4SC','KATEMBO',   'Précieuse', 'Joy',      'F','2008-11-11','Oicha',      'CSP-4SC-010','Parent Katembo','0978001010'),

    # ── 5ème Sciences (8 élèves)
    ('5SC','KABONGO',   'Emmanuel',  'Paul',     'M','2007-06-18','Beni',       'CSP-5SC-001','Parent Kabongo','0978002001'),
    ('5SC','NKASHAMA',  'Déborah',   'Anne',     'F','2007-02-25','Butembo',    'CSP-5SC-002','Parent Nkashama','0978002002'),
    ('5SC','MULUMBA',   'Samuel',    'Théo',     'M','2006-10-12','Beni',       'CSP-5SC-003','Parent Mulumba','0978002003'),
    ('5SC','KAYEMBE',   'Gloire',    'Élise',    'F','2007-08-03','Beni',       'CSP-5SC-004','Parent Kayembe','0978002004'),
    ('5SC','LUFUNGULA', 'Christophe','Marc',     'M','2007-01-27','Lubero',     'CSP-5SC-005','Parent Lufungula','0978002005'),
    ('5SC','KAPEND',    'Sandrine',  'Lydie',    'F','2006-11-09','Beni',       'CSP-5SC-006','Parent Kapend', '0978002006'),
    ('5SC','MUNGANGA',  'Rodrigue',  'Caleb',    'M','2007-04-15','Oicha',      'CSP-5SC-007','Parent Munganga','0978002007'),
    ('5SC','PALUKU',    'Micheline', 'Sara',     'F','2007-09-22','Butembo',    'CSP-5SC-008','Parent Paluku', '0978002008'),

    # ── 6ème Sciences (7 élèves)
    ('6SC','MBUYI',     'Bienvenu',  'Jonas',    'M','2005-03-22','Beni',       'CSP-6SC-001','Parent Mbuyi',  '0978003001'),
    ('6SC','KYUNGU',    'Aimée',     'Claire',   'F','2006-07-14','Butembo',    'CSP-6SC-002','Parent Kyungu', '0978003002'),
    ('6SC','MUTEBA',    'Didier',    'Pierre',   'M','2005-09-30','Beni',       'CSP-6SC-003','Parent Muteba', '0978003003'),
    ('6SC','LUPEMBA',   'Agnès',     'Noëlle',   'F','2005-12-05','Lubero',     'CSP-6SC-004','Parent Lupemba','0978003004'),
    ('6SC','TSHIBANGU', 'Cédric',    'Levi',     'M','2006-04-17','Beni',       'CSP-6SC-005','Parent Tshibangu','0978003005'),
    ('6SC','KABILA',    'Merveille', 'Joie',     'F','2005-08-09','Oicha',      'CSP-6SC-006','Parent Kabila', '0978003006'),
    ('6SC','NGOYI',     'Arsène',    'Benjamin', 'M','2006-01-03','Beni',       'CSP-6SC-007','Parent Ngoyi',  '0978003007'),

    # ── 4ème Littéraire (7 élèves)
    ('4LIT','NGANDU',   'Béatrice',  'Joie',     'F','2008-06-11','Beni',       'CSP-4LT-001','Parent Ngandu', '0978004001'),
    ('4LIT','KALONJI',  'Héritier',  'Abel',     'M','2008-02-19','Butembo',    'CSP-4LT-002','Parent Kalonji','0978004002'),
    ('4LIT','MUJINGA',  'Clarisse',  'Ève',      'F','2008-08-26','Beni',       'CSP-4LT-003','Parent Mujinga','0978004003'),
    ('4LIT','MBAYA',    'Josué',     'David',    'M','2007-10-07','Oicha',      'CSP-4LT-004','Parent Mbaya',  '0978004004'),
    ('4LIT','KAZADI',   'Princesse', 'Miriam',   'F','2008-05-23','Beni',       'CSP-4LT-005','Parent Kazadi', '0978004005'),
    ('4LIT','BWANA',    'Élie',      'Luc',      'M','2008-03-14','Lubero',     'CSP-4LT-006','Parent Bwana',  '0978004006'),
    ('4LIT','MASIKA',   'Grâce',     'Naomi',    'F','2008-09-01','Beni',       'CSP-4LT-007','Parent Masika', '0978004007'),

    # ── 5ème Littéraire (6 élèves)
    ('5LIT','MUHINDO',  'Isaac',     'Joseph',   'M','2007-02-08','Beni',       'CSP-5LT-001','Parent Muhindo','0978005001'),
    ('5LIT','KAMBALE',  'Dorcas',    'Esther',   'F','2006-11-17','Butembo',    'CSP-5LT-002','Parent Kambale','0978005002'),
    ('5LIT','VASIMWA',  'Barnabé',   'Amos',     'M','2007-05-29','Beni',       'CSP-5LT-003','Parent Vasimwa','0978005003'),
    ('5LIT','KIMANI',   'Fidèle',    'Lydia',    'F','2007-08-13','Oicha',      'CSP-5LT-004','Parent Kimani', '0978005004'),
    ('5LIT','BYAMUNGU', 'Raphaël',   'Simon',    'M','2006-12-22','Lubero',     'CSP-5LT-005','Parent Byamungu','0978005005'),
    ('5LIT','MAPENDO',  'Victoire',  'Ruth',     'F','2007-03-07','Beni',       'CSP-5LT-006','Parent Mapendo','0978005006'),

    # ── 4ème Commerciale & Gestion (6 élèves)
    ('4CG','MUSAU',     'Aristote',  'Caleb',    'M','2008-07-08','Beni',       'CSP-4CG-001','Parent Musau',  '0978006001'),
    ('4CG','TSHIMBA',   'Gloire',    'Hanna',    'F','2009-01-14','Butembo',    'CSP-4CG-002','Parent Tshimba','0978006002'),
    ('4CG','LIKAMBO',   'Jephté',    'Nathan',   'M','2008-04-25','Beni',       'CSP-4CG-003','Parent Likambo','0978006003'),
    ('4CG','FURAHA',    'Béni',      'Tabitha',  'F','2008-10-19','Oicha',      'CSP-4CG-004','Parent Furaha', '0978006004'),
    ('4CG','MUMBERE',   'Serge',     'Aaron',    'M','2009-02-28','Beni',       'CSP-4CG-005','Parent Mumbere','0978006005'),
    ('4CG','ZAWADI',    'Shalom',    'Priscille','F','2008-08-05','Lubero',     'CSP-4CG-006','Parent Zawadi', '0978006006'),
]

eleves = {}
for row in eleves_data:
    cl_key, nom, postnom, prenom, sexe, ddn, lieu, mat, parent, tel_parent = row
    s = Student.objects.create(
        nom=nom, postnom=postnom, prenom=prenom,
        sexe=sexe,
        date_naissance=datetime.date.fromisoformat(ddn),
        lieu_naissance=lieu,
        adresse=f'Quartier Bungulu, {lieu}',
        telephone='',
        nom_parent=parent,
        classe=classes[cl_key],
        matricule=mat,
        date_inscription=datetime.date(2024, 9, 2),
    )
    eleves[mat] = s

print(f"🎓 {len(eleves)} élèves créés")

# ══════════════════════════════════════════════════════════════════
#  10. MODÈLES DE BULLETINS
# ══════════════════════════════════════════════════════════════════
from bulletin.models import ModeleBulletin, ModeleBulletinMatiere

bulletins = {}
for cl_key, cl_obj in classes.items():
    mb = ModeleBulletin.objects.create(
        classe=cl_obj, annee_scolaire=annee, publie=True
    )
    bulletins[cl_key] = mb
    mcs = MatiereClasse.objects.filter(classe=cl_obj).select_related('matiere')
    for ordre, mc in enumerate(mcs.order_by('matiere__maxima', 'matiere__nom'), start=1):
        ModeleBulletinMatiere.objects.create(modele=mb, matiere=mc.matiere, ordre=ordre)

print(f"📋 {len(bulletins)} modèles de bulletins créés (publiés)")

# ══════════════════════════════════════════════════════════════════
#  11. NOTES — profils réalistes par élève
# ══════════════════════════════════════════════════════════════════
from grades.models import Note

PERIODES_NORMALES = ['1P', '2P', 'EXAM1', '3P', '4P', 'EXAM2']

def note_realiste(maxima, profil):
    """
    profil : 'excellent' | 'bon' | 'moyen' | 'faible'
    Pour EXAM, la valeur est divisée par 2 (maxima réel = maxima/2).
    """
    ranges = {
        60: {'excellent':(50,58),'bon':(40,52),'moyen':(30,43),'faible':(18,32)},
        30: {'excellent':(25,29),'bon':(20,27),'moyen':(15,23),'faible':(9,17)},
        20: {'excellent':(17,19),'bon':(14,18),'moyen':(11,15),'faible':(6,12)},
    }
    lo, hi = ranges[maxima][profil]
    return round(random.uniform(lo, hi), 1)

# Assigner un profil à chaque élève
PROFILS = ['excellent', 'excellent', 'bon', 'bon', 'bon', 'moyen', 'moyen', 'faible']
profil_eleve = {}
for mat_code in eleves:
    profil_eleve[mat_code] = random.choice(PROFILS)

notes_crees = 0
for mat_code, eleve in eleves.items():
    cl = eleve.classe
    profil = profil_eleve[mat_code]
    mcs = MatiereClasse.objects.filter(classe=cl).select_related('matiere')
    for mc in mcs:
        maxima = mc.matiere.maxima
        for periode in PERIODES_NORMALES:
            valeur = note_realiste(maxima, profil)
            if 'EXAM' in periode:
                # Pour les examens, la note est sur 2*maxima (double)
                valeur = valeur * 2
            Note.objects.create(
                eleve=eleve,
                matiere_classe=mc,
                periode=periode,
                valeur=Decimal(str(valeur)),
            )
            notes_crees += 1

        # REPÊCHAGE : uniquement pour les élèves faibles (simuler un échec)
        if profil == 'faible' and random.random() < 0.5:
            valeur_rep = note_realiste(maxima, 'moyen')
            Note.objects.create(
                eleve=eleve,
                matiere_classe=mc,
                periode='REPECHAGE',
                valeur=Decimal(str(valeur_rep)),
            )
            notes_crees += 1

print(f"📝 {notes_crees} notes créées (profils : excellent / bon / moyen / faible)")

# ══════════════════════════════════════════════════════════════════
#  12. PUBLICATIONS DES RÉSULTATS (portail parents)
# ══════════════════════════════════════════════════════════════════
from portail.models import PublicationResultats

periodes_publiees = ['1P', '2P', 'EXAM1', '3P', '4P']  # EXAM2 non encore publié
for cl_key, cl_obj in classes.items():
    for periode in periodes_publiees:
        pub = PublicationResultats.objects.create(
            classe=cl_obj,
            annee_scolaire=annee,
            periode=periode,
            publie=True,
            publie_par=prefet,
            date_publication=datetime.datetime(2025, 1, 15, 10, 0, 0,
                             tzinfo=datetime.timezone.utc),
        )

# EXAM2 créé mais NON publié (pour tester la restriction)
for cl_key, cl_obj in classes.items():
    PublicationResultats.objects.create(
        classe=cl_obj,
        annee_scolaire=annee,
        periode='EXAM2',
        publie=False,
    )

print(f"📢 Publications créées : 1P/2P/EXAM1/3P/4P publiées, EXAM2 non publiée")

# ══════════════════════════════════════════════════════════════════
#  13. PORTAIL PARENTS — accès activés pour quelques élèves
#  Note : le signal post_save crée automatiquement un PortailAcces
#  pour chaque élève. On met juste à jour les 5 premiers.
# ══════════════════════════════════════════════════════════════════
from portail.models import PortailAcces
from django.contrib.auth.hashers import make_password

code_test = '1234'
actives = 0
for mat_code in list(eleves.keys())[:5]:
    eleve = eleves[mat_code]
    acces = PortailAcces.objects.get(eleve=eleve)
    acces.code_acces_hash = make_password(code_test)
    acces.active = True
    acces.date_activation = datetime.datetime(2025, 1, 16, 8, 0, 0,
                            tzinfo=datetime.timezone.utc)
    acces.tentatives_echec = 0
    acces.bloque_jusqu = None
    acces.save()
    actives += 1

print(f"🔑 Portail : {actives} accès activés (code: {code_test}), {len(eleves)-actives} non activés")

# ══════════════════════════════════════════════════════════════════
#  RÉSUMÉ FINAL
# ══════════════════════════════════════════════════════════════════
print("\n" + "═"*55)
print("  ✅ SEEDING TERMINÉ AVEC SUCCÈS")
print("═"*55)
print("\n📌 COMPTES DE CONNEXION :")
print(f"  {'Rôle':<15} {'Username':<15} {'Mot de passe'}")
print(f"  {'-'*50}")
print(f"  {'Préfet':<15} {'prefet':<15} Prefet@2025")
for username, pwd, last, first, *_ in ens_data:
    print(f"  {'Enseignant':<15} {username:<15} {pwd}")
print("\n🌐 PORTAIL PARENTS :")
print(f"  Code d'accès des 5 premiers élèves : {code_test}")
print(f"  Périodes publiées : 1P, 2P, EXAM1, 3P, 4P")
print(f"  EXAM2 : créée mais non publiée (pour test)")
print("\n📊 STATISTIQUES :")
print(f"  Élèves   : {len(eleves)}")
print(f"  Classes  : {len(classes)}")
print(f"  Matières : {len(matieres)}")
print(f"  Notes    : {notes_crees}")
print("═"*55)
