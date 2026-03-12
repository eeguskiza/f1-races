"""Tests for seed_2026 management command and model logic."""
from datetime import datetime, time, timedelta, timezone as dt_timezone
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from predictions.models import Team, Driver, GrandPrix, Session, Prediction


User = get_user_model()


class SeedCommandTests(TestCase):
    """Test seed_2026 command."""

    def test_seed_creates_teams(self):
        call_command("seed_2026", stdout=StringIO())
        self.assertEqual(Team.objects.count(), 11)

    def test_seed_creates_drivers(self):
        call_command("seed_2026", stdout=StringIO())
        self.assertEqual(Driver.objects.count(), 22)

    def test_seed_creates_events(self):
        call_command("seed_2026", stdout=StringIO())
        self.assertEqual(GrandPrix.objects.count(), 24)  # 23 original + Madrid GP

    def test_seed_creates_sessions(self):
        call_command("seed_2026", stdout=StringIO())
        # 23 events, each with 5 sessions (some have sprint instead of FP2/FP3)
        self.assertGreaterEqual(Session.objects.count(), 100)

    def test_seed_idempotent(self):
        """Running seed twice doesn't duplicate."""
        call_command("seed_2026", stdout=StringIO())
        call_command("seed_2026", stdout=StringIO())
        self.assertEqual(Team.objects.count(), 11)
        self.assertEqual(Driver.objects.count(), 22)
        self.assertEqual(GrandPrix.objects.count(), 24)  # 23 original + Madrid GP

    def test_every_event_has_fp1(self):
        """Every event should have FP1 session."""
        call_command("seed_2026", stdout=StringIO())
        for gp in GrandPrix.objects.all():
            self.assertIsNotNone(
                gp.fp1_start_utc,
                f"Event {gp.name} missing FP1 session"
            )

    def test_deadline_is_friday_end_before_quali(self):
        """Deadline should be Friday 23:59:59 UTC (or QUALI start, if earlier)."""
        call_command("seed_2026", stdout=StringIO())
        gp = GrandPrix.objects.first()
        quali = gp.sessions.get(session_type="QUALI").start_utc.astimezone(dt_timezone.utc)
        days_since_friday = (quali.weekday() - 4) % 7
        friday_date = (quali - timedelta(days=days_since_friday)).date()
        friday_end = datetime.combine(friday_date, time(23, 59, 59), tzinfo=dt_timezone.utc)
        deadline = gp.deadline_utc
        self.assertEqual(deadline, min(friday_end, quali))

    def test_driver_alonso_exists(self):
        call_command("seed_2026", stdout=StringIO())
        alo = Driver.objects.get(code="ALO")
        self.assertEqual(alo.name, "Fernando Alonso")
        self.assertTrue(alo.active)


class DeadlineValidationTests(TestCase):
    """Test prediction deadline validation."""

    def setUp(self):
        # Create minimal data for testing
        self.team = Team.objects.create(name="Test Team", slug="test-team")
        self.driver1 = Driver.objects.create(code="D01", name="Driver 1", team=self.team)
        self.driver2 = Driver.objects.create(code="D02", name="Driver 2", team=self.team)
        self.driver3 = Driver.objects.create(code="D03", name="Driver 3", team=self.team)
        self.driver4 = Driver.objects.create(code="D04", name="Driver 4", team=self.team)
        self.driver5 = Driver.objects.create(code="D05", name="Driver 5", team=self.team)
        self.user = User.objects.create_user(username="testuser", password="testpass")

    def test_prediction_blocked_after_deadline(self):
        """Cannot create prediction after deadline."""
        # Create event with FP1 in the past
        gp = GrandPrix.objects.create(
            season_year=2026,
            round=99,
            name="Test GP",
            slug="test-gp"
        )
        # FP1 was 24 hours ago and no QUALI is set, so fallback deadline passed
        Session.objects.create(
            event=gp,
            session_type="FP1",
            start_utc=timezone.now() - timedelta(hours=24),
            order=1
        )

        # Try to create prediction - should fail
        prediction = Prediction(
            user=self.user,
            event=gp,
            p1=self.driver1,
            p2=self.driver2,
            p3=self.driver3,
            p4=self.driver4,
            p5=self.driver5,
            alonso_pos_guess=5
        )
        with self.assertRaises(ValidationError) as ctx:
            prediction.save()
        self.assertIn("cerradas", str(ctx.exception))

    def test_prediction_allowed_before_deadline(self):
        """Can create prediction before deadline."""
        # Create event with FP1 far in the future
        gp = GrandPrix.objects.create(
            season_year=2026,
            round=98,
            name="Future GP",
            slug="future-gp"
        )
        Session.objects.create(
            event=gp,
            session_type="FP1",
            start_utc=timezone.now() + timedelta(days=7),
            order=1
        )

        prediction = Prediction(
            user=self.user,
            event=gp,
            p1=self.driver1,
            p2=self.driver2,
            p3=self.driver3,
            p4=self.driver4,
            p5=self.driver5,
            alonso_pos_guess=5
        )
        prediction.save()  # Should not raise
        self.assertIsNotNone(prediction.pk)

    def test_position_22_is_allowed(self):
        """22 should be a valid finishing position for Alonso and Sainz."""
        gp = GrandPrix.objects.create(
            season_year=2026,
            round=96,
            name="Future GP 22",
            slug="future-gp-22"
        )
        Session.objects.create(
            event=gp,
            session_type="FP1",
            start_utc=timezone.now() + timedelta(days=7),
            order=1
        )

        prediction = Prediction(
            user=self.user,
            event=gp,
            p1=self.driver1,
            p2=self.driver2,
            p3=self.driver3,
            p4=self.driver4,
            p5=self.driver5,
            alonso_pos_guess=22,
            sainz_pos_guess=22,
        )
        prediction.save()
        self.assertIsNotNone(prediction.pk)

    def test_position_23_is_rejected(self):
        """23 should remain invalid."""
        gp = GrandPrix.objects.create(
            season_year=2026,
            round=95,
            name="Future GP 23",
            slug="future-gp-23"
        )
        Session.objects.create(
            event=gp,
            session_type="FP1",
            start_utc=timezone.now() + timedelta(days=7),
            order=1
        )

        prediction = Prediction(
            user=self.user,
            event=gp,
            p1=self.driver1,
            p2=self.driver2,
            p3=self.driver3,
            p4=self.driver4,
            p5=self.driver5,
            alonso_pos_guess=23,
            sainz_pos_guess=22,
        )
        with self.assertRaises(ValidationError):
            prediction.save()

    def test_duplicate_drivers_rejected(self):
        """Cannot have duplicate drivers in top5."""
        gp = GrandPrix.objects.create(
            season_year=2026, round=97, name="Test GP 2", slug="test-gp-2"
        )
        Session.objects.create(
            event=gp,
            session_type="FP1",
            start_utc=timezone.now() + timedelta(days=7),
            order=1
        )

        prediction = Prediction(
            user=self.user,
            event=gp,
            p1=self.driver1,
            p2=self.driver1,  # duplicate!
            p3=self.driver3,
            p4=self.driver4,
            p5=self.driver5,
            alonso_pos_guess=5
        )
        with self.assertRaises(ValidationError):
            prediction.save()
