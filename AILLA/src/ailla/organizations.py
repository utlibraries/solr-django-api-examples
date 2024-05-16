from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Organizations, Text, Languages, Collections, ContributorRole
from .serializers import OrganizationsSerializer, TextSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .pagination_utils import SmallResultsSetPagination
from django.db.models.functions import Coalesce, Lower
from django.core.cache import cache

import json

class OrganizationsViewSet(viewsets.ModelViewSet):
    queryset = Organizations.objects.all()
    serializer_class = OrganizationsSerializer
    pagination_class = SmallResultsSetPagination
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        # Get the 'lang' parameter from the query string, default to 'en' if not provided
        page_language = self.request.query_params.get('page_language', 'en')
        query = self.request.query_params.get('query', '')
        cache_key = f'organizations_queryset_{page_language}_{query}'
        queryset = cache.get(cache_key)
                
        if queryset is None:
            # Define a mapping between page_language codes and model fields
            page_language_field_mapping = {
                'en': 'org_name__en_neutral',
                'es': 'org_name__es_neutral',
                'pt': 'org_name__pt_neutral',
            }
            
            # Get the appropriate field name for sorting based on the passed page_language
            order_field = page_language_field_mapping.get(page_language, 'org_name__en_neutral')
            
            # Fallback to English if the specified page_language name is empty
            queryset = Organizations.objects.annotate(
                sorted_name=Coalesce(order_field, 'org_name__en_neutral')
            ).select_related(
                'org_name', 'description'
            ).prefetch_related(
                'research_languages__name', 
                'research_languages__description'
            ).filter(
                Q(id__icontains=query) | 
                Q(org_name__en__icontains=query) | 
                Q(org_name__es__icontains=query) | 
                Q(org_name__pt__icontains=query) |
                Q(org_name__en_neutral__icontains=query) |
                Q(org_name__es_neutral__icontains=query) |
                Q(org_name__pt_neutral__icontains=query)
            ).order_by(Lower('sorted_name'))

            cache.set(cache_key, queryset, timeout=300)
        
        return queryset

    
    def create(self, request, *args, **kwargs):
        user = request.user
        if is_admin_or_superadmin(user):
            return super(OrganizationsViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only admins can add Organizations."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_admin_or_superadmin(user):
            return super(OrganizationsViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only admins can edit Organizations."}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Organizations."}, status=status.HTTP_403_FORBIDDEN)
        organization = self.get_object()

        if organization.org_name:
            organization.org_name.delete()
        if organization.description:
            organization.description.delete()

        # Now delete the organization itself
        organization.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        cache_key = 'organizations_all'
        organizations_data = cache.get(cache_key)

        if organizations_data is None:
            organizations = Organizations.objects.all().select_related("org_name")

            class OrganizationsAllSerializer(serializers.ModelSerializer):
                org_name = TextSerializer(required=False)
                class Meta:
                    model = Organizations
                    fields = ('id', 'org_name', 'acronym')

            serializer = OrganizationsAllSerializer(organizations, many=True)
            organizations_data = serializer.data

            cache.set(cache_key, organizations_data, timeout=300)

        return Response(organizations_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def download(self, request):
        queryset = self.get_queryset()  # Get the unpaginated queryset
        serializer = OrganizationsSerializer(queryset, many=True)  # Serialize the data
        return Response(serializer.data)  # Return the serialized data
    
    @action(detail=True, methods=['get'])
    def collections(self, request, pk=None):
        try:
            organization = Organizations.objects.get(pk=pk)
            collections = Collections.objects.filter(
                Q(collectors_orgs=organization) | Q(depositors_orgs=organization),
                draft=False
            ).select_related('title', 'description')
            
            return Response(SimpleCollectionsSerializer(collections, many=True).data, status=status.HTTP_200_OK)
        except Organizations.DoesNotExist:
            return Response({'message': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
        
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        try:
            organization = Organizations.objects.get(pk=pk)
            contributor_roles = ContributorRole.objects.filter(organization=organization).select_related('item','item__name','item__description')
            items = [role.item for role in contributor_roles if role.item.draft is False]

            return Response(SimpleItemsSerializer(items, many=True).data, status=status.HTTP_200_OK)
        except Organizations.DoesNotExist:
            return Response({'message': 'organization not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def autosuggest(self, request):
        query = request.query_params.get('query', None)
        limit = request.query_params.get('limit', 10)

        # Parse limit to an integer, with error handling for invalid values
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)

        organizations = Organizations.objects.select_related('org_name').filter(
            Q(id__icontains=query) | 
            Q(org_name__en__icontains=query) | 
            Q(org_name__es__icontains=query) | 
            Q(org_name__pt__icontains=query) |
            Q(org_name__en_neutral__icontains=query) |
            Q(org_name__es_neutral__icontains=query) |
            Q(org_name__pt_neutral__icontains=query)
        )[:limit]

        class OrganizationsAutosuggestSerializer(serializers.ModelSerializer):
            org_name = TextSerializer()

            class Meta:
                model = Organizations
                fields = ('id', 'org_name')

        serializer = OrganizationsAutosuggestSerializer(organizations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    