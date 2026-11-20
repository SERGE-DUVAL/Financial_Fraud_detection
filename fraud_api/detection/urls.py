from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("api/modele/", views.api_modele, name="api_modele"),
    path("api/exemple/", views.api_exemple, name="api_exemple"),
    path("api/predire/", views.api_predire, name="api_predire"),
    path("api/lot/", views.api_lot, name="api_lot"),
]
