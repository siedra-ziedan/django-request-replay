import requests

from .models import ReplayRequest

from django.conf import settings


def get_replay_data(replay_request_id):
    replay_request = ReplayRequest.objects.get(
        id=replay_request_id
    )

    return {
        "method": replay_request.method,
        "path": replay_request.path,
        "query_params": replay_request.query_params,
        "headers": replay_request.headers,
        "body": replay_request.body,
    }

import time
def replay_request(replay_request_id):
    if not getattr(settings, "REPLAY_ENABLED", True):
      raise RuntimeError(
        "Django request replay is disabled."
      )
    data = get_replay_data(replay_request_id)
    base_url = getattr(
    settings,
    "REPLAY_BASE_URL",
    "http://127.0.0.1:8000",
     ) 
    url = base_url + data["path"]
    headers = {
    key: value
    for key, value in data["headers"].items()
    if key.lower() not in {
        "content-length",
        "host",
        "connection",
        "transfer-encoding",
        "cookie",
        "authorization",
        "proxy-authorization",
    }
}
    headers["X-Django-Replay"] = "1"
    start_time = time.perf_counter()

    response = requests.request(
     method=data["method"],
     url=url,
     params=data["query_params"],
     headers=headers,
     data=data["body"],
      )

    elapsed_time = time.perf_counter() - start_time
    response.replay_elapsed_time = elapsed_time
    return response