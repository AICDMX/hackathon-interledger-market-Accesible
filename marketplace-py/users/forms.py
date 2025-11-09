from django import forms
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from .models import User


class ProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your.email@example.com')
        })
    )
    
    wallet_endpoint = forms.CharField(
        label=_('Wallet Endpoint'),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Interledger wallet endpoint')
        }),
        help_text=_('Your Interledger wallet endpoint URL')
    )
    
    preferred_language = forms.ChoiceField(
        label=_('Preferred Language'),
        choices=[
            ('en', 'English'),
            ('es', 'Spanish'),
            ('nah', 'Nahuatl'),
            ('oto', 'Otomi'),
            ('maz', 'Mazahua'),
            ('que', 'Quechua'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    native_languages = forms.CharField(
        label=_('Native Languages'),
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Comma-separated: nahuatl, otomi')
        }),
        help_text=_('List languages you can work in (comma-separated)')
    )
    
    role = forms.ChoiceField(
        label=_('Role'),
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_('Your role in the marketplace')
    )
    
    profile_note = forms.CharField(
        label=_('Profile Note'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': _('Tell job owners about yourself and why you are interested...')
        }),
        help_text=_('This will be used to auto-fill your job applications')
    )
    
    profile_audio = forms.FileField(
        label=_('Profile Audio (Optional)'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'audio/*'
        }),
        help_text=_('Optional audio introduction')
    )
    
    profile_video = forms.FileField(
        label=_('Profile Video (Optional)'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'video/*'
        }),
        help_text=_('Optional video introduction')
    )
    
    profile_image = forms.ImageField(
        label=_('Profile Image (Optional)'),
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text=_('Optional profile image')
    )
    
    class Meta:
        model = User
        fields = ['email', 'wallet_endpoint', 'preferred_language', 'native_languages', 'role', 
                  'profile_note', 'profile_audio', 'profile_video', 'profile_image']
    
    def clean_email(self):
        """Ensure email is unique if changed."""
        email = self.cleaned_data.get('email')
        if email and self.instance.pk:
            # Check if email is being changed and if it's already taken
            if email != self.instance.email:
                if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError(_('This email is already in use.'))
        return email


class PasswordChangeForm(forms.Form):
    """Form for changing user password."""
    
    old_password = forms.CharField(
        label=_('Current Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password'
        }),
        required=True
    )
    
    new_password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        required=True,
        help_text=password_validation.password_validators_help_text_html()
    )
    
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        required=True
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """Verify old password is correct."""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(_('Your current password is incorrect.'))
        return old_password
    
    def clean_new_password2(self):
        """Verify both new passwords match and meet validation requirements."""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError(_('The two password fields didn\'t match.'))
        
        if password2:
            password_validation.validate_password(password2, self.user)
        
        return password2
    
    def save(self):
        """Save the new password."""
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.save()
        return self.user
