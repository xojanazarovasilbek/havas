from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'), # Asosiy sahifa login bo'ladi
    path('logout/', views.logout_view, name='logout'),
    path('kassa/', views.kassa_page, name='kassa'),
    path('get-product/', views.get_product, name='get_product'),
    path('complete-sale/', views.complete_sale, name='complete_sale'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('add-product/', views.add_product, name='add_product'),
]