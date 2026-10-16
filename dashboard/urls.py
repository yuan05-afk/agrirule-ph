from django.urls import path

from dashboard import views

urlpatterns = [
    path('', views.dashboard_index, name='dashboard_index'),
    path('crops/', views.crops_list, name='dashboard_crops_list'),
    path('crops/add/', views.crop_add, name='dashboard_crop_add'),
    path('crops/edit/<int:crop_id>/', views.crop_edit, name='dashboard_crop_edit'),
    path('rules/', views.rules_list, name='dashboard_rules_list'),
    path('rules/add/', views.rule_add, name='dashboard_rule_add'),
    path('rules/edit/<int:rule_id>/', views.rule_edit, name='dashboard_rule_edit'),
    path('consultations/', views.consultations_list, name='dashboard_consultations'),
]
