from django.urls import path
from . import views

urlpatterns = [
    # ── Public (parents) ──────────────────────────────────────────────────
    path('', views.portail_accueil, name='portail_accueil'),
    path('scan/<str:token>/', views.portail_scan, name='portail_scan'),
    path('resultats/<str:token>/', views.portail_resultats, name='portail_resultats'),
    path('deconnexion/<str:token>/', views.portail_deconnexion, name='portail_deconnexion'),

    # ── QR Code image ─────────────────────────────────────────────────────
    path('qr/<int:pk>/', views.qr_code_image, name='qr_code_image'),

    # ── Back-office Préfet ────────────────────────────────────────────────
    path('publications/', views.publication_list, name='publication_list'),
    path('publications/toggle/<int:classe_id>/<str:periode>/',
         views.publication_toggle, name='publication_toggle'),
    path('config/', views.portail_config_view, name='portail_config'),
    path('acces/', views.acces_list, name='portail_acces_list'),
    path('acces/reset/<int:pk>/', views.reset_acces_eleve, name='reset_acces_eleve'),
]
