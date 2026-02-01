"""
Management command to seed 2026 F1 data.

Usage:
    python manage.py seed_2026                  # From data/f1calendar_2026.json
    python manage.py seed_2026 --from-fixtures  # From JSON fixtures
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from predictions.models import Team, Driver, GrandPrix, Session


class Command(BaseCommand):
    help = "Seed 2026 F1 teams, drivers, events and sessions (idempotent upsert)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--from-fixtures",
            action="store_true",
            help="Load from JSON fixtures instead of data file",
        )

    def handle(self, *args, **options):
        if options["from_fixtures"]:
            self._load_from_fixtures()
        else:
            self._load_from_data_file()

        self.stdout.write(self.style.SUCCESS("Seed completed."))

    def _load_from_fixtures(self):
        """Load from Django fixtures JSON files."""
        fixtures_dir = Path(__file__).resolve().parent.parent.parent / "fixtures"

        # Teams
        self._load_teams_fixture(fixtures_dir / "teams_2026.json")

        # Drivers
        self._load_drivers_fixture(fixtures_dir / "drivers_2026.json")

        # Events + Sessions from data file
        self._load_events_from_data()

    def _load_from_data_file(self):
        """Load from data/f1calendar_2026.json."""
        # First seed teams and drivers with defaults
        self._seed_default_teams()
        self._seed_default_drivers()

        # Then load events
        self._load_events_from_data()

    def _load_teams_fixture(self, path):
        if not path.exists():
            self.stdout.write(f"  Teams fixture not found: {path}")
            return
        with open(path, "r") as f:
            data = json.load(f)
        for item in data:
            fields = item["fields"]
            Team.objects.update_or_create(
                slug=fields["slug"],
                defaults={
                    "name": fields["name"],
                    "color": fields.get("color", ""),
                    "active": fields.get("active", True),
                },
            )
        self.stdout.write(f"  Teams: {len(data)} upserted")

    def _load_drivers_fixture(self, path):
        if not path.exists():
            self.stdout.write(f"  Drivers fixture not found: {path}")
            return
        with open(path, "r") as f:
            data = json.load(f)
        for item in data:
            fields = item["fields"]
            team = None
            if fields.get("team"):
                team = Team.objects.filter(pk=fields["team"]).first()
            Driver.objects.update_or_create(
                code=fields["code"],
                defaults={
                    "name": fields["name"],
                    "team": team,
                    "active": fields.get("active", True),
                },
            )
        self.stdout.write(f"  Drivers: {len(data)} upserted")

    def _load_events_from_data(self):
        """Load events and sessions from data/f1calendar_2026.json."""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_file = base_dir / "data" / "f1calendar_2026.json"

        if not data_file.exists():
            self.stdout.write(self.style.WARNING(f"  Data file not found: {data_file}"))
            return

        with open(data_file, "r") as f:
            events_data = json.load(f)

        events_count = 0
        sessions_count = 0

        for ev in events_data:
            gp, _ = GrandPrix.objects.update_or_create(
                slug=ev["slug"],
                defaults={
                    "season_year": ev["season_year"],
                    "round": ev["round"],
                    "name": ev["name"],
                    "country": ev.get("country", ""),
                    "circuit": ev.get("circuit", ""),
                },
            )
            events_count += 1

            for sess in ev.get("sessions", []):
                Session.objects.update_or_create(
                    event=gp,
                    session_type=sess["type"],
                    defaults={
                        "start_utc": parse_datetime(sess["start_utc"]),
                        "order": sess.get("order", 0),
                    },
                )
                sessions_count += 1

        self.stdout.write(f"  Events: {events_count} upserted")
        self.stdout.write(f"  Sessions: {sessions_count} upserted")

    def _seed_default_teams(self):
        """Seed default teams for 2026."""
        teams = [
            {"slug": "red-bull", "name": "Red Bull Racing", "color": "#3671C6"},
            {"slug": "ferrari", "name": "Ferrari", "color": "#E80020"},
            {"slug": "mclaren", "name": "McLaren", "color": "#FF8000"},
            {"slug": "mercedes", "name": "Mercedes", "color": "#27F4D2"},
            {"slug": "aston-martin", "name": "Aston Martin", "color": "#229971"},
            {"slug": "alpine", "name": "Alpine", "color": "#FF87BC"},
            {"slug": "williams", "name": "Williams", "color": "#64C4FF"},
            {"slug": "racing-bulls", "name": "Racing Bulls", "color": "#6692FF"},
            {"slug": "audi", "name": "Audi", "color": "#52E252"},
            {"slug": "haas", "name": "Haas F1 Team", "color": "#B6BABD"},
            {"slug": "cadillac", "name": "Cadillac", "color": "#1E3D6B"},
        ]
        for t in teams:
            Team.objects.update_or_create(
                slug=t["slug"],
                defaults={"name": t["name"], "color": t["color"], "active": True},
            )
        self.stdout.write(f"  Teams: {len(teams)} upserted")

    def _seed_default_drivers(self):
        """Seed default drivers for 2026."""
        drivers = [
            {"code": "VER", "name": "Max Verstappen", "team_slug": "red-bull"},
            {"code": "HAD", "name": "Isack Hadjar", "team_slug": "red-bull"},
            {"code": "LEC", "name": "Charles Leclerc", "team_slug": "ferrari"},
            {"code": "HAM", "name": "Lewis Hamilton", "team_slug": "ferrari"},
            {"code": "NOR", "name": "Lando Norris", "team_slug": "mclaren"},
            {"code": "PIA", "name": "Oscar Piastri", "team_slug": "mclaren"},
            {"code": "RUS", "name": "George Russell", "team_slug": "mercedes"},
            {"code": "ANT", "name": "Kimi Antonelli", "team_slug": "mercedes"},
            {"code": "ALO", "name": "Fernando Alonso", "team_slug": "aston-martin"},
            {"code": "STR", "name": "Lance Stroll", "team_slug": "aston-martin"},
            {"code": "GAS", "name": "Pierre Gasly", "team_slug": "alpine"},
            {"code": "COL", "name": "Franco Colapinto", "team_slug": "alpine"},
            {"code": "ALB", "name": "Alexander Albon", "team_slug": "williams"},
            {"code": "SAI", "name": "Carlos Sainz", "team_slug": "williams"},
            {"code": "LAW", "name": "Liam Lawson", "team_slug": "racing-bulls"},
            {"code": "LIN", "name": "Arvid Lindblad", "team_slug": "racing-bulls"},
            {"code": "HUL", "name": "Nico Hulkenberg", "team_slug": "audi"},
            {"code": "BOR", "name": "Gabriel Bortoleto", "team_slug": "audi"},
            {"code": "OCO", "name": "Esteban Ocon", "team_slug": "haas"},
            {"code": "BEA", "name": "Oliver Bearman", "team_slug": "haas"},
            {"code": "PER", "name": "Sergio Perez", "team_slug": "cadillac"},
            {"code": "BOT", "name": "Valtteri Bottas", "team_slug": "cadillac"},
        ]
        for d in drivers:
            team = Team.objects.filter(slug=d["team_slug"]).first()
            Driver.objects.update_or_create(
                code=d["code"],
                defaults={"name": d["name"], "team": team, "active": True},
            )
        self.stdout.write(f"  Drivers: {len(drivers)} upserted")
