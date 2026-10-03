from django.db import models


class ReplayRequest(models.Model):
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    query_params = models.JSONField(default=dict)
    headers = models.JSONField(default=dict)
    body = models.TextField(blank=True)
    body_truncated = models.BooleanField(default=False)
    status_code = models.PositiveIntegerField()
    user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)