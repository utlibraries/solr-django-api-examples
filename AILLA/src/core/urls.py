from django.urls import include, re_path, path
from django.contrib import admin
from rest_framework import routers

app_name = "ailla"

urlpatterns = [
    re_path(r'', include('ailla.urls')),
    path("debug/", include("debug_toolbar.urls")),
]
