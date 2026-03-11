from django.urls import path

from . import views

app_name = "kiosk"

urlpatterns = [
    path('', views.kiosk_display, name='kiosk_display'),
]
