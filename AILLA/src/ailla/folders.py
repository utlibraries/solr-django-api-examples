import os
import requests
import re

from django.db.models import Prefetch
from django.http import QueryDict
from rest_framework import viewsets, status, serializers
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from core.logger import logger
from django.db import transaction

from .models import Folders, Genre, Items, Persons, Organizations, Countries, Languages, Text, File, Collections
from .serializers import TextSerializer
from .serializers_folders import FoldersSerializer

class FoldersViewSet(viewsets.ModelViewSet):
    serializer_class = FoldersSerializer
    pagination_class = None
    queryset = Folders.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Folders.objects.select_related(
            'parent_collection',
            'parent_collection__title',
            'title',
            'description',
            'lang_indigenous_title',
            'lang_indigenous_description',
        ).prefetch_related(
            Prefetch('subject_languages', queryset=Languages.objects.select_related('name')),
            Prefetch('countries', queryset=Countries.objects.select_related('name')),
        )
    
    def create(self, request, *args, **kwargs):
        user = request.user

        parent_instance = Collections.objects.get(id=request.data['parent_collection'])

        if has_create_permission(user, parent_instance):
            return super().create(request, *args, **kwargs)
        return Response({"detail": "You don't have the necessary permissions to create in this collection."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user
        folder_instance = self.get_object()

        if has_edit_permission(user, folder_instance):
            return super(FoldersViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "You don't have the necessary permissions to edit this folder."}, status=status.HTTP_403_FORBIDDEN)

    
    def destroy(self, request, pk=None):
        user = request.user
        instance = self.get_object()
        if not instance.draft:
            if not is_superadmin(user):
                return Response({"detail": "Only superadmins can delete published folders."}, status=status.HTTP_403_FORBIDDEN)
        else:
            if not has_edit_permission(user, instance):
                return Response({"detail": "User does not have required permissions to delete this folder."}, status=status.HTTP_403_FORBIDDEN)
        folder_id = instance.id
        with transaction.atomic(): 
            folder = Folders.objects.get(id=folder_id)

            # Delete all text objects referenced in folder
            ## Foreign-key text object fields are: name, description
            folder_title_id = folder.title.id
            folder_description_id = folder.description.id
            
            # Delete items and files
            items = Items.objects.filter(parent_folder=folder_id)
            if items:
                for item in items:
                    item_id = item.id
                    item_name_id = item.name.id
                    logger.debug(f"ITEM NAME TEXT OBJECT ID{item_name_id}")
                    item_name_text = Text.objects.get(id=item_name_id)
                    item_name_text.delete()
                    
                    item_description_id = item.description.id
                    item_description_text = Text.objects.get(id=item_description_id)
                    item_description_text.delete()

                    # Delete item
                    item.delete()

            # Delete folder
            folder.delete()

            # Delete folder title text object
            folder_title_text = Text.objects.get(id=folder_title_id)
            folder_title_text.delete()

            # Delete folder description text object
            folder_description_text = Text.objects.get(id=folder_description_id)
            folder_description_text.delete()


            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['GET'])
    def user_role(self, request, pk=None):
        folder = self.get_object()
        role = get_object_user_role(request.user, folder)
        return Response({'role': role})
    
    @action(detail=True, methods=['GET'])
    def get_owners(self, request, pk=None):
        """
        Retrieve a list of owners for a specific folder.

        Parameters:
        - request: The current request object.
        - pk (optional): The primary key of the folder. Might be required due to route configuration.

        Returns:
        - Response: A DRF Response containing a list of owner details for the folder.
        """
        try:
            folder_instance = self.get_object()
            owners = get_object_owners(folder_instance)
            return Response(owners, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": "An error occurred while fetching folder owners."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        folders = Folders.objects.all().select_related('title')

        class FoldersAllSerializer(serializers.ModelSerializer):
            title = TextSerializer(required=False)
            class Meta:
                model = Folders
                fields = ('id', 'title')

        serializer = FoldersAllSerializer(folders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk):
        """lists items that belong to a specific folder

        Returns:
            list: list of json objects + http 200
        """

        folder = Folders.objects.prefetch_related(
                Prefetch('items', queryset=Items.objects.select_related('name', 'description').prefetch_related(
                    Prefetch('genre', queryset=Genre.objects.select_related('name','description'))
                ))
            ).get(pk=pk)
        items = folder.items.all()
        return Response(SimpleItemsSerializer(items, many=True).data, status=status.HTTP_200_OK)
