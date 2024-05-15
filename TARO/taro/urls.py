"""
Core project's URLs file. Imports all URLs from taro_manager/urls.py
"""
from django.urls import include, path

urlpatterns = [
    path('', include('taro.taro_manager.urls')),
]
