from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.job_list, name='list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('owner-dashboard/', views.job_owner_dashboard, name='owner_dashboard'),
    path('create/', views.create_job, name='create'),
    path('<int:pk>/edit/', views.edit_job, name='edit'),
    path('<int:pk>/duplicate/', views.duplicate_job, name='duplicate'),
    path('<int:pk>/', views.job_detail, name='detail'),
    path('<int:pk>/submit/', views.submit_job, name='submit'),
    path('<int:pk>/preview-submission/', views.preview_submission, name='preview_submission'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('my-jobs/<int:pk>/complete/', views.mark_job_completed, name='mark_job_completed'),
    path('accepted/', views.accepted_jobs, name='accepted'),
    path('<int:job_pk>/accept/<int:submission_pk>/', views.accept_submission, name='accept_submission'),
    path('<int:job_pk>/decline/<int:submission_pk>/', views.decline_submission, name='decline_submission'),
    path('<int:job_pk>/mark-complete/<int:submission_pk>/', views.mark_submission_complete, name='mark_submission_complete'),
    path('<int:pk>/apply/', views.apply_to_job, name='apply_to_job'),
    path('<int:pk>/applications/', views.view_applications, name='view_applications'),
    path('<int:job_pk>/applications/<int:application_pk>/select/', views.select_application, name='select_application'),
    path('<int:pk>/pre-approve-payments/', views.pre_approve_payments, name='pre_approve_payments'),
    path('<int:pk>/start-contract/', views.start_contract, name='start_contract'),
    path('contract-complete/<str:contract_id>/', views.complete_contract_payment, name='complete_contract_payment'),
    path('<int:pk>/complete-contract/', views.complete_contract, name='complete_contract'),
    path('<int:pk>/cancel-contract/', views.cancel_contract, name='cancel_contract'),
    # Payment finish callback (from wallet -> Django)
    path('payments/finish', views.payments_finish, name='payments_finish'),
    path('my-products/', views.my_products, name='my_products'),
    path('my-money/', views.my_money, name='my_money'),
    path('pending/', views.pending_jobs, name='pending_jobs'),
    path('filler-1/', views.filler_page_1, name='filler_1'),
    path('filler-2/', views.filler_page_2, name='filler_2'),
    path('audio-support/<slug:slug>/', views.audio_support, name='audio_support'),
]
