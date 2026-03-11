from django.urls import path

from . import views

app_name = "kiosk"

urlpatterns = [
    path('', views.kiosk_list_or_default, name='kiosk_display'),
    path('<slug:kiosk_slug>/', views.kiosk_display, name='kiosk_display_by_slug'),
]
