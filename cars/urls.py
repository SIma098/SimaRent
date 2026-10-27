from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'cars'

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog/', views.listing, name='listing'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contact, name='contact'),
    # CRUD автомобилей
    path('catalog/add/', views.car_create, name='car_create'),
    path('catalog/<int:pk>/', views.car_detail, name='car_detail'),
    path('catalog/<int:pk>/edit/', views.car_update, name='car_update'),
    path('catalog/<int:pk>/delete/', views.car_delete, name='car_delete'),
    # CRUD офисов
    path('contacts/offices/add/', views.office_create, name='office_create'),
    path('contacts/offices/<int:pk>/edit/', views.office_update, name='office_update'),
    path('contacts/offices/<int:pk>/delete/', views.office_delete, name='office_delete'),
    # личный кабинет
    path('profile/', views.profile, name='profile'),
    # вход и выход — готовые представления Django, шаблон входа свой
    path('login/', auth_views.LoginView.as_view(
        template_name='cars/login.html', redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
