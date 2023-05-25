from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('contacts/', views.contacts, name='contacts'),
    path('about_us/', views.about_us, name='about_us'),
    path('typography/', views.typography, name='typography'),
    path('auth/', include('authentication.urls')),
    path('admin/', admin.site.urls),
]
