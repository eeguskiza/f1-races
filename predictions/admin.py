from django.contrib import admin
from django.contrib import messages
from .models import Team, Driver, GrandPrix, Session, Prediction, NewsPost


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "color", "active"]
    list_filter = ["active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "team", "active"]
    list_filter = ["active", "team"]
    search_fields = ["code", "name"]


class SessionInline(admin.TabularInline):
    model = Session
    extra = 0
    ordering = ["order"]


def calculate_scores(modeladmin, request, queryset):
    """Admin action: calculate scores for all predictions of selected GPs."""
    updated = 0
    skipped = 0
    for gp in queryset:
        if not gp.has_results:
            skipped += 1
            continue
        predictions = Prediction.objects.filter(event=gp).select_related(
            "p1", "p2", "p3", "p4", "p5", "event"
        )
        for pred in predictions:
            pred.score = pred.calculate_score()
            pred.save(skip_lock_check=True)
            updated += 1

    if updated:
        messages.success(request, f"Puntuaciones calculadas: {updated} predicciones actualizadas.")
    if skipped:
        messages.warning(request, f"{skipped} GP(s) sin resultados completos — omitidos.")

calculate_scores.short_description = "Calcular puntuaciones"


@admin.register(GrandPrix)
class GrandPrixAdmin(admin.ModelAdmin):
    list_display = ["round", "name", "country", "season_year", "is_locked", "has_results"]
    list_filter = ["season_year"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SessionInline]
    actions = [calculate_scores]


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["event", "session_type", "start_utc", "order"]
    list_filter = ["session_type", "event__season_year"]


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ["user", "event", "score", "submitted_at"]
    list_filter = ["event"]
    raw_id_fields = ["user", "p1", "p2", "p3", "p4", "p5"]


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at", "has_image"]
    list_filter = ["created_at"]
    search_fields = ["title", "body"]
    fieldsets = [
        (None, {"fields": ["title", "body"]}),
        ("Imagen", {"fields": ["image_url"], "classes": ["collapse"]}),
    ]

    @admin.display(boolean=True, description="Imagen")
    def has_image(self, obj):
        return bool(obj.image_url)
