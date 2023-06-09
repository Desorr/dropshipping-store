from django.contrib import admin
from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.index, name='index'),
    path('contacts/', views.contacts, name='contacts'),
    path('about_us/', views.about_us, name='about_us'),
    path('balance/', views.balance_add, name='balance_add'),
    path('auth/', include('authentication.urls')),
    path('shop/', include('shop.urls')),
    path('admin/', admin.site.urls),
]
