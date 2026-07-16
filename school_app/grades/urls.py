from django.urls import path
from . import views

urlpatterns = [
    path('', views.saisie_notes, name='saisie_notes'),
    path('consulter/', views.consulter_notes, name='consulter_notes'),
]
