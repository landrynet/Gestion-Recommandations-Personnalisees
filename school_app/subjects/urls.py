from django.urls import path
from . import views

urlpatterns = [
    path('', views.matiere_list, name='matiere_list'),
    path('nouvelle/', views.matiere_create, name='matiere_create'),
    path('<int:pk>/modifier/', views.matiere_update, name='matiere_update'),
    path('<int:pk>/supprimer/', views.matiere_delete, name='matiere_delete'),
    path('affectations/', views.affectation_list, name='affectation_list'),
    path('affectations/nouvelle/', views.affectation_create, name='affectation_create'),
    path('affectations/<int:pk>/modifier/', views.affectation_update, name='affectation_update'),
    path('affectations/<int:pk>/supprimer/', views.affectation_delete, name='affectation_delete'),
]
