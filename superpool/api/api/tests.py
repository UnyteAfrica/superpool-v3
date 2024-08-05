from django.test import TestCase
import pytest
from rest_framework.test import APIClient

# WE WOULD BE TESTING OUR MIDDLEWARE SINCE ITS MEANT TO INTERACT WITH
# THE REQUEST AND RESPONSE OBJECTS


def test_request_authenticated_with_middleware_and_correct_credentials():
    pass


def test_request_unauthenticated_with_middleware_and_incorrect_credentials():
    pass


def test_request_unauthenticated_with_middleware_and_no_credentials():
    pass
