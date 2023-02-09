'''URLs for the dashboard app.'''

from django.urls import path, include
from django.contrib import admin
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('api/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('', views.handle_index, name='index'),
]
