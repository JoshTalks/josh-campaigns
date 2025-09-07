from django.urls import path
from .views import register, home, user_login

urlpatterns = [
    path("", home, name="register"),
    path("register/", register, name="home"),
    path("login/", user_login, name="login"),
]
