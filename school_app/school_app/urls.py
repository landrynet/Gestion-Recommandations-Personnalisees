from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # PWA — sw.js doit être servi à la racine pour contrôler tout le site
    path('sw.js', TemplateView.as_view(
        template_name='sw.js',
        content_type='application/javascript',
    ), name='sw'),
    path('manifest.json', TemplateView.as_view(
        template_name='manifest.json',
        content_type='application/manifest+json',
    ), name='manifest'),
    path('', include('dashboard.urls')),
    path('login/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('eleves/', include('students.urls')),
    path('enseignants/', include('teachers.urls')),
    path('classes/', include('classes.urls')),
    path('matieres/', include('subjects.urls')),
    path('bulletins/', include('bulletin.urls')),
    path('notes/', include('grades.urls')),
    path('rapports/', include('reports.urls')),
    path('parametres/', include('school_settings.urls')),
    path('portail/', include('portail.urls')),
    path('cartes/', include('carte_eleve.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
