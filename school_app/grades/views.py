import json
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST

from .models import Note
from .forms import NoteForm
from subjects.models import MatiereClasse
from students.models import Student
from classes.models import Classe
from school_settings.models import SchoolInfo


# ─── Saisie des notes ─────────────────────────────────────────────────────────
@login_required
def saisie_notes(request):
    """Saisie des notes — enseignant (ses classes), préfet interdit ici."""
    user = request.user

    if user.is_prefet():
        messages.info(request, "La saisie des notes est réservée aux enseignants.")
        return redirect('consulter_notes')

    periodes = [
        ('1P',        '1ère Période'),
        ('2P',        '2ème Période'),
        ('EXAM1',     'Examen S1'),
        ('3P',        '3ème Période'),
        ('4P',        '4ème Période'),
        ('EXAM2',     'Examen S2'),
        ('REPECHAGE', 'Repêchage'),
    ]

    try:
        teacher = user.teacher_profile
        matieres_classes = MatiereClasse.objects.filter(
            enseignant=teacher
        ).select_related('matiere', 'classe', 'classe__section')
    except Exception:
        matieres_classes = MatiereClasse.objects.none()

    mc_id          = request.GET.get('mc', '')
    periode        = request.GET.get('periode', '1P')
    matiere_classe = None
    eleves         = []
    form           = None

    if mc_id:
        matiere_classe = get_object_or_404(MatiereClasse, pk=mc_id)
        try:
            if matiere_classe.enseignant != user.teacher_profile:
                messages.error(request, "Vous ne pouvez modifier que vos propres matières.")
                return redirect('saisie_notes')
        except Exception:
            messages.error(request, "Profil enseignant introuvable.")
            return redirect('dashboard')

        eleves = Student.objects.filter(classe=matiere_classe.classe).order_by('nom', 'postnom')

        if request.method == 'POST':
            form = NoteForm(request.POST, eleves=eleves, matiere_classe=matiere_classe, periode=periode)
            if form.is_valid():
                form.save()
                messages.success(request, f"Notes enregistrées — {matiere_classe.matiere} / {periode}.")
                return redirect(f'/notes/?mc={mc_id}&periode={periode}')
        else:
            form = NoteForm(eleves=eleves, matiere_classe=matiere_classe, periode=periode)

    return render(request, 'grades/saisie_notes.html', {
        'matieres_classes': matieres_classes,
        'mc_id':            mc_id,
        'periodes':         periodes,
        'periode':          periode,
        'matiere_classe':   matiere_classe,
        'eleves':           eleves,
        'form':             form,
    })


# ─── Auto-save AJAX ───────────────────────────────────────────────────────────
@login_required
@require_POST
def autosave_note(request):
    """Sauvegarde automatique d'une note individuelle via AJAX."""
    try:
        mc_id    = request.POST.get('mc_id')
        eleve_id = request.POST.get('eleve_id')
        periode  = request.POST.get('periode')
        valeur   = request.POST.get('valeur', '').strip()

        if not all([mc_id, eleve_id, periode]):
            return JsonResponse({'success': False, 'error': 'Données manquantes'}, status=400)

        mc    = get_object_or_404(MatiereClasse, pk=mc_id)
        eleve = get_object_or_404(Student, pk=eleve_id)

        # Vérification sécurité : l'enseignant ne peut sauver que ses matières
        user = request.user
        if not user.is_prefet():
            try:
                if mc.enseignant != user.teacher_profile:
                    return JsonResponse({'success': False, 'error': 'Non autorisé'}, status=403)
            except Exception:
                return JsonResponse({'success': False, 'error': 'Profil introuvable'}, status=403)

        # Calcul du maxima selon la période
        max_val = mc.matiere.maxima * (2 if periode in ('EXAM1', 'EXAM2') else 1)

        if valeur == '' or valeur is None:
            # Supprimer la note si le champ est vidé
            Note.objects.filter(eleve=eleve, matiere_classe=mc, periode=periode).delete()
            return JsonResponse({'success': True, 'action': 'deleted'})

        try:
            val_decimal = Decimal(valeur.replace(',', '.'))
        except InvalidOperation:
            return JsonResponse({'success': False, 'error': 'Valeur invalide'}, status=400)

        if val_decimal < 0 or val_decimal > max_val:
            return JsonResponse({
                'success': False,
                'error': f'La note doit être entre 0 et {max_val}'
            }, status=400)

        Note.objects.update_or_create(
            eleve=eleve,
            matiere_classe=mc,
            periode=periode,
            defaults={'valeur': val_decimal}
        )
        return JsonResponse({'success': True, 'action': 'saved', 'valeur': str(val_decimal)})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ─── Consultation des notes ───────────────────────────────────────────────────
@login_required
def consulter_notes(request):
    """Consultation des notes — préfet voit tout, enseignant voit ses classes."""
    user = request.user
    periodes = [
        ('1P', '1ère P'), ('2P', '2ème P'), ('EXAM1', 'Exam S1'),
        ('3P', '3ème P'), ('4P', '4ème P'), ('EXAM2', 'Exam S2'),
        ('REPECHAGE', 'Repêchage'),
    ]

    if user.is_prefet():
        classes = Classe.objects.select_related('section', 'annee_scolaire')
    else:
        try:
            teacher = user.teacher_profile
            mc_qs   = MatiereClasse.objects.filter(enseignant=teacher).values_list('classe_id', flat=True)
            classes = Classe.objects.filter(pk__in=mc_qs).select_related('section')
        except Exception:
            classes = Classe.objects.none()

    classe_id        = request.GET.get('classe', '')
    mc_id            = request.GET.get('mc', '')
    matieres_classes = []
    eleves_notes     = []
    selected_mc      = None

    if classe_id:
        if user.is_prefet():
            matieres_classes = MatiereClasse.objects.filter(
                classe_id=classe_id
            ).select_related('matiere', 'enseignant', 'enseignant__user').order_by('matiere__maxima', 'matiere__nom')
        else:
            try:
                matieres_classes = MatiereClasse.objects.filter(
                    classe_id=classe_id, enseignant=user.teacher_profile
                ).select_related('matiere', 'enseignant', 'enseignant__user')
            except Exception:
                matieres_classes = []

    if mc_id:
        selected_mc = get_object_or_404(MatiereClasse, pk=mc_id)
        eleves = Student.objects.filter(classe=selected_mc.classe).order_by('nom', 'postnom')
        for eleve in eleves:
            row = {'eleve': eleve, 'notes': {}}
            for code, label in periodes:
                try:
                    n = Note.objects.get(eleve=eleve, matiere_classe=selected_mc, periode=code)
                    row['notes'][code] = n.valeur
                except Note.DoesNotExist:
                    row['notes'][code] = None
            eleves_notes.append(row)

    return render(request, 'grades/consulter_notes.html', {
        'classes':          classes,
        'classe_id':        classe_id,
        'mc_id':            mc_id,
        'matieres_classes': matieres_classes,
        'selected_mc':      selected_mc,
        'eleves_notes':     eleves_notes,
        'periodes':         periodes,
    })


# ─── Export Excel ─────────────────────────────────────────────────────────────
@login_required
def export_notes_excel(request):
    """Exporte un fichier Excel vierge (ou pré-rempli) pour saisie hors-ligne."""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side, numbers
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        messages.error(request, "Module openpyxl manquant. Contactez l'administrateur.")
        return redirect('saisie_notes')

    mc_id   = request.GET.get('mc', '')
    periodes_sel = request.GET.getlist('periodes')

    if not mc_id:
        messages.error(request, "Veuillez sélectionner une matière/classe.")
        return redirect('saisie_notes')

    mc = get_object_or_404(MatiereClasse, pk=mc_id)

    # Sécurité
    if not request.user.is_prefet():
        try:
            if mc.enseignant != request.user.teacher_profile:
                messages.error(request, "Non autorisé.")
                return redirect('saisie_notes')
        except Exception:
            return redirect('saisie_notes')

    all_periodes = [
        ('1P', '1ère Période'),  ('2P', '2ème Période'),
        ('EXAM1', 'Examen S1'),  ('3P', '3ème Période'),
        ('4P', '4ème Période'),  ('EXAM2', 'Examen S2'),
        ('REPECHAGE', 'Repêchage'),
    ]
    if periodes_sel:
        periodes = [(c, l) for c, l in all_periodes if c in periodes_sel]
    else:
        periodes = all_periodes

    eleves = Student.objects.filter(classe=mc.classe).order_by('nom', 'postnom')
    school = SchoolInfo.get_info()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f"{mc.matiere.nom[:20]}"

    # ── Styles ──
    hdr_font    = Font(bold=True, size=11)
    title_font  = Font(bold=True, size=13)
    center      = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left        = Alignment(horizontal='left', vertical='center')
    fill_header = PatternFill('solid', fgColor='1565C0')
    fill_sub    = PatternFill('solid', fgColor='CFD8DC')
    fill_max    = PatternFill('solid', fgColor='ECEFF1')
    white_font  = Font(bold=True, color='FFFFFF', size=10)
    thin        = Side(style='thin', color='888888')
    border      = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ── En-tête école ──
    ws.merge_cells('A1:A3')
    ws['A1'] = 'REPUBLIQUE DEMOCRATIQUE DU CONGO'
    ws['A1'].font = Font(bold=True, size=10)
    ws['A1'].alignment = center

    ws.merge_cells(f'B1:{get_column_letter(4 + len(periodes))}3')
    school_nom = school.nom if school else 'ÉCOLE'
    school_ann = f"Année scolaire : {mc.classe.annee_scolaire}" if hasattr(mc.classe, 'annee_scolaire') and mc.classe.annee_scolaire else ''
    ws[f'B1'] = f"{school_nom}\n{school_ann}\nFEUILLE DE NOTES — {mc.matiere.nom} — {mc.classe}"
    ws[f'B1'].font = title_font
    ws[f'B1'].alignment = center
    ws.row_dimensions[1].height = 50
    ws.row_dimensions[2].height = 15
    ws.row_dimensions[3].height = 15

    # ── Info matière ──
    row = 4
    ws.merge_cells(f'A{row}:{get_column_letter(4 + len(periodes))}{row}')
    max_normal = mc.matiere.maxima
    ws[f'A{row}'] = (
        f"Matière : {mc.matiere.nom}  |  Classe : {mc.classe}  |  "
        f"Maxima période normale : {max_normal}  |  Maxima examen : {max_normal * 2}  |  "
        f"NE PAS modifier les colonnes N°, Matricule, Nom"
    )
    ws[f'A{row}'].font = Font(italic=True, size=9, color='555555')
    ws[f'A{row}'].alignment = left
    ws.row_dimensions[row].height = 18

    # ── Métadonnées cachées pour import ──
    row = 5
    ws[f'A{row}'] = 'META_MC_ID'
    ws[f'B{row}'] = mc.pk
    ws[f'A{row}'].font = Font(color='FFFFFF')
    ws[f'B{row}'].font = Font(color='FFFFFF')

    # ── En-têtes colonnes ──
    row = 6
    headers = ['N°', 'Matricule', 'Nom', 'Postnom'] + [label for _, label in periodes]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = white_font
        cell.fill = fill_header
        cell.alignment = center
        cell.border = border
    ws.row_dimensions[row].height = 30

    # ── Largeurs colonnes ──
    ws.column_dimensions['A'].width = 5
    ws.column_dimensions['B'].width = 14
    ws.column_dimensions['C'].width = 18
    ws.column_dimensions['D'].width = 18
    for i in range(len(periodes)):
        ws.column_dimensions[get_column_letter(5 + i)].width = 13

    # ── Ligne MAXIMA ──
    row = 7
    mx_row = ['', '', 'MAXIMA', '']
    for code, _ in periodes:
        max_v = max_normal * 2 if code in ('EXAM1', 'EXAM2') else max_normal
        mx_row.append(max_v)
    for col, val in enumerate(mx_row, 1):
        cell = ws.cell(row=row, column=col, value=val)
        cell.fill = fill_max
        cell.font = Font(bold=True, size=9)
        cell.alignment = center
        cell.border = border
    ws.row_dimensions[row].height = 18

    # ── Données élèves ──
    first_data_row = 8
    for i, eleve in enumerate(eleves):
        row = first_data_row + i
        ws.cell(row=row, column=1, value=i + 1).alignment = center
        ws.cell(row=row, column=2, value=eleve.matricule).font = Font(size=9)
        ws.cell(row=row, column=3, value=eleve.nom).font = Font(bold=True, size=9)
        ws.cell(row=row, column=4, value=eleve.postnom).font = Font(size=9)

        for col_i, (code, _) in enumerate(periodes):
            col = 5 + col_i
            max_v = max_normal * 2 if code in ('EXAM1', 'EXAM2') else max_normal
            # Pré-remplir avec la note existante
            try:
                note = Note.objects.get(eleve=eleve, matiere_classe=mc, periode=code)
                val = float(note.valeur)
            except Note.DoesNotExist:
                val = None

            cell = ws.cell(row=row, column=col, value=val)
            cell.alignment = center
            cell.border = border
            cell.font = Font(size=10)

            # Validation des données (0 ≤ note ≤ maxima)
            dv = DataValidation(
                type='decimal',
                operator='between',
                formula1='0',
                formula2=str(max_v),
                showErrorMessage=True,
                errorTitle='Note invalide',
                error=f'La note doit être entre 0 et {max_v}',
            )
            ws.add_data_validation(dv)
            dv.add(cell)

        # Protéger les colonnes fixes (N°, Matricule, Nom) visuellement
        for col in [1, 2, 3, 4]:
            ws.cell(row=row, column=col).fill = fill_max
            ws.cell(row=row, column=col).border = border
        ws.row_dimensions[row].height = 18

    # ── Figer les volets ──
    ws.freeze_panes = ws.cell(row=first_data_row, column=5)

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"notes_{mc.matiere.nom}_{mc.classe}_{'-'.join(c for c, _ in periodes)}.xlsx"
    filename = filename.replace(' ', '_').replace('/', '-')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response


# ─── Import Excel — Upload ────────────────────────────────────────────────────
@login_required
def import_notes_excel(request):
    """Étape 1 : upload du fichier Excel exporté."""
    user = request.user
    try:
        teacher = user.teacher_profile
        matieres_classes = MatiereClasse.objects.filter(
            enseignant=teacher
        ).select_related('matiere', 'classe') if not user.is_prefet() else MatiereClasse.objects.select_related('matiere', 'classe')
    except Exception:
        matieres_classes = MatiereClasse.objects.none()

    if user.is_prefet():
        matieres_classes = MatiereClasse.objects.select_related('matiere', 'classe', 'classe__section').order_by('classe__nom', 'matiere__nom')

    if request.method == 'POST' and request.FILES.get('fichier_excel'):
        import openpyxl, io
        fichier = request.FILES['fichier_excel']
        try:
            wb = openpyxl.load_workbook(io.BytesIO(fichier.read()), data_only=True)
            ws = wb.active

            # Lire métadonnées
            mc_id = ws['B5'].value
            if not mc_id:
                messages.error(request, "Fichier invalide : métadonnées manquantes. Utilisez uniquement les fichiers exportés depuis ce système.")
                return redirect('import_notes_excel')

            mc = get_object_or_404(MatiereClasse, pk=mc_id)

            # Sécurité
            if not user.is_prefet():
                try:
                    if mc.enseignant != user.teacher_profile:
                        messages.error(request, "Ce fichier ne vous appartient pas.")
                        return redirect('import_notes_excel')
                except Exception:
                    return redirect('import_notes_excel')

            # Lire en-têtes (ligne 6) pour détecter les périodes
            header_row = list(ws.iter_rows(min_row=6, max_row=6, values_only=True))[0]
            periode_labels = {
                '1ère Période': '1P', '2ème Période': '2P', 'Examen S1': 'EXAM1',
                '3ème Période': '3P', '4ème Période': '4P', 'Examen S2': 'EXAM2',
                'Repêchage': 'REPECHAGE',
            }
            # Colonnes des périodes (index 4+)
            periode_cols = []
            for col_i, h in enumerate(header_row[4:], 4):
                if h and h in periode_labels:
                    periode_cols.append((col_i, periode_labels[h], h))

            # Lire données (à partir de ligne 8, ligne 7 = MAXIMA)
            all_periodes = [
                ('1P', '1ère P'), ('2P', '2ème P'), ('EXAM1', 'Exam S1'),
                ('3P', '3ème P'), ('4P', '4ème P'), ('EXAM2', 'Exam S2'),
                ('REPECHAGE', 'Repêchage'),
            ]
            eleves = Student.objects.filter(classe=mc.classe).order_by('nom', 'postnom')
            eleve_map = {e.matricule: e for e in eleves}

            preview_data = []
            errors = []

            for row in ws.iter_rows(min_row=8, values_only=True):
                if not row[1]:  # Matricule vide = fin du tableau
                    break
                matricule = str(row[1]).strip()
                eleve = eleve_map.get(matricule)
                if not eleve:
                    errors.append(f"Matricule inconnu : {matricule}")
                    continue

                changes = []
                for col_i, code, label in periode_cols:
                    max_v = mc.matiere.maxima * (2 if code in ('EXAM1', 'EXAM2') else 1)
                    new_val = row[col_i]
                    if new_val is not None:
                        try:
                            new_dec = Decimal(str(new_val)).quantize(Decimal('0.01'))
                        except Exception:
                            errors.append(f"{eleve.nom_complet} / {label} : valeur invalide '{new_val}'")
                            continue
                        if new_dec < 0 or new_dec > max_v:
                            errors.append(f"{eleve.nom_complet} / {label} : {new_dec} hors limites (0-{max_v})")
                            continue
                    else:
                        new_dec = None

                    # Valeur actuelle en base
                    try:
                        existing = Note.objects.get(eleve=eleve, matiere_classe=mc, periode=code)
                        old_dec = existing.valeur
                    except Note.DoesNotExist:
                        old_dec = None

                    changed = (new_dec != old_dec)
                    changes.append({
                        'periode': code, 'label': label,
                        'avant': old_dec, 'apres': new_dec,
                        'changed': changed,
                    })

                preview_data.append({
                    'eleve': eleve,
                    'changes': changes,
                    'has_changes': any(c['changed'] for c in changes),
                })

            if errors:
                for err in errors[:5]:
                    messages.warning(request, err)

            # Stocker en session pour confirmation
            session_data = []
            for row in preview_data:
                session_data.append({
                    'eleve_id': row['eleve'].pk,
                    'eleve_nom': row['eleve'].nom_complet,
                    'changes': [
                        {
                            'periode': c['periode'], 'label': c['label'],
                            'avant': str(c['avant']) if c['avant'] is not None else None,
                            'apres': str(c['apres']) if c['apres'] is not None else None,
                            'changed': c['changed'],
                        }
                        for c in row['changes']
                    ],
                    'has_changes': row['has_changes'],
                })
            request.session['import_preview'] = session_data
            request.session['import_mc_id']   = mc.pk

            return render(request, 'grades/import_preview.html', {
                'mc': mc,
                'preview_data': preview_data,
                'errors': errors,
                'nb_changes': sum(1 for r in preview_data if r['has_changes']),
            })

        except Exception as e:
            messages.error(request, f"Erreur lecture fichier : {e}")
            return redirect('import_notes_excel')

    return render(request, 'grades/import_notes.html', {'matieres_classes': matieres_classes})


# ─── Import Excel — Confirmation ──────────────────────────────────────────────
@login_required
@require_POST
def import_notes_preview(request):
    """Étape 2 : confirmation et enregistrement des notes importées."""
    session_data = request.session.get('import_preview')
    mc_id        = request.session.get('import_mc_id')

    if not session_data or not mc_id:
        messages.error(request, "Session expirée. Veuillez réimporter le fichier.")
        return redirect('import_notes_excel')

    mc = get_object_or_404(MatiereClasse, pk=mc_id)

    # Sécurité
    user = request.user
    if not user.is_prefet():
        try:
            if mc.enseignant != user.teacher_profile:
                messages.error(request, "Non autorisé.")
                return redirect('saisie_notes')
        except Exception:
            return redirect('saisie_notes')

    nb_saved = 0
    for row in session_data:
        if not row['has_changes']:
            continue
        eleve = get_object_or_404(Student, pk=row['eleve_id'])
        for change in row['changes']:
            if not change['changed']:
                continue
            new_val = change['apres']
            if new_val is None:
                Note.objects.filter(eleve=eleve, matiere_classe=mc, periode=change['periode']).delete()
            else:
                Note.objects.update_or_create(
                    eleve=eleve, matiere_classe=mc, periode=change['periode'],
                    defaults={'valeur': Decimal(new_val)}
                )
            nb_saved += 1

    # Nettoyer la session
    del request.session['import_preview']
    del request.session['import_mc_id']

    messages.success(request, f"{nb_saved} note(s) importée(s) avec succès pour {mc.matiere} — {mc.classe}.")
    return redirect(f'/notes/?mc={mc.pk}&periode=1P')
