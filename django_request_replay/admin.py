from django.contrib import admin

from .models import ReplayRequest


@admin.register(ReplayRequest)
class ReplayRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "method",
        "path",
        "status_code",
        "body_truncated",
        "created_at",
    )
    list_filter = ("status_code", "body_truncated", "method")
    search_fields = ("path", "method")