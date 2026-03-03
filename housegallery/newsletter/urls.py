from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("", views.signup_page, name="signup"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("confirm/<uuid:token>/", views.confirm, name="confirm"),
    path("unsubscribe/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
    path("preview/<slug:slug>/", views.preview, name="preview"),
]
