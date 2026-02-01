from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django import forms
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import GrandPrix, Prediction, Driver, NewsPost
from .forms import PredictionForm


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


def home(request):
    """Public home page with news and next GP."""
    # Recent news (3-6 posts)
    news = NewsPost.objects.all()[:6]

    # Next GP (first with race_start_utc in future)
    now = timezone.now()
    next_event = None
    for gp in GrandPrix.objects.prefetch_related("sessions").all():
        race_start = gp.race_start_utc
        if race_start and race_start > now:
            next_event = gp
            break

    return render(request, "predictions/home.html", {
        "news": news,
        "next_event": next_event,
    })


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
    """User dashboard with total points, next race, and recent predictions."""
    user = request.user
    now = timezone.now()

    # Total points
    total_points = Prediction.objects.filter(
        user=user, score__isnull=False
    ).aggregate(total=Sum("score"))["total"] or 0

    # Next race (first event with RACE session in future)
    next_event = None
    user_prediction = None
    for gp in GrandPrix.objects.prefetch_related("sessions").all():
        race_start = gp.race_start_utc
        if race_start and race_start > now:
            next_event = gp
            user_prediction = Prediction.objects.filter(user=user, event=gp).select_related(
                "p1", "p2", "p3", "p4", "p5"
            ).first()
            break

    # Recent predictions (last 5)
    recent_predictions = Prediction.objects.filter(user=user).select_related(
        "event", "p1", "p2", "p3", "p4", "p5"
    ).order_by("-event__round")[:5]

    context = {
        "total_points": total_points,
        "next_event": next_event,
        "user_prediction": user_prediction,
        "recent_predictions": recent_predictions,
    }
    return render(request, "predictions/dashboard.html", context)


def races(request):
    """List all events with status and user pick info."""
    events = []
    now = timezone.now()
    user = request.user

    # Get user's predictions if logged in
    user_predictions = {}
    if user.is_authenticated:
        for pred in Prediction.objects.filter(user=user).select_related("event"):
            user_predictions[pred.event_id] = True

    for gp in GrandPrix.objects.prefetch_related("sessions").all():
        race_start = gp.race_start_utc
        deadline = gp.deadline_utc
        is_locked = gp.is_locked

        events.append({
            "gp": gp,
            "race_start": race_start,
            "deadline": deadline,
            "status": "CLOSED" if is_locked else "OPEN",
            "has_pick": user_predictions.get(gp.id, False),
        })

    return render(request, "predictions/races.html", {"events": events})


def race_detail(request, slug):
    """Detail view for a Grand Prix."""
    gp = get_object_or_404(
        GrandPrix.objects.prefetch_related("sessions"),
        slug=slug
    )

    sessions = gp.sessions.all().order_by("order", "start_utc")

    user_prediction = None
    if request.user.is_authenticated:
        user_prediction = Prediction.objects.filter(
            user=request.user, event=gp
        ).select_related("p1", "p2", "p3", "p4", "p5").first()

    return render(request, "predictions/race_detail.html", {
        "gp": gp,
        "sessions": sessions,
        "user_prediction": user_prediction,
    })


@login_required
def pick(request, slug):
    """Create or edit a prediction for a GP."""
    gp = get_object_or_404(GrandPrix, slug=slug)

    # Check if locked
    if gp.is_locked:
        return render(request, "predictions/pick.html", {
            "gp": gp,
            "locked": True,
        })

    # Get existing prediction or None
    prediction = Prediction.objects.filter(
        user=request.user, event=gp
    ).select_related("p1", "p2", "p3", "p4", "p5").first()

    if request.method == "POST":
        form = PredictionForm(request.POST, instance=prediction)
        if form.is_valid():
            pred = form.save(commit=False)
            pred.user = request.user
            pred.event = gp
            pred.alonso_pos_guess = int(form.cleaned_data["alonso_pos_guess"])
            try:
                pred.save()
                messages.success(request, f"Pick guardado para {gp.name}")
                return redirect("predictions:dashboard")
            except Exception as e:
                form.add_error(None, str(e))
    else:
        form = PredictionForm(instance=prediction)

    return render(request, "predictions/pick.html", {
        "gp": gp,
        "form": form,
        "prediction": prediction,
        "locked": False,
    })


def leaderboard(request):
    """Leaderboard ranking by total points."""
    # Get users with their total scores and prediction counts
    users_data = []

    # Get all users who have predictions
    user_stats = (
        Prediction.objects.values("user_id", "user__username")
        .annotate(
            total_score=Sum("score"),
            picks_count=Count("id"),
        )
        .order_by("-total_score")
    )

    for stats in user_stats:
        users_data.append({
            "username": stats["user__username"],
            "total_score": stats["total_score"] or 0,
            "picks_count": stats["picks_count"],
        })

    # Total races count
    total_races = GrandPrix.objects.count()

    return render(request, "predictions/leaderboard.html", {
        "users_data": users_data,
        "total_races": total_races,
    })
