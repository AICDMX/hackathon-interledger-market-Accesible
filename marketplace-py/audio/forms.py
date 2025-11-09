from django import forms
from django.utils.translation import gettext_lazy as _
from .models import AudioContribution


class AudioContributionForm(forms.ModelForm):
    """Public-facing upload form for community audio contributions."""

    class Meta:
        model = AudioContribution
        fields = ['language_code', 'file', 'notes']
        widgets = {
            'language_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej. es, nah, oto')
            }),
            'notes': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': _('Describe el contexto de tu audio (opcional)')
            }),
        }
        labels = {
            'language_code': _('Idioma del audio'),
            'file': _('Archivo de audio'),
            'notes': _('Notas para el equipo'),
        }

    def __init__(self, *args, hide_language=False, **kwargs):
        """Initialize form, optionally hiding the language field."""
        super().__init__(*args, **kwargs)
        if hide_language:
            # Remove language_code from fields if it should be hidden
            if 'language_code' in self.fields:
                del self.fields['language_code']

    file = forms.FileField(
        label=_('Archivo de audio'),
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'audio/*'}),
    )
