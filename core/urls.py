from django.urls import path

from core import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('consult/', views.consult, name='consult'),
    path('results/<int:consultation_id>/', views.results, name='results'),
    path('results/<int:consultation_id>/analytics/', views.result_analytics, name='result_analytics'),
    path('results/<int:consultation_id>/analytics/data/', views.result_analytics_data, name='result_analytics_data'),
    path('history/', views.history, name='history'),
    path('healthz/', views.healthz, name='healthz'),
]
