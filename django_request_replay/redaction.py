import json


SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
}

SENSITIVE_BODY_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
}


def redact_headers(headers):
    redacted = {}

    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value

    return redacted

def _redact_value(value):
    if isinstance(value, dict):
        redacted = {}

        for key, item in value.items():
            if key.lower() in SENSITIVE_BODY_KEYS:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = _redact_value(item)

        return redacted

    if isinstance(value, list):
        return [_redact_value(item) for item in value]

    return value


def redact_body(body):
    if not body:
        return body

    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return body

    return json.dumps(_redact_value(data))