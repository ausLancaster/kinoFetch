from django.urls import path
from . import views

urlpatterns = [
  path("", views.home),
  path("update_listings/", views.update_listings, name='update_listings')
]
