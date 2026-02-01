from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone

from .models import GrandPrix, Prediction, Driver


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


def home(request):
    return render(request, "predictions/home.html")


def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("predictions:home")
    else:
        form = SignupForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    """User dashboard with total points and next race status."""
    user = request.user
    now = timezone.now()

    # Total points
    total_points = Prediction.objects.filter(
        user=user, score__isnull=False
    ).aggregate(total=Sum("score"))["total"] or 0

    # Next race (first event with RACE session in future)
    next_event = None
    user_prediction = None
    for gp in GrandPrix.objects.all():
        race_start = gp.race_start_utc
        if race_start and race_start > now:
            next_event = gp
            user_prediction = Prediction.objects.filter(user=user, event=gp).first()
            break

    context = {
        "total_points": total_points,
        "next_event": next_event,
        "user_prediction": user_prediction,
    }
    return render(request, "predictions/dashboard.html", context)


def races(request):
    """List all events with status."""
    events = []
    now = timezone.now()

    for gp in GrandPrix.objects.prefetch_related("sessions").all():
        race_start = gp.race_start_utc
        deadline = gp.deadline_utc
        is_locked = gp.is_locked

        events.append({
            "gp": gp,
            "race_start": race_start,
            "deadline": deadline,
            "status": "CLOSED" if is_locked else "OPEN",
        })

    return render(request, "predictions/races.html", {"events": events})


def leaderboard(request):
    return render(request, "predictions/leaderboard.html")
