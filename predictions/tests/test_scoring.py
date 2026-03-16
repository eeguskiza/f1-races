from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from predictions.models import Driver, GrandPrix, Prediction, Session, Team


User = get_user_model()


class ScoringRulesTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(name="Test Team", slug="test-team")
        self.drivers = [
            Driver.objects.create(code=f"D{i:02d}", name=f"Driver {i}", team=self.team)
            for i in range(1, 7)
        ]
        self.user = User.objects.create_user(username="scoring-user", password="testpass")

        self.gp = GrandPrix.objects.create(
            season_year=2026,
            round=77,
            name="Scoring GP",
            slug="scoring-gp",
            result_p1=self.drivers[0],
            result_p2=self.drivers[1],
            result_p3=self.drivers[2],
            result_p4=self.drivers[3],
            result_p5=self.drivers[4],
            result_alonso_pos=0,
            result_sainz_pos=0,
        )
        Session.objects.create(
            event=self.gp,
            session_type="FP1",
            start_utc=timezone.now() + timedelta(days=7),
            order=1,
        )

    def test_exact_dnf_is_two_points_in_total_and_breakdown(self):
        prediction = Prediction.objects.create(
            user=self.user,
            event=self.gp,
            p1=self.drivers[0],
            p2=self.drivers[1],
            p3=self.drivers[2],
            p4=self.drivers[3],
            p5=self.drivers[4],
            alonso_pos_guess=0,
            sainz_pos_guess=0,
        )

        total = prediction.calculate_score()
        breakdown = prediction.score_breakdown()

        self.assertEqual(breakdown["alonso"], 2)
        self.assertEqual(breakdown["sainz"], 2)
        self.assertEqual(total, 84)
