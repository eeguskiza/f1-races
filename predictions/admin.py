from django.contrib import admin
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


@admin.register(GrandPrix)
class GrandPrixAdmin(admin.ModelAdmin):
    list_display = ["round", "name", "country", "season_year", "is_locked", "has_results"]
    list_filter = ["season_year"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [SessionInline]


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
