from django import forms
from accounts.models import CustomUser
from .models import Teacher


class TeacherForm(forms.Form):
    first_name = forms.CharField(label='Prénom', max_length=100,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Nom', max_length=100,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    username = forms.CharField(label="Nom d'utilisateur", max_length=150,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=False,
                              widget=forms.EmailInput(attrs={'class': 'form-control'}))
    telephone = forms.CharField(label='Téléphone', max_length=20, required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Mot de passe', required=False,
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                help_text="Laisser vide pour ne pas changer")

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        if instance:
            self.fields['first_name'].initial = instance.user.first_name
            self.fields['last_name'].initial = instance.user.last_name
            self.fields['username'].initial = instance.user.username
            self.fields['email'].initial = instance.user.email
            self.fields['telephone'].initial = instance.telephone
            self.fields['password'].required = False

    def clean_username(self):
        username = self.cleaned_data['username']
        qs = CustomUser.objects.filter(username=username)
        if self.instance:
            qs = qs.exclude(pk=self.instance.user.pk)
        if qs.exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def save(self):
        data = self.cleaned_data
        if self.instance:
            user = self.instance.user
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.username = data['username']
            user.email = data['email']
            if data['password']:
                user.set_password(data['password'])
            user.save()
            self.instance.telephone = data['telephone']
            self.instance.save()
            return self.instance
        else:
            user = CustomUser.objects.create_user(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                password=data['password'] or 'django1234',
                role='enseignant'
            )
            teacher = Teacher.objects.create(user=user, telephone=data['telephone'])
            return teacher
