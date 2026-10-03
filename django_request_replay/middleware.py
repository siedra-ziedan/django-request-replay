from .models import ReplayRequest
from .redaction import redact_headers , redact_body
from django.conf import settings

class RequestReplayMiddleware:
    def __init__(self, get_response):
      self.get_response = get_response

      self.status_codes = getattr(
        settings,
        "REPLAY_STATUS_CODES",
        [500, 502, 503, 504],
          )

      self.max_body_size = getattr(
        settings,
        "MAX_BODY_SIZE",
        10 * 1024 * 1024,
      )
    def _get_body(self, request):
      body = request.body
      if len(body) > self.max_body_size:
        return "", True
      return redact_body(
              body.decode("utf-8", errors="replace")
          ), False
    def _save_request(self, request, status_code):
      body, body_truncated = self._get_body(request)

      user = getattr(request, "user", None)

      ReplayRequest.objects.create(
        method=request.method,
        path=request.path,
        query_params=request.GET.dict(),
        headers=redact_headers(request.headers),
        body=body,
        body_truncated=body_truncated,
        status_code=status_code,
        user_id=(
            str(user.pk)
            if user is not None and user.is_authenticated
            else None
        ),
           )
    def __call__(self, request):
      if request.headers.get("X-Django-Replay") == "1":
        return self.get_response(request)
      try:
        response = self.get_response(request)

      except Exception:
        self._save_request(request, 500)
        raise

      if response.status_code in self.status_codes:
        self._save_request(request, response.status_code)
      return response

