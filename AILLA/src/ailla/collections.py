from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django.db.models import Prefetch
from rest_framework import viewsets, status, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from ailla.serializers_folders import SimpleFoldersSerializer
from core.logger import logger
from django.db import transaction
from ailla.solr import solr

from core.logger import logger
from .models import Collections, Text, Persons, Languages, Countries, Organizations, Folders, Items, File
from .serializers import TextSerializer
from .serializers_collections import CollectionsSerializer, CollectionsSolrSerializer
from .serializers_folders import FoldersSolrSerializer

from .pagination_utils import SmallResultsSetPagination
from django.db.models import Q
from django.db.models.functions import Coalesce, Lower
from django.core.cache import cache


class CollectionsViewSet(viewsets.ModelViewSet):
    serializer_class = CollectionsSerializer
    pagination_class = SmallResultsSetPagination
    queryset = Collections.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Get the 'page_language' parameter from the query string, default to 'en' if not provided
        page_language = self.request.query_params.get('page_language', 'en')
        query = self.request.query_params.get('query', '')       
        cache_key = f'collections_queryset_{page_language}_{query}'
        queryset = cache.get(cache_key)

        if queryset is None:
            # Define a mapping between page_language codes and Collections title fields
            page_language_field_mapping = {
                'en': 'title__en_neutral',
                'es': 'title__es_neutral',
                'pt': 'title__pt_neutral',
            }
            
            # Get the appropriate field name for sorting based on the passed page_language
            order_field = page_language_field_mapping.get(page_language, 'title__en_neutral')

            # Fallback to English neutral if the specified page_language title is empty
            queryset = Collections.objects.annotate(
                sorted_title=Coalesce(order_field, 'title__en_neutral')
            ).select_related(
                'title',
                'description',
                'lang_indigenous_title',
                'lang_indigenous_description'
            ).prefetch_related(
                Prefetch('collectors_persons', queryset=Persons.objects.only('id', 'given_name', 'surname')),
                Prefetch('collectors_orgs', queryset=Organizations.objects.select_related('org_name')),
                Prefetch('depositors_persons', queryset=Persons.objects.only('id', 'given_name', 'surname')),
                Prefetch('depositors_orgs', queryset=Organizations.objects.select_related('org_name')),
                Prefetch('collection_languages', queryset=Languages.objects.select_related('name')),
                Prefetch('countries', queryset=Countries.objects.select_related('name')),
            ).filter(
                Q(id__icontains=query) |
                Q(title__en__icontains=query) |
                Q(title__es__icontains=query) |
                Q(title__pt__icontains=query) |
                Q(title__en_neutral__icontains=query) |
                Q(title__es_neutral__icontains=query) |
                Q(title__pt_neutral__icontains=query)
            ).order_by(Lower('sorted_title'))
            
            cache.set(cache_key, queryset, timeout=300)
        
        return queryset
    
    @action(detail=False, methods=['GET'])
    def get_published(self, request):
        queryset = self.get_queryset().filter(draft=False)
        page = self.paginate_queryset(queryset)  # Paginate the queryset
        serialized_data = CollectionsSerializer(page, many=True).data
        return self.get_paginated_response(serialized_data)
    
    @action(detail=False, methods=['GET'])
    def get_drafts(self, request):
        user = request.user

        # Check if the user is authenticated
        if not user.is_authenticated:
            return Response({"detail": "You must be logged in to access this resource."}, status=status.HTTP_401_UNAUTHORIZED)

        # Ensure the user has a profile attached and their role is 'ADMIN'
        if is_admin_or_superadmin(user):
            queryset = self.get_queryset().filter(draft=True)
            
            # Directly serialize the entire queryset without pagination
            serialized_data = CollectionsSerializer(queryset, many=True).data
            
            return Response(serialized_data)
        
        return Response({"detail": "Only admins can see collections in draft status."}, status=status.HTTP_403_FORBIDDEN)
        
    def create(self, request, *args, **kwargs):
        user = request.user
        # Ensure the user has a profile attached and their role is 'ADMIN'
        if is_admin_or_superadmin(user):
            return super(CollectionsViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only admins can create collections."}, status=status.HTTP_403_FORBIDDEN)

    
    def update(self, request, *args, **kwargs):
        user = request.user
        collection_instance = self.get_object()

        if has_edit_permission(user, collection_instance):
            return super(CollectionsViewSet, self).update(request, *args, **kwargs)
        return Response({"detail": "You don't have the necessary permissions to update this collection."}, status=status.HTTP_403_FORBIDDEN)


    @action(detail=False, methods=['get'])
    def all(self, request):
        collections = Collections.objects.all().select_related('title')

        class CollectionsAllSerializer(serializers.ModelSerializer):
            title = TextSerializer(required=False)
            class Meta:
                model = Collections
                fields = ('id', 'title')

        serializer = CollectionsAllSerializer(collections, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def children(self, request: Request, pk):
        """lists folders that belong to a specific collection

        Returns:
            list: list of json objects + http 200
        """

        folders = Collections.objects.get(pk=pk).folders.all().select_related('title', 'description')
        return Response(SimpleFoldersSerializer(folders, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def publish(self, request: Request, pk=None):
        # if not is_admin_or_superadmin(request.user):
        #     return Response({"detail": "Only admins or superadmins can publish this collection."}, status=status.HTTP_403_FORBIDDEN)

        # Change DRAFT on Collection to False
        collection = self.get_object()
        collection.draft = False
        collection.save()

        # Add to Solr
        solr_data = []
        collection_data = CollectionsSolrSerializer(collection).data
        solr_data.append(collection_data)

        folders = Folders.objects.filter(parent_collection=collection.id)
        if folders:
            for folder in folders:
                folder.draft = False
                folder.save()

                folder_data = FoldersSolrSerializer(folder).data
                solr_data.append(folder_data)

                items = Items.objects.filter(parent_folder=folder.id)
                if items:
                    for item in items:
                        item.draft = False
                        item.save()

                        item_data = ItemsSolrSerializer(item).data
                        solr_data.append(item_data)

                        files = File.objects.filter(parent_item=item.id)
                        if files:
                            for file in files:
                                file_data = FilesSolrSerializer(file).data
                                solr_data.append(file_data)

        solr.add(solr_data)

        return Response(CollectionsSerializer(collection).data, status=status.HTTP_200_OK)