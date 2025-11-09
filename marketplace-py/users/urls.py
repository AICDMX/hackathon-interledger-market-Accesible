from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('register/creator/', views.register_creator, name='register_creator'),
    path('register/doer/', views.register_doer, name='register_doer'),
]
