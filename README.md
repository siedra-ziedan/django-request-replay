# django-request-replay
# django-request-replay

A Django library for capturing and replaying failed HTTP requests locally.

[PyPI](https://pypi.org/project/django-request-replay/0.1.1/) 

Replay failed Django HTTP requests locally.

## The Problem

Some Django errors are difficult to reproduce.

A request may fail in production or staging, but reproducing the exact request locally can be difficult.

`django-request-replay` captures failed requests and allows developers to replay them later.

## How It Works

```text
HTTP Request
     ↓
Django Middleware
     ↓
Request fails
     ↓
Capture safely
     ↓
ReplayRequest
     ↓
Developer finds the request ID
     ↓
python manage.py replay_request <id>
     ↓
Request is replayed locally
Installation
Install the package with pip:
pip install django-request-replay
Add the app to INSTALLED_APPS:
INSTALLED_APPS = [
    ...
    "django_request_replay",
]
Add the middleware:
MIDDLEWARE = [
    "django_request_replay.middleware.RequestReplayMiddleware",
    ...
]
Run migrations:
python manage.py migrate
Configuration
Add the following settings to your Django project:
REPLAY_BASE_URL = "http://127.0.0.1:8000"
REPLAY_ENABLED = True
By default, the middleware captures:
500
502
503
504
You can customize the captured status codes:
REPLAY_STATUS_CODES = [500, 502, 503, 504]
The request body is limited to 10 MB by default:
MAX_BODY_SIZE = 10 * 1024 * 1024
Usage
List Captured Requests
To see captured failed requests:
python manage.py replay_requests
Example:
ID    METHOD    PATH                     STATUS
------------------------------------------------
12    POST      /api/payment/            500
11    GET       /api/profile/            503
10    POST      /api/orders/             500
You can filter by status code:
python manage.py replay_requests --status 500
Limit the number of results:
python manage.py replay_requests --limit 5
Combine filters:
python manage.py replay_requests --status 500 --limit 5
Replay a Request
Once you know the request ID:
python manage.py replay_request 12
Example:
Replay completed: POST /api/payment/ -> 500 (0.145s)
The request is sent again to the configured REPLAY_BASE_URL.
Verbose Mode
Use --verbose to see additional response information:
python manage.py replay_request 12 --verbose
Example:
Replay completed: POST /api/payment/ -> 500 (0.145s)

Response status: 500
Content-Type: text/html
Response size: 4218 bytes
Security
Sensitive request data is redacted before being stored.
Sensitive Headers
The following headers are redacted by default:
Authorization
Cookie
Set-Cookie
X-API-Key
Sensitive Body Fields
The following JSON fields are redacted:
password
token
secret
api_key
Example:
{
    "username": "sedra",
    "password": "[REDACTED]",
    "token": "[REDACTED]"
}
Nested JSON objects and lists are also handled recursively.
Sensitive authentication headers are not sent during replay.
Large Request Bodies
Request bodies larger than the configured limit are not stored.
Instead, the request is marked as truncated:
body_truncated = True
This helps prevent the replay database from growing unexpectedly because of very large request bodies.
Replay Protection
Replayed requests include a special header:
X-Django-Replay: 1
The middleware detects this header and does not capture the replayed request again.
This prevents an infinite capture loop:
Replay request
     ↓
Fails again
     ↓
Captured again
     ↓
Replayed again
     ↓
...
Testing
Run the test suite with:
python example/manage.py test django_request_replay
The project includes tests for:
Request redaction
Header redaction
Nested JSON redaction
Failed request capture
Exception capture
5xx responses
Body truncation
Query parameters
Replay behavior
Sensitive headers
Replay loop prevention
Management commands
Disabled replay
Connection errors
Project Structure

django-request-replay/
│
├── django_request_replay/
│   ├── middleware.py
│   ├── models.py
│   ├── redaction.py
│   ├── replay.py
│   ├── admin.py
│   ├── tests.py
│   └── management/
│       └── commands/
│           ├── replay_request.py
│           └── replay_requests.py
│
├── example/
│   ├── manage.py
│   └── config/
│
├── pyproject.toml
├── README.md
└── .gitignore

License
MIT
