# pylint: disable=no-self-use,too-many-ancestors
"""
Taro Search API Views. For more info: https://docs.djangoproject.com/en/3.1/topics/http/views/
"""
import json
import requests

from django.http import HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.db.utils import OperationalError
from django.views.decorators.cache import cache_page
from drf_haystack.viewsets import HaystackViewSet
from drf_haystack.mixins import FacetMixin
from haystack.query import SearchQuerySet
from rest_framework.response import Response

from taro.taro_manager.models import FindingAid, Repository, Creator, \
    AllowList, FindingAidDisplayField
from taro.taro_manager.serializers import FindingAidSearchSerializer,  \
    CreatorSearchSerializer, AllowListSearchSerializer, \
    RepositorySearchSerializer, FindingAidFacetSerializer, FindingAidDisplaySerializer
# from taro.taro_manager.utilities import ExceptionalUserRateThrottle, is_deployed_react_app
from taro.taro_manager.solr_query import SolrQuery
from taro.taro_manager.logger import logger


class FindingAidDisplayViewSet(FacetMixin, HaystackViewSet):
    index_models = [FindingAidDisplayField]
    serializer_class = FindingAidDisplaySerializer
    # throttle_classes = [ExceptionalUserRateThrottle]

    def list(self, request, *args, **kwargs):
        params = self.request.query_params
        if not params:
            return Response("Only one finding aid display may be returned at a time. Please specify a repository and filename in the search query.", status=400)
        
        queryset = SearchQuerySet().models(FindingAidDisplayField)
        queryset = self.filter_queryset(queryset)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class FindingAidSearchViewSet(FacetMixin, HaystackViewSet):
    """
    Welcome to the Open TARO Finding Aid Search API!\n
    This open API is available is accessible by anyone but was designed with researchers and data harvesters in mind.
    This API is also what powers the TARO search & browse features on the [public display site](https://www.txarchives.org).\n
    *Anonymous requests are currently limited to 100 per hour.*
    See documentation at at https://txarchives.org/search-api
    """
    index_models = [FindingAid]
    serializer_class = FindingAidSearchSerializer
    # throttle_classes = [ExceptionalUserRateThrottle]
    facet_serializer_class = FindingAidFacetSerializer
    facet_query_params_text = 'params'  # default is "selected_facets"
    # See https://django-haystack.readthedocs.io/en/latest/faceting.html#configuring-facet-behaviour
    # and https://drf-haystack.readthedocs.io/en/latest/07_faceting.html#
    # for additional faceting configuration options.

    # def dispatch(self, *args, **kwargs):
    #     try:
    #         return super(FindingAidSearchViewSet, self).dispatch(*args, **kwargs)
    #     except OperationalError as e:
    #         return JsonResponse({'error': 'An invalid authorization token was provided.'}, status=400)

    # @method_decorator(cache_page(60 * 60 * 6))  # caching search results for 6 hours
    def list(self, request, *args, **kwargs):
        """
        Overriding list() method to make our own custom Solr queries
        instead of relying on built-in Haystack generated Solr queries.
        """
        params = self.request.query_params
        solr_query = SolrQuery()
        # from_front_end = is_deployed_react_app(request)
        # if from_front_end == False:
        #     logger.debug(f"Search API Request from {request.user}")
        custom_solr_query = solr_query.build_query(params=params, frontend_request=False)
        solr_results = requests.get(url=custom_solr_query)
        content = solr_results.content
        decoded = content.decode('utf8')
        if json.loads(decoded).get('error'):
            return HttpResponse(json.dumps(json.loads(decoded).get('error')), status=400)
        cleaned = json.loads(decoded).get('response').get('docs')
        # if from_front_end == False:
        
        for fa in cleaned:
            fa.update({"display_site": f"txarchives.org/{fa['repository']}/finding_aids/{fa['filename']}"})
            fa.update({"xml": f"txarchives.org/admin/{fa['repository']}/{fa['filename']}"})
            

        return Response(cleaned, status=200)


class RepositorySearchViewSet(HaystackViewSet):
    """
    Repository View Set - where you can see all the repositories
    """
    index_models = [Repository]
    serializer_class = RepositorySearchSerializer
    # throttle_classes = [ExceptionalUserRateThrottle]

    # def dispatch(self, *args, **kwargs):
    #     try:
    #         return super(RepositorySearchViewSet, self).dispatch(*args, **kwargs)
    #     except OperationalError as e:
    #         return JsonResponse({'error': 'An invalid authorization token was provided.'}, status=400)

    # @method_decorator(cache_page(60 * 60 * 24))  # caching repository search results for 24 hours
    def list(self, request, *args, **kwargs):
        """
        Overriding list() method to provide cached repository results. The below is copy-pasted
        from Django source code. (The method decorator is all that's needed to cache results.)
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CreatorSearchViewSet(HaystackViewSet):
    index_models = [Creator]
    # throttle_classes = [ExceptionalUserRateThrottle]
    serializer_class = CreatorSearchSerializer

    # @method_decorator(cache_page(60 * 60 * 24))  # caching creator search results for 6 hours
    def list(self, request, *args, **kwargs):
        """
        Overriding list() method to provide cached creator results. The below is copy-pasted
        from Django source code. (The method decorator is all that's needed to cache results.)
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AllowListSearchViewSet(HaystackViewSet):
    """
    These refer to browse-by categories that are defined by
    TARO member (specifically TARO Admin) provided "allow lists".
    """
    index_models = [AllowList]
    # throttle_classes = [ExceptionalUserRateThrottle]
    serializer_class = AllowListSearchSerializer

    # @method_decorator(cache_page(60 * 60 * 24))  # caching allowlist search results for 6 hours
    def list(self, request, *args, **kwargs):
        """
        Overriding list() method to provide cached allowlist results. The below is copy-pasted
        from Django source code. (The method decorator is all that's needed to cache results.)
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
