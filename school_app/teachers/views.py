from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Teacher
from .forms import TeacherForm
from accounts.views import prefet_required


@login_required
@prefet_required
def teacher_list(request):
    q = request.GET.get('q', '')
    teachers = Teacher.objects.select_related('user')
    if q:
        teachers = teachers.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q)
        )
    return render(request, 'teachers/teacher_list.html', {'teachers': teachers, 'q': q})


@login_required
@prefet_required
def teacher_create(request):
    form = TeacherForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        teacher, temp_password = form.save()
        return render(request, 'teachers/teacher_created.html', {
            'teacher': teacher,
            'temp_password': temp_password,
        })
    return render(request, 'teachers/teacher_form.html', {'form': form, 'titre': 'Ajouter un enseignant'})


@login_required
@prefet_required
def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, instance=teacher)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Enseignant modifié avec succès.")
        return redirect('teacher_list')
    return render(request, 'teachers/teacher_form.html', {'form': form, 'titre': 'Modifier un enseignant', 'obj': teacher})


@login_required
@prefet_required
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, "Enseignant supprimé.")
        return redirect('teacher_list')
    return render(request, 'teachers/teacher_confirm_delete.html', {'obj': teacher})


@login_required
def teacher_detail(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    return render(request, 'teachers/teacher_detail.html', {'teacher': teacher})
