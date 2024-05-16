from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Languages, Collections
from .serializers import LanguagesSerializer, TextSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .pagination_utils import SmallResultsSetPagination
from django.db.models.functions import Coalesce, Lower
from django.core.cache import cache

import json

class LanguagesViewSet(viewsets.ModelViewSet):
    queryset = Languages.objects.all()
    serializer_class = LanguagesSerializer
    pagination_class = SmallResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Get the 'lang' parameter from the query string, default to 'en' if not provided
        page_language = self.request.query_params.get('page_language', 'en')
        query = self.request.query_params.get('query', '')
        cache_key = f'languages_queryset_{page_language}_{query}'
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
            queryset = Languages.objects.annotate(
                sorted_name=Coalesce(order_field, 'name__en_neutral')
            ).select_related(
                'name', 'description', 'language_family'
            ).prefetch_related(
                'countries'
            ).filter(
                Q(id__icontains=query) | 
                Q(name__en__icontains=query) | 
                Q(name__es__icontains=query) | 
                Q(name__pt__icontains=query) |
                Q(name__en_neutral__icontains=query) | 
                Q(name__es_neutral__icontains=query) | 
                Q(name__pt_neutral__icontains=query) |
                Q(language_code__icontains=query)
            ).order_by(Lower('sorted_name'))

            cache.set(cache_key, queryset, timeout=300)
        
        return queryset


    def create(self, request, *args, **kwargs):
        user = request.user
        if is_admin_or_superadmin(user):
            return super(LanguagesViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only admins can add Languages."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_admin_or_superadmin(user):
            return super(LanguagesViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only admins can edit Languages."}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Languages."}, status=status.HTTP_403_FORBIDDEN)
        language = self.get_object()

        if language.name:
            language.name.delete()
        if language.description:
            language.description.delete()

        # Now delete the language itself
        language.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def all(self, request):
        cache_key = 'languages_all'
        languages_data = cache.get(cache_key)

        if languages_data is None:
            languages = Languages.objects.all().select_related('name')

            class LanguagesAllSerializer(serializers.ModelSerializer):
                name = TextSerializer(required=False)
                class Meta:
                    model = Languages
                    fields = ('id', 'name', 'language_code')

            serializer = LanguagesAllSerializer(languages, many=True)
            languages_data = serializer.data

            cache.set(cache_key, languages_data, timeout=300)

        return Response(languages_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def download(self, request):
        queryset = self.get_queryset()  # Get the unpaginated queryset
        serializer = LanguagesSerializer(queryset, many=True)  # Serialize the data
        return Response(serializer.data)  # Return the serialized data
    
    @action(detail=True, methods=['get'])
    def collections(self, request, pk=None):
        try:
            language = Languages.objects.get(pk=pk)
            collections = Collections.objects.filter(
                Q(collection_languages=language),
                draft=False
            ).select_related('title', 'description')
            
            return Response(SimpleCollectionsSerializer(collections, many=True).data, status=status.HTTP_200_OK)
        except Languages.DoesNotExist:
            return Response({'message': 'Language not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def test(self, request):
        languages = Languages.objects.all()[:5]

        class LanguagesAllSerializer(serializers.ModelSerializer):
            name = TextSerializer(required=False)
            class Meta:
                model = Languages
                fields = ('id', 'name', 'language_code')

        serializer = LanguagesAllSerializer(languages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def autosuggest(self, request):
        query = request.query_params.get('query', None)
        limit = request.query_params.get('limit', 10)

        # Parse limit to an integer, with error handling for invalid values
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)

        languages = Languages.objects.select_related('name').filter(
            Q(id__icontains=query) | 
            Q(name__en__icontains=query) | 
            Q(name__es__icontains=query) | 
            Q(name__pt__icontains=query) |
            Q(name__en_neutral__icontains=query) | 
            Q(name__es_neutral__icontains=query) | 
            Q(name__pt_neutral__icontains=query) |
            Q(language_code__icontains=query)
        )[:limit]

        class LanguagesAutosuggestSerializer(serializers.ModelSerializer):
            name = TextSerializer()

            class Meta:
                model = Languages
                fields = ('id', 'name', 'language_code')

        serializer = LanguagesAutosuggestSerializer(languages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def make_csv(response, page_language):
        csv_rows = []

        headers = [
            "id",
            "islandora_pid",
            f"name.{page_language}",
            "indigenous_name",
            "alternative_name",
            "language_code",
            f"countries_detail.{page_language}",
            f"language_family_detail.{page_language}",
            "macro_language",
            f"description.{page_language}"
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

                if field_name == 'language_family_detail' and isinstance(item[field_name], dict) and item[field_name] is not None:
                    name = (item[field_name].get("name") and (item[field_name]["name"].get(lang) or item[field_name]["name"].get("en"))) or ""
                    lang_obj_id = item[field_name].get('id') or ''
                    field_value = f"{name}, {lang_obj_id}"
                elif field_name == 'countries_detail' and isinstance(item[field_name], list) and item[field_name] is not None:
                    field_value_list = []
                    for lang_obj in item[field_name]:
                        name = (lang_obj.get("name") and (lang_obj["name"].get(lang) or lang_obj["name"].get("en"))) or ""
                        lang_obj_id = lang_obj.get('id') or ''
                        formatted_value = f"{name}, {lang_obj_id}"
                        field_value_list.append(formatted_value)
                    field_value = '; '.join(field_value_list)
                elif field_name in item and item[field_name] is not None:
                    if field_name == 'macro_language':
                        field_value = str(item[field_name])
                    elif isinstance(item[field_name], int):
                        field_value = str(item[field_name])
                    elif isinstance(item[field_name], str) or isinstance(item[field_name], list):
                        field_value = item[field_name]
                    else:
                        field_value = item[field_name].get(lang, '') or item[field_name].get('en', '') or ''

                if field_name == "description" and item["description"] is not None:
                    if item["description"].get('en', '') == item["description"].get('es', '') == item["description"].get('pt', ''):
                        field_value = ''
                
                if not field_value:
                    field_value = ''

                if isinstance(field_value, str) and (',' in field_value or '\n' in field_value):
                    field_value = field_value.replace('"', '""')
                    field_value = f'"{field_value}"'

                values[index] = field_value if isinstance(field_value, str) else str(field_value)
                # values.append(f'"{field_value}"' if isinstance(field_value, str) and ',' in field_value else str(field_value))

            csv_rows.append(','.join(values))

        return '\n'.join(csv_rows)