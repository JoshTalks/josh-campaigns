from django.urls import path
from .views import register, home

urlpatterns = [
    path("", home, name="register"),
    path("register/", register, name="home"),

]
