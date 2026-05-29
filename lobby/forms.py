from django import forms
from .models import Perfil
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegistroForm(UserCreationForm):
    
    email = forms.EmailField(required=True, help_text='Obrigatório para recuperação de senha')

    class Meta:
        model = User
        fields = ['username', 'email'] 

class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['foto', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Conte um pouco sobre você...'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }

