from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import CustomUser, generate_temp_password
from .forms import LoginForm, UserCreateForm, UserUpdateForm, ForcePasswordChangeForm
from teachers.models import Teacher


# ─── Authentification ─────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.must_change_password:
            return redirect('force_change_password')
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        if user.must_change_password:
            return redirect('force_change_password')
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Changement de mot de passe forcé (première connexion) ───────────────────

@login_required
def force_change_password(request):
    """Obligatoire avant tout accès si must_change_password est True."""
    if not request.user.must_change_password:
        return redirect('dashboard')

    form = ForcePasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.must_change_password = False
        request.user.save(update_fields=['password', 'must_change_password'])
        update_session_auth_hash(request, request.user)   # Maintient la session active
        messages.success(request, "Mot de passe mis à jour. Bienvenue !")
        return redirect('dashboard')

    return render(request, 'accounts/force_password_change.html', {'form': form})


# ─── Décorateurs de rôle ──────────────────────────────────────────────────────

def prefet_required(view_func):
    """Réservé au Préfet des études uniquement."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.must_change_password:
            return redirect('force_change_password')
        if not request.user.is_prefet():
            messages.error(request, "Accès réservé au Préfet des études.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def enseignant_only(view_func):
    """Réservé aux enseignants uniquement (bloque le préfet)."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.must_change_password:
            return redirect('force_change_password')
        if request.user.is_prefet():
            messages.error(request, "Cette section est réservée aux enseignants.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Gestion des utilisateurs ─────────────────────────────────────────────────

@login_required
@prefet_required
def user_list(request):
    users = CustomUser.objects.all().order_by('role', 'last_name', 'first_name')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@prefet_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        user, temp_password = form.save()
        if user.role == 'enseignant':
            Teacher.objects.get_or_create(user=user)
        return render(request, 'accounts/user_created.html', {
            'user': user,
            'temp_password': temp_password,
            'is_reset': False,
        })
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'titre': 'Créer un utilisateur',
    })


@login_required
@prefet_required
def user_update(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        messages.success(request, "Utilisateur modifié avec succès.")
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {
        'form': form,
        'titre': 'Modifier un utilisateur',
        'obj': user,
    })


@login_required
@prefet_required
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Utilisateur supprimé.")
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'obj': user})


@login_required
@prefet_required
def reset_user_password(request, pk):
    """Le préfet réinitialise le mot de passe d'un utilisateur → nouveau mot de passe temporaire."""
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        temp_password = generate_temp_password()
        user.set_password(temp_password)
        user.must_change_password = True
        user.save(update_fields=['password', 'must_change_password'])
        return render(request, 'accounts/user_created.html', {
            'user': user,
            'temp_password': temp_password,
            'is_reset': True,
        })
    return render(request, 'accounts/reset_confirm.html', {'obj': user})
