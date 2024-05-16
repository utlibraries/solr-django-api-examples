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
    
