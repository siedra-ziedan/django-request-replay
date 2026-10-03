from django.test import SimpleTestCase , override_settings ,RequestFactory
from urllib3 import request
from io import StringIO
from django.core.management import call_command
from django_request_replay.replay import replay_request
from .redaction import redact_body, redact_headers
from .middleware import ReplayRequest, RequestReplayMiddleware
from django.http import JsonResponse, response
from django.test import TestCase
from unittest.mock import patch
from django.core.management.base import CommandError
import requests
class RedactionTests(SimpleTestCase):

    def test_sensitive_body_fields_are_redacted(self):
        body = '{"username": "sedra", "password": "secret123", "token": "abc456"}'

        result = redact_body(body)

        self.assertNotIn("secret123", result)
        self.assertNotIn("abc456", result)

        self.assertIn("[REDACTED]", result)

    def test_sensitive_headers_are_redacted(self):
        headers = {
            "Authorization": "Bearer secret-token",
            "Cookie": "session=super-secret",
            "Content-Type": "application/json",
        }

        result = redact_headers(headers)

        self.assertEqual(
            result["Authorization"],
            "[REDACTED]",
        )

        self.assertEqual(
            result["Cookie"],
            "[REDACTED]",
        )

        self.assertEqual(
            result["Content-Type"],
            "application/json",
        )
    @override_settings(MAX_BODY_SIZE=10)
    def test_large_body_is_truncated(self):
      factory = RequestFactory()

      request = factory.post(
        "/test/",
        data="a" * 20,
        content_type="text/plain",
        )      
      
      middleware = RequestReplayMiddleware(lambda request: None)

      body, truncated = middleware._get_body(request)

      self.assertEqual(body, "")
      self.assertTrue(truncated)
    def test_redact_nested_body(self):
      body = """
       {
        "user": {
            "name": "Sedra",
            "password": "secret123"
        }
        }
           """

      result = redact_body(body)

      self.assertIn('"password": "[REDACTED]"', result)
      self.assertIn('"name": "Sedra"', result)


class MiddlewareTests(TestCase):

    def test_500_response_is_captured(self):
        def fake_view(request):
            return JsonResponse(
                {"error": "Something went wrong"},
                status=500,
            )

        middleware = RequestReplayMiddleware(fake_view)

        request = RequestFactory().get("/test-error/")

        response = middleware(request)

        self.assertEqual(response.status_code, 500)

        replay_request = ReplayRequest.objects.latest("id")

        self.assertEqual(
            replay_request.path,
            "/test-error/",
        )

        self.assertEqual(
            replay_request.status_code,
            500,
        )  
    def test_exception_is_captured(self):
     def fake_view(request):
        raise ValueError("Something went wrong")

     middleware = RequestReplayMiddleware(fake_view)

     request = RequestFactory().get("/test-error/")

     with self.assertRaises(ValueError):
          middleware(request)

     replay_request = ReplayRequest.objects.latest("id")

     self.assertEqual(replay_request.path, "/test-error/")
     self.assertEqual(replay_request.status_code, 500)       

    def test_503_response_is_captured(self):
     def fake_view(request):
        return JsonResponse(
            {"error": "Service unavailable"},
            status=503,
        )

     middleware = RequestReplayMiddleware(fake_view)

     request = RequestFactory().get("/test-503/")

     response = middleware(request)

     self.assertEqual(response.status_code, 503)

     replay_request = ReplayRequest.objects.latest("id")

     self.assertEqual(replay_request.path, "/test-503/")
     self.assertEqual(replay_request.status_code, 503)    

    def test_sensitive_data_is_redacted_before_storage(self):
      def fake_view(request):
        return JsonResponse(
            {"error": "Something went wrong"},
            status=500,
        )

      middleware = RequestReplayMiddleware(fake_view)

      request = RequestFactory().post(
        "/login/",
        data='{"username":"sedra","password":"secret123","token":"abc456"}',
        content_type="application/json",
        )

      response = middleware(request)

      self.assertEqual(response.status_code, 500)

      replay_request = ReplayRequest.objects.latest("id")

      self.assertNotIn("secret123", replay_request.body)
      self.assertNotIn("abc456", replay_request.body)
      self.assertIn("[REDACTED]", replay_request.body)

    def test_replay_request_is_not_captured_again(self):
      def fake_view(request):
        return JsonResponse(
            {"error": "Something went wrong"},
            status=500,
        )

      middleware = RequestReplayMiddleware(fake_view)

      request = RequestFactory().get(
        "/test-error/",
        HTTP_X_DJANGO_REPLAY="1",
      )

      response = middleware(request)

      self.assertEqual(response.status_code, 500)

      self.assertEqual(
        ReplayRequest.objects.count(),
        0,
      )
    def test_sensitive_headers_are_redacted_before_storage(self):
      def fake_view(request):
        return JsonResponse(
            {"error": "Something went wrong"},
            status=500,
        )

      middleware = RequestReplayMiddleware(fake_view)

      request = RequestFactory().get(
        "/test/",
        HTTP_AUTHORIZATION="Bearer super-secret-token",
        HTTP_COOKIE="session=super-secret",
        )

      response = middleware(request)

      self.assertEqual(response.status_code, 500)

      replay_request = ReplayRequest.objects.latest("id")

      self.assertEqual(
        replay_request.headers["Authorization"],
        "[REDACTED]",
       )

      self.assertEqual(
        replay_request.headers["Cookie"],
        "[REDACTED]",
        )

    @override_settings(MAX_BODY_SIZE=10)
    def test_large_body_is_not_stored(self):
      def fake_view(request):
        return JsonResponse(
            {"error": "Something went wrong"},
            status=500,
        )

      middleware = RequestReplayMiddleware(fake_view)

      request = RequestFactory().post(
        "/upload/",
        data="a" * 100,
        content_type="text/plain",
        )

      response = middleware(request)

      self.assertEqual(response.status_code, 500)

      replay_request = ReplayRequest.objects.latest("id")

      self.assertEqual(replay_request.body, "")
      self.assertTrue(replay_request.body_truncated)

    def test_query_params_are_captured(self):
      def fake_view(request):
        return JsonResponse(
            {"error": "Something went wrong"},
            status=500,
        )

      middleware = RequestReplayMiddleware(fake_view)

      request = RequestFactory().get(
        "/search/?page=2&category=books"
        )

      response = middleware(request)

      self.assertEqual(response.status_code, 500)
 
      replay_request = ReplayRequest.objects.latest("id")

      self.assertEqual( replay_request.query_params,{"page": "2", "category": "books"}  
        )

    def test_content_type_is_preserved(self):
      def fake_view(request):
        return JsonResponse(
            {"error": "Something went wrong"},
            status=500,
        )

      middleware = RequestReplayMiddleware(fake_view)

      request = RequestFactory().post(
        "/test/",
        data='{"name":"sedra"}',
        content_type="application/json",
      )

      response = middleware(request)

      self.assertEqual(response.status_code, 500)

      replay_request = ReplayRequest.objects.latest("id")

      self.assertEqual(
        replay_request.headers["Content-Type"],
        "application/json",
      
     )
    @patch("django_request_replay.replay.requests.request")
    def test_replay_sends_query_params(self, mock_request):
       replay_request = ReplayRequest.objects.create(
        method="GET",
        path="/search/",
        query_params={
            "page": "2",
            "category": "books",
        },
        headers={},
        body="",
        status_code=500,
    )

       mock_response = mock_request.return_value
       mock_response.status_code = 200
       mock_response.headers = {}
       mock_response.content = b"OK"

       from django_request_replay.replay import replay_request as run_replay

       run_replay(replay_request.id)

       mock_request.assert_called_once()

       call_kwargs = mock_request.call_args.kwargs

       self.assertEqual(
        call_kwargs["params"],
        {
            "page": "2",
            "category": "books",
        },
           )    

    @patch("django_request_replay.replay.requests.request")
    def test_replay_preserves_method_and_url(self, mock_request):
      replay_request = ReplayRequest.objects.create(
        method="POST",
        path="/api/orders/",
        query_params={},
        headers={},
        body='{"item": "book"}',
        status_code=500,
    )

      mock_response = mock_request.return_value
      mock_response.status_code = 200
      mock_response.headers = {}
      mock_response.content = b"OK"

      from django_request_replay.replay import (
        replay_request as run_replay,
      )

      run_replay(replay_request.id)

      call_kwargs = mock_request.call_args.kwargs

      self.assertEqual(call_kwargs["method"], "POST")
      self.assertEqual(
        call_kwargs["url"],
        "http://127.0.0.1:8000/api/orders/",
         )   
    @patch("django_request_replay.replay.requests.request")
    def test_replay_sends_body(self, mock_request):
      replay_request = ReplayRequest.objects.create(
        method="POST",
        path="/api/orders/",
        query_params={},
        headers={
            "Content-Type": "application/json",
        },
        body='{"item": "book"}',
        status_code=500,
    )

      mock_response = mock_request.return_value
      mock_response.status_code = 200
      mock_response.headers = {}
      mock_response.content = b"OK"

      from django_request_replay.replay import (
        replay_request as run_replay,
       )

      run_replay(replay_request.id)

      call_kwargs = mock_request.call_args.kwargs

      self.assertEqual(
        call_kwargs["data"],
        '{"item": "book"}',
       )  

    @patch("django_request_replay.replay.requests.request")
    def test_replay_does_not_send_sensitive_headers(self, mock_request):
      replay_request = ReplayRequest.objects.create(
        method="GET",
        path="/private/",
        query_params={},
        headers={
            "Authorization": "[REDACTED]",
            "Cookie": "[REDACTED]",
            "Content-Type": "application/json",
        },
        body="",
        status_code=500,
       )

      mock_response = mock_request.return_value
      mock_response.status_code = 200
      mock_response.headers = {}
      mock_response.content = b"OK"

      from django_request_replay.replay import (
        replay_request as run_replay,
        )

      run_replay(replay_request.id)

      call_kwargs = mock_request.call_args.kwargs
      headers = call_kwargs["headers"]

      self.assertNotIn("Authorization", headers)
      self.assertNotIn("Cookie", headers)

      self.assertEqual(
        headers["Content-Type"],
        "application/json",
        )  
    @patch("django_request_replay.management.commands.replay_request.replay_request")
    def test_replay_management_command(self, mock_replay):
      replay_request = ReplayRequest.objects.create(
        method="GET",
        path="/test/",
        query_params={},
        headers={},
        body="",
        status_code=500,
    )

      mock_response = mock_replay.return_value
      mock_response.status_code = 200
      mock_response.headers = {
         "Content-Type": "application/json",
       }
      mock_response.content = b'{"ok": true}'
      mock_response.replay_elapsed_time = 0.123

      output = StringIO()

      call_command(
        "replay_request",
        str(replay_request.id),
        stdout=output,
      )

      mock_replay.assert_called_once_with(
        replay_request.id
     )
      self.assertIn(
        "Replay completed",
        output.getvalue(),
      )  
    @override_settings(REPLAY_ENABLED=False)
    def test_replay_disabled(self):
     with self.assertRaises(RuntimeError):
        replay_request(1)

    @override_settings(REPLAY_ENABLED=False)
    def test_replay_command_when_disabled(self):
      ReplayRequest.objects.create(
        method="GET",
        path="/test-error/",
        status_code=500,
      )

      with self.assertRaises(RuntimeError):
        call_command("replay_request", 1)

    def test_replay_command_connection_error(self):
      ReplayRequest.objects.create(
        method="GET",
        path="/test-error/",
        status_code=500,
      )

      with patch(
        "django_request_replay.management.commands.replay_request.replay_request",
        side_effect=requests.exceptions.ConnectionError,
        ):
        with self.assertRaises(CommandError) as context:
            call_command("replay_request", 1)

      self.assertIn(
        "Could not connect to the replay server",
        str(context.exception),
      )    