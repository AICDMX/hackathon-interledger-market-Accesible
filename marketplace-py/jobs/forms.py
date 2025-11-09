from django import forms
from django.utils.translation import gettext_lazy as _

from .models import JobApplication


class JobApplicationForm(forms.ModelForm):
    """Form for workers to submit their profile/application for a job."""
    
    class Meta:
        model = JobApplication
        fields = ['profile_note', 'profile_audio', 'profile_video', 'profile_image']
        widgets = {
            'profile_note': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': _('Tell the job owner about yourself and why you are interested in this job...')
            }),
        }
