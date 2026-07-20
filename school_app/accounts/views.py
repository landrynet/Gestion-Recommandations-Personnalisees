import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from notifications.service import notify
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import CustomUser, generate_temp_password
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm,
    ForcePasswordChangeForm, ProfileForm, ChangePasswordForm,
)
from teachers.models import Teacher

logger_sec = logging.getLogger('sgn.security')
logger     = logging.getLogger('sgn')


# ─── Authentification ─────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.must_change_password:
            return redirect('force_change_password')
        return redirect('dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '?'))
            logger_sec.info(
                "CONNEXION user=%s role=%s ip=%s",
                user.username, user.role, ip,
            )
            if user.must_change_password:
                return redirect('force_change_password')
            return redirect('dashboard')
        else:
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '?'))
            identifier = request.POST.get('username', '')
            logger_sec.warning("ECHEC_CONNEXION identifier=%s ip=%s", identifier, ip)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        logger_sec.info("DECONNEXION user=%s", request.user.username)
    logout(request)
    return redirect('login')


# ─── Changement de mot de passe forcé (première connexion) ───────────────────

@login_required
def force_change_password(request):
    if not request.user.must_change_password:
        return redirect('dashboard')

    form = ForcePasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        request.user.set_password(form.cleaned_data['new_password'])
        request.user.must_change_password = False
        request.user.save(update_fields=['password', 'must_change_password'])
        update_session_auth_hash(request, request.user)
        messages.success(request, "Mot de passe mis à jour. Bienvenue !")
        return redirect('dashboard')

    return render(request, 'accounts/force_password_change.html', {'form': form, 'hide_sidebar': True})


# ─── Décorateurs de rôle ──────────────────────────────────────────────────────

def prefet_required(view_func):
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


# ─── Profil utilisateur ───────────────────────────────────────────────────────

@login_required
def profile_view(request):
    """Chaque utilisateur peut consulter et modifier son propre profil."""
    user = request.user
    profile_form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=user,
    )
    password_form = ChangePasswordForm(user=user, data=None)

    # Chargement de l'onglet actif depuis le paramètre
    active_tab = request.POST.get('_tab', 'info') or request.GET.get('tab', 'info')

    if request.method == 'POST':
        action = request.POST.get('_action', 'profile')

        if action == 'profile':
            active_tab = 'info'
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profil mis à jour avec succès.")
                return redirect('profile_view')
            else:
                messages.error(request, "Veuillez corriger les erreurs ci-dessous.")

        elif action == 'password':
            active_tab = 'password'
            password_form = ChangePasswordForm(user=user, data=request.POST)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data['new_password'])
                user.save(update_fields=['password'])
                update_session_auth_hash(request, user)
                notify(
                    request.user,
                    "Mot de passe modifié",
                    "Votre mot de passe a été changé avec succès.",
                    categorie='ADMIN', priorite='SUCCES', type_notif='MDP_CHANGE',
                    lien='/login/profile/',
                )
                messages.success(request, "Mot de passe modifié avec succès.")
                return redirect('profile_view')
            else:
                messages.error(request, "Veuillez corriger les erreurs du formulaire.")

    # Infos supplémentaires pour l'enseignant
    teacher_profile = None
    if user.is_enseignant():
        try:
            teacher_profile = user.teacher_profile
        except Teacher.DoesNotExist:
            pass

    return render(request, 'accounts/profile.html', {
        'profile_form':   profile_form,
        'password_form':  password_form,
        'teacher_profile': teacher_profile,
        'active_tab':     active_tab,
    })


# ─── Gestion des utilisateurs (préfet) ───────────────────────────────────────

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
        # Notification au nouvel utilisateur
        notify(
            user,
            "Bienvenue sur SGN — votre compte a été créé",
            f"Votre compte ({user.get_role_display()}) a été créé par le préfet. "
            "Connectez-vous avec votre mot de passe temporaire et changez-le immédiatement.",
            categorie='ADMIN', priorite='IMPORTANT', type_notif='COMPTE_CREE',
            lien='/login/profile/', expediteur=request.user,
        )
        return render(request, 'accounts/user_created.html', {
            'target_user': user,
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
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        temp_password = generate_temp_password()
        user.set_password(temp_password)
        user.must_change_password = True
        user.save(update_fields=['password', 'must_change_password'])
        # Notification à l'utilisateur concerné
        notify(
            user,
            "Votre mot de passe a été réinitialisé",
            "Un préfet a réinitialisé votre mot de passe. Connectez-vous avec le nouveau mot de passe temporaire et changez-le immédiatement.",
            categorie='ADMIN', priorite='CRITIQUE', type_notif='MDP_REINIT',
            lien='/login/profile/', expediteur=request.user,
        )
        return render(request, 'accounts/user_created.html', {
            'target_user': user,
            'temp_password': temp_password,
            'is_reset': True,
        })
    return render(request, 'accounts/reset_confirm.html', {'obj': user})
