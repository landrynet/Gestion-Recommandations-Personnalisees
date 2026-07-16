from django.urls import path
from . import views

urlpatterns = [
    # Années scolaires
    path('annees/', views.annee_list, name='annee_list'),
    path('annees/nouvelle/', views.annee_create, name='annee_create'),
    path('annees/<int:pk>/modifier/', views.annee_update, name='annee_update'),
    path('annees/<int:pk>/supprimer/', views.annee_delete, name='annee_delete'),
    # Sections
    path('sections/', views.section_list, name='section_list'),
    path('sections/nouvelle/', views.section_create, name='section_create'),
    path('sections/<int:pk>/modifier/', views.section_update, name='section_update'),
    path('sections/<int:pk>/supprimer/', views.section_delete, name='section_delete'),
    # Classes
    path('', views.classe_list, name='classe_list'),
    path('nouvelle/', views.classe_create, name='classe_create'),
    path('<int:pk>/modifier/', views.classe_update, name='classe_update'),
    path('<int:pk>/supprimer/', views.classe_delete, name='classe_delete'),
]
