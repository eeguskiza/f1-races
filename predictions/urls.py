from django.urls import path
from . import views

app_name = "predictions"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("races/", views.races, name="races"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
]

