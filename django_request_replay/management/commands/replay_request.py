from django.core.management.base import BaseCommand, CommandError
import requests
from django_request_replay.replay import replay_request
from django_request_replay.models import ReplayRequest


class Command(BaseCommand):
    help = "Replay a captured Django request"

    def add_arguments(self, parser):
        parser.add_argument(
            "replay_request_id",
            type=int,
        )
        parser.add_argument(
           "--verbose",
           action="store_true",
           help="Print detailed information about the replayed request and response",)

    def handle(self, *args, **options):
        replay_request_id = options["replay_request_id"]

        if not ReplayRequest.objects.filter(
            id=replay_request_id
        ).exists():
            raise CommandError(
                f"ReplayRequest with id {replay_request_id} does not exist."
            )
        captured_request = ReplayRequest.objects.get(
           id=replay_request_id
         )
        try:
          response = replay_request(replay_request_id)
        except requests.exceptions.ConnectionError:
         raise CommandError(
        "Could not connect to the replay server. "
        "Make sure Django is running and REPLAY_BASE_URL is correct."
            )

        self.stdout.write(
          self.style.SUCCESS(
           f"Replay completed: "
           f"{captured_request.method} "
           f"{captured_request.path} "
           f"-> {response.status_code} "
           f"({response.replay_elapsed_time:.3f}s)"
          )
        )
        if options["verbose"]:
          self.stdout.write("")
          self.stdout.write(f"Response status: {response.status_code}")
          self.stdout.write(f"Content-Type: {response.headers.get('Content-Type')}")
          self.stdout.write(f"Response size: {len(response.content)} bytes")