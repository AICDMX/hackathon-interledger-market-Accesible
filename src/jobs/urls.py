from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_job, name='create'),
    path('<int:pk>/', views.job_detail, name='detail'),
    path('<int:pk>/submit/', views.submit_job, name='submit'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('accepted/', views.accepted_jobs, name='accepted'),
    path('<int:job_pk>/accept/<int:submission_pk>/', views.accept_submission, name='accept_submission'),
    path('my-products/', views.my_products, name='my_products'),
    path('my-money/', views.my_money, name='my_money'),
    path('pending/', views.pending_jobs, name='pending_jobs'),
    path('filler-1/', views.filler_page_1, name='filler_1'),
    path('filler-2/', views.filler_page_2, name='filler_2'),
]
