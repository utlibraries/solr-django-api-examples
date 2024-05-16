import requests
import os
from django.http import HttpResponse
from core.logger import logger

""" Health check endpoint. """
def health_check(request):
    return HttpResponse("OK")

