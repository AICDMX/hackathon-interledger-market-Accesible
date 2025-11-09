from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import User


def register(request):
    """User registration view."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role', 'both')
        
        if password1 != password2:
            messages.error(request, _('Passwords do not match.'))
            return render(request, 'users/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Username already exists.'))
            return render(request, 'users/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            role=role
        )
        login(request, user)
        messages.success(request, _('Registration successful!'))
        return redirect('jobs:dashboard')
    
    return render(request, 'users/register.html')


def register_creator(request):
    """Registration view for job creators (funders)."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, _('Passwords do not match.'))
            return render(request, 'users/register_creator.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Username already exists.'))
            return render(request, 'users/register_creator.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            role='funder'
        )
        login(request, user)
        messages.success(request, _('Registration successful! Welcome, job creator!'))
        return redirect('jobs:dashboard')
    
    return render(request, 'users/register_creator.html')


def register_doer(request):
    """Registration view for job doers (creators)."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 != password2:
            messages.error(request, _('Passwords do not match.'))
            return render(request, 'users/register_doer.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, _('Username already exists.'))
            return render(request, 'users/register_doer.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            role='creator'
        )
        login(request, user)
        messages.success(request, _('Registration successful! Welcome, job doer!'))
        return redirect('jobs:dashboard')
    
    return render(request, 'users/register_doer.html')


def profile(request):
    """User profile view."""
    if request.method == 'POST':
        user = request.user
        user.wallet_endpoint = request.POST.get('wallet_endpoint', '')
        user.preferred_language = request.POST.get('preferred_language', 'en')
        user.native_languages = request.POST.get('native_languages', '')
        user.save()
        messages.success(request, _('Profile updated successfully!'))
        return redirect('users:profile')
    
    return render(request, 'users/profile.html')
