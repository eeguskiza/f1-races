from django.db import migrations


def cancel_races(apps, schema_editor):
    GrandPrix = apps.get_model("predictions", "GrandPrix")
    GrandPrix.objects.filter(
        season_year=2026,
        slug__in=["bahrain-gp", "saudi-gp"],
    ).update(cancelled=True)


def uncancel_races(apps, schema_editor):
    GrandPrix = apps.get_model("predictions", "GrandPrix")
    GrandPrix.objects.filter(
        season_year=2026,
        slug__in=["bahrain-gp", "saudi-gp"],
    ).update(cancelled=False)


class Migration(migrations.Migration):

    dependencies = [
        ("predictions", "0005_cancelled_grandprix"),
    ]

    operations = [
        migrations.RunPython(cancel_races, uncancel_races),
    ]
