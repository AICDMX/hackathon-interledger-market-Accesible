from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='list'),
    path('create/', views.create_job, name='create'),
    path('<int:pk>/', views.job_detail, name='detail'),
    path('<int:pk>/submit/', views.submit_job, name='submit'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('accepted/', views.accepted_jobs, name='accepted'),
    path('<int:job_pk>/accept/<int:submission_pk>/', views.accept_submission, name='accept_submission'),
]
