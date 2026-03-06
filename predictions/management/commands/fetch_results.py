"""
Management command to fetch F1 race results from Jolpica API
and auto-calculate prediction scores.

Usage:
    python manage.py fetch_results              # Fetch all pending past GPs
    python manage.py fetch_results --round 1    # Fetch specific round
    python manage.py fetch_results --dry-run    # Show what would happen without saving
    python manage.py fetch_results --force      # Re-fetch even if GP already has results
"""
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone

from predictions.models import Driver, GrandPrix, Prediction

JOLPICA_URL = "https://api.jolpi.ca/ergast/f1/{year}/{round}/results/"

# Drivers we track with their codes in our DB
ALONSO_CODE = "ALO"
SAINZ_CODE = "SAI"


def _is_classified_finish(status: str) -> bool:
    """Returns True if the status indicates the driver finished the race."""
    return status == "Finished" or status.startswith("+")


class Command(BaseCommand):
    help = "Fetch race results from Jolpica API and calculate scores automatically"

    def add_arguments(self, parser):
        parser.add_argument("--round", type=int, dest="round_num", help="Round number to fetch")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be done without saving")
        parser.add_argument("--force", action="store_true", help="Re-fetch even if GP already has results")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        round_num = options.get("round_num")

        now = timezone.now()
        qs = GrandPrix.objects.prefetch_related("sessions").filter(season_year=2026)

        if round_num:
            qs = qs.filter(round=round_num)

        pending = []
        for gp in qs:
            race_time = gp.race_start_utc
            if race_time is None:
                continue
            # Wait at least 4 hours after race start before fetching
            if now < race_time + timezone.timedelta(hours=4):
                continue
            if gp.has_results and not force:
                continue
            pending.append(gp)

        if not pending:
            self.stdout.write("No hay GPs pendientes de resultados.")
            return

        for gp in pending:
            self.stdout.write(f"\nProcesando: {gp.name} (Ronda {gp.round}, {gp.season_year})")
            self._fetch_and_save(gp, dry_run)

    def _fetch_and_save(self, gp: GrandPrix, dry_run: bool) -> None:
        url = JOLPICA_URL.format(year=gp.season_year, round=gp.round)

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(f"  ERROR conectando con la API: {e}")
            return

        try:
            races = response.json()["MRData"]["RaceTable"]["Races"]
        except (KeyError, TypeError, ValueError):
            self.stderr.write("  ERROR: formato de respuesta inesperado.")
            return

        if not races:
            self.stdout.write("  Sin resultados disponibles aún.")
            return

        results = races[0].get("Results", [])
        if not results:
            self.stdout.write("  Sin resultados disponibles aún.")
            return

        # Build position -> driver_code map from API
        pos_to_code = {int(r["position"]): r["Driver"].get("code", "").upper() for r in results}

        top5_codes = [pos_to_code.get(p, "?") for p in range(1, 6)]
        self.stdout.write(f"  Top 5 API: {', '.join(top5_codes)}")

        # Resolve top 5 drivers from DB
        drivers_by_code = {d.code.upper(): d for d in Driver.objects.filter(active=True)}

        top5_drivers = {}
        for pos in range(1, 6):
            code = pos_to_code.get(pos)
            driver = drivers_by_code.get(code) if code else None
            if not driver:
                self.stderr.write(
                    f"  ADVERTENCIA: piloto no encontrado para P{pos} (código API: {code!r}). "
                    "Comprueba que el código coincide con el de la BD."
                )
                return
            top5_drivers[pos] = driver

        # Alonso position
        alonso_pos = self._get_driver_pos(results, ALONSO_CODE)
        sainz_pos = self._get_driver_pos(results, SAINZ_CODE)

        self.stdout.write(f"  Alonso: P{alonso_pos}  |  Sainz: P{sainz_pos}")

        if dry_run:
            self.stdout.write("  [DRY RUN] No se guardaron cambios.")
            return

        # Save results to GrandPrix
        gp.result_p1 = top5_drivers[1]
        gp.result_p2 = top5_drivers[2]
        gp.result_p3 = top5_drivers[3]
        gp.result_p4 = top5_drivers[4]
        gp.result_p5 = top5_drivers[5]
        gp.result_alonso_pos = alonso_pos
        gp.result_sainz_pos = sainz_pos
        gp.save()

        self.stdout.write(self.style.SUCCESS("  Resultados guardados en BD."))

        # Auto-calculate scores for all predictions of this GP
        predictions = Prediction.objects.filter(event=gp).select_related(
            "p1", "p2", "p3", "p4", "p5", "event"
        )
        count = 0
        for pred in predictions:
            pred.score = pred.calculate_score()
            pred.save(skip_lock_check=True)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"  Puntuaciones calculadas: {count} predicciones."))

    def _get_driver_pos(self, results: list, driver_code: str) -> int:
        """Returns finishing position for a driver, 0 if DNF or not found."""
        result = next(
            (r for r in results if r["Driver"].get("code", "").upper() == driver_code),
            None,
        )
        if result is None:
            self.stdout.write(f"  AVISO: {driver_code} no encontrado en los resultados de la API.")
            return 0

        status = result.get("status", "")
        if not _is_classified_finish(status):
            return 0  # DNF

        return int(result["position"])
