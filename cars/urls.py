from django.urls import path

from . import views

app_name = 'cars'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.listing, name='listing'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contact, name='contact'),
]
