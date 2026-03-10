from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("subscribe/", views.subscribe, name="subscribe"),
    path("confirm/<uuid:token>/", views.confirm, name="confirm"),
    path("unsubscribe/", views.unsubscribe_request_page, name="unsubscribe_request_page"),
    path("unsubscribe/request/", views.unsubscribe_request, name="unsubscribe_request"),
    path("unsubscribe/<uuid:token>/", views.unsubscribe, name="unsubscribe"),
    path("preview/<slug:slug>/", views.preview, name="preview"),
]
