from django import forms
from .models import AnneeScolaire, Section, Classe


class AnneeScolaireForm(forms.ModelForm):
    class Meta:
        model = AnneeScolaire
        fields = ['annee', 'active']
        widgets = {
            'annee': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2024-2025'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: Générale, Commerciale'}),
        }


class ClasseForm(forms.ModelForm):
    class Meta:
        model = Classe
        fields = ['nom', 'section', 'annee_scolaire']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ex: 7ème, 8ème, 1ère'}),
            'section': forms.Select(attrs={'class': 'form-select'}),
            'annee_scolaire': forms.Select(attrs={'class': 'form-select'}),
        }
