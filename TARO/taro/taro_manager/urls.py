"""
Taro Manager URLs file. For more info: https://docs.djangoproject.com/en/3.1/topics/http/urls/
"""
from django.urls import path
from django.conf import urls
from rest_framework import routers

from taro.taro_manager.views import FindingAidSearchViewSet, CreatorSearchViewSet, \
    AllowListSearchViewSet, RepositorySearchViewSet, FindingAidDisplayViewSet

router = routers.DefaultRouter()
router.register(r'finding_aid_display/search', FindingAidDisplayViewSet, basename="finding-aid-display")
router.register(r'repository/search', RepositorySearchViewSet, basename="repository-search")
router.register(r'finding_aid/search', FindingAidSearchViewSet, basename="finding-aid-search")
router.register(r'creators/search', CreatorSearchViewSet, basename="creator-search")
router.register(r'allowlists/search', AllowListSearchViewSet, basename="allowlist-search")

app_name = 'taro_manager'   # pylint: disable=invalid-name

urlpatterns = [
    path('api/', urls.include(router.urls)),
    path('api-auth/', urls.include('rest_framework.urls')),
]