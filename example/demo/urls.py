from django.urls import path
from .views import test_error, test_sensitive, test_503

urlpatterns = [
    path("test-error/", test_error),
    path("test-sensitive/", test_sensitive),
    path("test-503/", test_503),
]



