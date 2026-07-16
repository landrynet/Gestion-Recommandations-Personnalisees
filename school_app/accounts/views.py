from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser
from .forms import LoginForm, UserCreateForm, UserUpdateForm
from teachers.models import Teacher


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


def prefet_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_prefet():
            messages.error(request, "Accès réservé au Préfet des études.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@prefet_required
def user_list(request):
    users = CustomUser.objects.all().order_by('last_name', 'first_name')
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
@prefet_required
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        if user.role == 'enseignant':
            Teacher.objects.get_or_create(user=user)
        messages.success(request, f"Utilisateur « {user.get_full_name() or user.username} » créé avec succès.")
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'titre': 'Créer un utilisateur'})


@login_required
@prefet_required
def user_update(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if form.is_valid():
        form.save()
        messages.success(request, "Utilisateur modifié avec succès.")
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'titre': 'Modifier un utilisateur', 'obj': user})


@login_required
@prefet_required
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Utilisateur supprimé.")
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'obj': user})
