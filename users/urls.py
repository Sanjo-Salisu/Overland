from django.urls import path
from . import views

urlpatterns = [
    path('', views.register_customer, name='register_customer'),
    path('scan/', views.scan_qr_view, name='scan_qr'),  
]


