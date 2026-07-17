from django import forms
from .models import Matiere, MatiereClasse


class MatiereForm(forms.ModelForm):
    class Meta:
        model = Matiere
        fields = ['nom', 'maxima']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'maxima': forms.Select(attrs={'class': 'form-select'}),
        }


class MatiereClasseForm(forms.ModelForm):
    class Meta:
        model = MatiereClasse
        fields = ['matiere', 'classe', 'enseignant']
        widgets = {
            'matiere': forms.Select(attrs={'class': 'form-select'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from classes.models import Classe, AnneeScolaire
        annee = AnneeScolaire.objects.filter(active=True).first()
        if annee:
            self.fields['classe'].queryset = Classe.objects.filter(
                annee_scolaire=annee
            ).select_related('section')
        self.fields['enseignant'].required = False
