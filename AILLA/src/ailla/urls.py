from django.urls import path, include, re_path
from django.contrib import admin
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers

from .organizations import OrganizationsViewSet
from .countries import CountriesViewSet
from .languages import LanguagesViewSet
from .controlled_vocabularies import  MediaContentTypesViewSet,GenreViewSet, ParticipantRolesViewSet, OriginalMediaTypeViewSet
from .collections import CollectionsViewSet
from .folders import FoldersViewSet
from .contributor_roles import ContributorRoleViewSet
from .search import SearchView
from .search import AuthorityFileFacetsView
from . import views

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'collections', CollectionsViewSet)
router.register(r'folders', FoldersViewSet)

router.register(r'organizations', OrganizationsViewSet)
router.register(r'languages', LanguagesViewSet)
router.register(r'countries', CountriesViewSet)

router.register(r'contributorroles', ContributorRoleViewSet)
router.register(r'genres', GenreViewSet)
router.register(r'participantroles', ParticipantRolesViewSet)
router.register(r'mediacontenttype', MediaContentTypesViewSet)
router.register(r'originalmediatype', OriginalMediaTypeViewSet)


"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

urlpatterns = [
    path('', include(router.urls)),
    path('admin/', admin.site.urls),
    path('search/', SearchView.as_view(), name='search'),
    path('facets/', AuthorityFileFacetsView.as_view(), name='facets'),
    path('health/', views.health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)