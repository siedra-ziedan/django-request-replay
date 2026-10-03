from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
from django.http import HttpResponse
from django.http import JsonResponse


def test_error(request):
    raise Exception("This is a test error")


@csrf_exempt
def test_sensitive(request):
    data = request.body
    raise Exception("Sensitive data test")



def test_503(request):
    return JsonResponse(
        {"error": "Service unavailable"},
        status=503,
    )