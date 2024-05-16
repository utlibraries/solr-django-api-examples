from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Countries, Collections
from .serializers import CountriesSerializer, TextSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .pagination_utils import SmallResultsSetPagination
from django.db.models.functions import Coalesce, Lower
from django.core.cache import cache

import json

class CountriesViewSet(viewsets.ModelViewSet):
    queryset = Countries.objects.all()
    serializer_class = CountriesSerializer
    pagination_class = SmallResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Get the 'lang' parameter from the query string, default to 'en' if not provided
        page_language = self.request.query_params.get('page_language', 'en')
        query = self.request.query_params.get('query', '')
        cache_key = f'countries_queryset_{page_language}_{query}'
        queryset = cache.get(cache_key)
        if queryset is None:
            # Define a mapping between page_language codes and model fields
            page_language_field_mapping = {
                'en': 'name__en_neutral',
                'es': 'name__es_neutral',
                'pt': 'name__pt_neutral',
            }
            
            # Get the appropriate field name for sorting based on the passed page_language
            order_field = page_language_field_mapping.get(page_language, 'name__en_neutral')
            
            # Fallback to English if the specified page_language name is empty
            queryset = Countries.objects.annotate(
                sorted_name=Coalesce(order_field, 'name__en_neutral')
            ).select_related(
                'name',
            ).filter(
                Q(id__icontains=query) | 
                Q(name__en__icontains=query) | 
                Q(name__es__icontains=query) | 
                Q(name__pt__icontains=query) |
                Q(name__en_neutral__icontains=query) | 
                Q(name__es_neutral__icontains=query) | 
                Q(name__pt_neutral__icontains=query) |
                Q(country_code__icontains=query)
            ).order_by(Lower('sorted_name'))

            cache.set(cache_key, queryset, timeout=300)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        user = request.user
        if is_admin_or_superadmin(user):
            return super(CountriesViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only admins can add Countries."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_admin_or_superadmin(user):
            return super(CountriesViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only admins can edit Countries"}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Countries"}, status=status.HTTP_403_FORBIDDEN)

        country = self.get_object()

        if country.name:
            country.name.delete()

        # Now delete the country itself
        country.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    

    @action(detail=False, methods=['get'])
    def all(self, request):
        cache_key = 'countries_all'
        countries_data = cache.get(cache_key)

        if countries_data is None:
            countries = Countries.objects.all().select_related('name')

            class CountriesAllSerializer(serializers.ModelSerializer):
                name = TextSerializer(required=False)
                class Meta:
                    model = Countries
                    fields = ('id', 'name', 'country_code', 'flag_code')

            serializer = CountriesAllSerializer(countries, many=True)
            countries_data = serializer.data

            cache.set(cache_key, countries_data, timeout=300)

        return Response(countries_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def download(self, request):
        queryset = self.get_queryset()  # Get the unpaginated queryset
        serializer = CountriesSerializer(queryset, many=True)  # Serialize the data
        return Response(serializer.data)  # Return the serialized data
    
    @action(detail=True, methods=['get'])
    def collections(self, request, pk=None):
        try:
            country = Countries.objects.get(pk=pk)
            collections = Collections.objects.filter(
                Q(countries=country),
                draft=False
            ).select_related('title', 'description')
            
            return Response(SimpleCollectionsSerializer(collections, many=True).data, status=status.HTTP_200_OK)
        except Countries.DoesNotExist:
            return Response({'message': 'country not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def autosuggest(self, request):
        query = request.query_params.get('query', None)
        limit = request.query_params.get('limit', 10)

        # Parse limit to an integer, with error handling for invalid values
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)

        countries = Countries.objects.select_related('name').filter(
            Q(id__icontains=query) | 
            Q(name__en__icontains=query) | 
            Q(name__es__icontains=query) | 
            Q(name__pt__icontains=query) |
            Q(name__en_neutral__icontains=query) | 
            Q(name__es_neutral__icontains=query) | 
            Q(name__pt_neutral__icontains=query) |
            Q(country_code__icontains=query)
        )[:limit]

        class CountriesAutosuggestSerializer(serializers.ModelSerializer):
            name = TextSerializer()

            class Meta:
                model = Countries
                fields = ('id', 'name', 'flag_code', 'country_code')

        serializer = CountriesAutosuggestSerializer(countries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def make_csv(response, page_language):
        csv_rows = []
        headers = [
            "id",
            f"name.{page_language}",
            "islandora_pid",
            "country_code",
            "viaf",
            "flag_code",
        ]
        csv_rows.append(','.join(headers))

        response_content = response.content.decode('utf-8')

        # Load JSON from the content
        data = json.loads(response_content)

        for item in data:
            values = [None] * len(headers)

            for index, key in enumerate(headers):
                field_name, lang = key.split('.') if '.' in key else (key, 'en')
                field_value = ''

                if field_name in item and item[field_name] is not None:
                    if isinstance(item[field_name], int):
                        field_value = str(item[field_name])
                    elif isinstance(item[field_name], str) or isinstance(item[field_name], list):
                        field_value = item[field_name]
                    else:
                        field_value = item[field_name].get(lang, '') or item[field_name].get('en', '') or ''

                if isinstance(field_value, str) and (',' in field_value or '\n' in field_value):
                    field_value = field_value.replace('"', '""')
                    field_value = f'"{field_value}"'

                values[index] = field_value if isinstance(field_value, str) else str(field_value)

            csv_rows.append(','.join(values))

        return '\n'.join(csv_rows)