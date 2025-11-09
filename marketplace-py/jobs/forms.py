from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import JobFunding, JobApplication


class JobFundingForm(forms.ModelForm):
    """Collects pledges for a job budget."""
    
    def __init__(self, *args, job=None, **kwargs):
        self.job = job
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = JobFunding
        fields = ['amount', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount is None:
            raise forms.ValidationError(_('Amount is required.'))
        if amount <= Decimal('0'):
            raise forms.ValidationError(_('Amount must be greater than zero.'))
        
        if self.job:
            remaining = self.job.remaining_budget()
            if remaining <= Decimal('0'):
                raise forms.ValidationError(_('This job is already fully funded.'))
            if amount > remaining:
                raise forms.ValidationError(
                    _('Only %(remaining)s ILP is still needed for this job.'),
                    params={'remaining': remaining}
                )
        return amount


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
