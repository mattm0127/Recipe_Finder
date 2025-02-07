from django import forms
from django.contrib.auth.forms import UserCreationForm
from . import models

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        help_text='This is required incase you forget your password.'
        )

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

class IngredientInputForm(forms.Form):
    ingredients = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'cols': 50}))


