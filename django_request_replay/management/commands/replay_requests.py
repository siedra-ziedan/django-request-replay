from django.core.management.base import BaseCommand

from django_request_replay.models import ReplayRequest


class Command(BaseCommand):
    help = "List captured failed requests"

    def handle(self, *args, **options):
        requests = ReplayRequest.objects.order_by("-created_at")

        if not requests.exists():
            self.stdout.write("No captured requests found.")
            return

        self.stdout.write(
            f"{'ID':<6}"
            f"{'METHOD':<10}"
            f"{'PATH':<40}"
            f"{'STATUS':<10}"
            f"CREATED"
        )

        self.stdout.write("-" * 90)

        for request in requests:
            self.stdout.write(
                f"{request.id:<6}"
                f"{request.method:<10}"
                f"{request.path:<40}"
                f"{request.status_code:<10}"
                f"{request.created_at}"
            )