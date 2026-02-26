from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

# F1 championship points by finishing position
F1_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}


class Team(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)
    color = models.CharField(max_length=7, blank=True)  # hex color
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Driver(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=80)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class GrandPrix(models.Model):
    """A race weekend event."""
    season_year = models.IntegerField(default=2026)
    round = models.IntegerField()
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    country = models.CharField(max_length=80, blank=True)
    circuit = models.CharField(max_length=120, blank=True)

    # Results
    result_p1 = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    result_p2 = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    result_p3 = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    result_p4 = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    result_p5 = models.ForeignKey(Driver, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    result_alonso_pos = models.IntegerField(null=True, blank=True)
    result_sainz_pos = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["season_year", "round"]
        verbose_name_plural = "Grand Prix"

    def __str__(self):
        return f"{self.name} ({self.season_year})"

    @property
    def fp1_start_utc(self):
        """Return FP1 session start time."""
        fp1 = self.sessions.filter(session_type="FP1").first()
        return fp1.start_utc if fp1 else None

    @property
    def race_start_utc(self):
        """Return RACE session start time."""
        race = self.sessions.filter(session_type="RACE").first()
        return race.start_utc if race else None

    @property
    def deadline_utc(self):
        """Predictions close 48h before FP1."""
        fp1 = self.fp1_start_utc
        if fp1:
            return fp1 - timedelta(hours=24)
        return None

    @property
    def is_locked(self) -> bool:
        """True if predictions are closed."""
        deadline = self.deadline_utc
        if deadline is None:
            return True  # No FP1 = locked
        return timezone.now() >= deadline

    @property
    def has_results(self) -> bool:
        return all([
            self.result_p1, self.result_p2, self.result_p3,
            self.result_p4, self.result_p5
        ]) and self.result_alonso_pos is not None and self.result_sainz_pos is not None


class Session(models.Model):
    """A session within a GP weekend (FP1, FP2, etc.)."""
    SESSION_TYPES = [
        ("FP1", "Practice 1"),
        ("FP2", "Practice 2"),
        ("FP3", "Practice 3"),
        ("QUALI", "Qualifying"),
        ("RACE", "Race"),
        ("SPRINT_QUALI", "Sprint Qualifying"),
        ("SPRINT", "Sprint"),
    ]

    event = models.ForeignKey(GrandPrix, on_delete=models.CASCADE, related_name="sessions")
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES)
    start_utc = models.DateTimeField()
    end_utc = models.DateTimeField(null=True, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["event", "order", "start_utc"]
        constraints = [
            models.UniqueConstraint(fields=["event", "session_type"], name="uniq_session_event_type")
        ]

    def __str__(self):
        return f"{self.event.name} - {self.get_session_type_display()}"


class Prediction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(GrandPrix, on_delete=models.CASCADE)

    p1 = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="+")
    p2 = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="+")
    p3 = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="+")
    p4 = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="+")
    p5 = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="+")

    alonso_pos_guess = models.IntegerField()  # 0=DNF, 1-20
    sainz_pos_guess = models.IntegerField(default=0)  # 0=DNF, 1-20

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    score = models.IntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "event"], name="uniq_prediction_user_event")
        ]
        ordering = ["event__round", "user__username"]

    def __str__(self):
        return f"{self.user.username} - {self.event.name}"

    def clean(self):
        # Validate top5 unique
        picks = [self.p1_id, self.p2_id, self.p3_id, self.p4_id, self.p5_id]
        if len(set(picks)) != 5:
            raise ValidationError("Top5: no puedes repetir pilotos.")

        # Validate alonso position
        if self.alonso_pos_guess < 0 or self.alonso_pos_guess > 20:
            raise ValidationError("Posición Alonso inválida (0=DNF, 1-20).")

        # Validate sainz position
        if self.sainz_pos_guess < 0 or self.sainz_pos_guess > 20:
            raise ValidationError("Posición Sainz inválida (0=DNF, 1-20).")

        # Validate deadline (event may not be set yet during form validation)
        if self.event_id is not None and self.event.is_locked:
            raise ValidationError("Las predicciones están cerradas para este GP.")

    def calculate_score(self) -> int:
        """Calculate score based on GP results. GP must have results set."""
        gp = self.event
        if not gp.has_results:
            return 0

        score = 0

        # Map finishing position -> driver for top 5
        result_map = {
            1: gp.result_p1_id,
            2: gp.result_p2_id,
            3: gp.result_p3_id,
            4: gp.result_p4_id,
            5: gp.result_p5_id,
        }
        # Map driver -> finishing position (for half-points lookup)
        driver_to_pos = {drv_id: pos for pos, drv_id in result_map.items()}

        # Top 5 scoring
        for pos in range(1, 6):
            predicted_id = getattr(self, f"p{pos}_id")
            actual_pos = driver_to_pos.get(predicted_id)
            if actual_pos is None:
                continue
            real_pts = F1_POINTS[actual_pos]
            if actual_pos == pos:
                score += real_pts          # exact hit
            else:
                score += real_pts // 2    # right driver, wrong slot

        # Alonso scoring
        if gp.result_alonso_pos is not None:
            alonso_pts = F1_POINTS.get(gp.result_alonso_pos, 0)
            if self.alonso_pos_guess == gp.result_alonso_pos:
                score += alonso_pts * 2
            elif gp.result_alonso_pos <= 10:
                score += alonso_pts

        # Sainz scoring (same rules)
        if gp.result_sainz_pos is not None:
            sainz_pts = F1_POINTS.get(gp.result_sainz_pos, 0)
            if self.sainz_pos_guess == gp.result_sainz_pos:
                score += sainz_pts * 2
            elif gp.result_sainz_pos <= 10:
                score += sainz_pts

        return score

    def save(self, *args, **kwargs):
        # Skip deadline check if updating score only
        if not kwargs.pop("skip_lock_check", False):
            self.full_clean()
        super().save(*args, **kwargs)


class NewsPost(models.Model):
    title = models.CharField(max_length=140)
    body = models.TextField()
    image_url = models.URLField(blank=True, help_text="URL de imagen externa (opcional)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
