"""
URL configuration for sgr_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from sgr_app import web_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web Views (HTML + Bootstrap 5)
    path('', web_views.web_login, name='home'),
    path('login/', web_views.web_login, name='web_login'),
    path('logout/', web_views.web_logout, name='web_logout'),
    path('verificar-2fa/', web_views.web_verificar_2fa, name='web_verificar_2fa'),
    path('dashboard/', web_views.web_dashboard, name='web_dashboard'),
    path('personal/', web_views.web_personal, name='web_personal'),
    path('verificacion/', web_views.web_verificacion, name='web_verificacion'),
    path('verificacion/<int:evidencia_id>/validar/', web_views.web_validar_evidencia, name='web_validar_evidencia'),
    path('tubo/', web_views.web_tubo, name='web_tubo'),
    path('tubo/<int:compromiso_id>/cambiar-estado/', web_views.web_cambiar_estado_compromiso, name='web_cambiar_estado_compromiso'),
    path('tubo/crear/', web_views.web_crear_compromiso, name='web_crear_compromiso'),
    path('terreno/', web_views.web_terreno, name='web_terreno'),
    path('casos-sociales/', web_views.web_casos_sociales, name='web_casos_sociales'),
    path('auditoria/', web_views.web_auditoria, name='web_auditoria'),

    # API REST
    path('api/', include('sgr_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])


