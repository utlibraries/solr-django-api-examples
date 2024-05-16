
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import MediaContentType, Genre, ParticipantRoles, OriginalMediaType
from .serializers import MediaContentTypeSerializer, GenreSerializer, ParticipantRolesSerializer, OriginalMediaTypeSerializer, TextSerializer
from django.db.models import Q
from rest_framework.permissions import IsAuthenticatedOrReadOnly



class MediaContentTypesViewSet(viewsets.ModelViewSet):
    depth = 0
    queryset = MediaContentType.objects.all()
    serializer_class = MediaContentTypeSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = MediaContentType.objects.select_related(
            'name',
            'description',
        )

        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        if is_superadmin(user):
            return super(MediaContentTypesViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only superadmins can create Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_superadmin(user):
            return super(MediaContentTypesViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only superadmins can edit Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
        media_content_type = self.get_object()

        if media_content_type.name:
            media_content_type.name.delete()
        if media_content_type.description:
            media_content_type.description.delete()

        # Now delete the media_content_type itself
        media_content_type.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def all(self, request):

        media_content_type = MediaContentType.objects.select_related('name', 'description').all()

        class MediaContentTypeAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = MediaContentType
                fields = ('id', 'name', 'description')

        serializer = MediaContentTypeAllSerializer(media_content_type, many=True)
        media_content_type_data = serializer.data

        return Response(media_content_type_data, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['get'])
    def autosuggest(self, request):
        query = request.query_params.get('query', None)
        limit = request.query_params.get('limit', 10)

        # Parse limit to an integer, with error handling for invalid values
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)

        mediaContentTypes = MediaContentType.objects.select_related('name', 'description').filter(
            Q(id__icontains=query) | 
            Q(name__en__icontains=query) | 
            Q(name__es__icontains=query) | 
            Q(name__pt__icontains=query)
        )[:limit]

        class MediaContentTypeAutosuggestSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = MediaContentType
                fields = ('id', 'name', 'description')

        serializer = MediaContentTypeAutosuggestSerializer(mediaContentTypes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GenreViewSet(viewsets.ModelViewSet):
    depth = 0
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Genre.objects.select_related(
            'name',
            'description',
        )
    
        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        if is_superadmin(user):
            return super(GenreViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only superadmins can create Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_superadmin(user):
            return super(GenreViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only superadmins can edit Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
        genre = self.get_object()

        if genre.name:
            genre.name.delete()
        if genre.description:
            genre.description.delete()

        # Now delete the genre itself
        genre.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def all(self, request):
        genre_list = Genre.objects.select_related('name', 'description').all()

        class GenreAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = Genre
                fields = ('id', 'name', 'description')

        serializer = GenreAllSerializer(genre_list, many=True)
        genre_data = serializer.data

        return Response(genre_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def autosuggest(self, request):
        query = request.query_params.get('query', None)
        limit = request.query_params.get('limit', 10)

        # Parse limit to an integer, with error handling for invalid values
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)

        genres = Genre.objects.select_related('name','description').filter(
            Q(id__icontains=query) | 
            Q(name__en__icontains=query) | 
            Q(name__es__icontains=query) | 
            Q(name__pt__icontains=query)
        )[:limit]

        class GenreAutosuggestSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = Genre
                fields = ('id', 'name', 'description')

        serializer = GenreAutosuggestSerializer(genres, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ParticipantRolesViewSet(viewsets.ModelViewSet):
    depth = 0
    queryset = ParticipantRoles.objects.all()
    serializer_class = ParticipantRolesSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_queryset(self):
        queryset = ParticipantRoles.objects.select_related(
            'name',
            'description',
        )

        return queryset


    def create(self, request, *args, **kwargs):
        user = request.user
        if is_superadmin(user):
            return super(ParticipantRolesViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only superadmins can create Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_superadmin(user):
            return super(ParticipantRolesViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only superadmins can edit Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
        participant_role = self.get_object()

        if participant_role.name:
            participant_role.name.delete()
        if participant_role.description:
            participant_role.description.delete()

        # Now delete the participant_role itself
        participant_role.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        participant_roles = ParticipantRoles.objects.select_related('name', 'description').all()

        class ParticipantRolesAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = ParticipantRoles
                fields = ('id', 'name', 'description')

        serializer = ParticipantRolesAllSerializer(participant_roles, many=True)
        participant_roles_data = serializer.data


        return Response(participant_roles_data, status=status.HTTP_200_OK)
        
    @action(detail=False, methods=['get'])
    def autosuggest(self, request):
        query = request.query_params.get('query', None)
        limit = request.query_params.get('limit', 10)

        # Parse limit to an integer, with error handling for invalid values
        try:
            limit = int(limit)
        except ValueError:
            return Response({'error': 'Invalid limit parameter'}, status=status.HTTP_400_BAD_REQUEST)

        participantRoles = ParticipantRoles.objects.select_related('name', 'description').filter(
            Q(id__icontains=query) | 
            Q(name__en__icontains=query) | 
            Q(name__es__icontains=query) | 
            Q(name__pt__icontains=query)
        )[:limit]

        class ParticipantRolesAutosuggestSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = ParticipantRoles
                fields = ('id', 'name', 'description')

        serializer = ParticipantRolesAutosuggestSerializer(participantRoles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OriginalMediaTypeViewSet(viewsets.ModelViewSet):
    depth = 0
    queryset = OriginalMediaType.objects.all()
    serializer_class = OriginalMediaTypeSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly]


    def get_queryset(self):
        queryset = OriginalMediaType.objects.select_related(
            'name',
            'description',
        )
            
        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        if is_superadmin(user):
            return super(OriginalMediaTypeViewSet, self).create(request, *args, **kwargs)
        return Response({"detail": "Only superadmins can create Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def update(self, request, *args, **kwargs):
        user = request.user

        if is_superadmin(user):
            return super(OriginalMediaTypeViewSet, self).update(request, *args, **kwargs)
        
        return Response({"detail": "Only superadmins can edit Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
    
    def destroy(self, request, pk=None):
        user = request.user
        if not is_superadmin(user):
            return Response({"detail": "Only superadmins can delete Controlled Vocabulary."}, status=status.HTTP_403_FORBIDDEN)
        original_media_type = self.get_object()

        if original_media_type.name:
            original_media_type.name.delete()
        if original_media_type.description:
            original_media_type.description.delete()

        # Now delete the original_media_type itself
        original_media_type.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def all(self, request):
        original_media_type = OriginalMediaType.objects.select_related('name', 'description').all()

        class OriginalMediaTypeAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = OriginalMediaType
                fields = ('id', 'name', 'description')

        serializer = OriginalMediaTypeAllSerializer(original_media_type, many=True)
        original_media_type_data = serializer.data


        return Response(original_media_type_data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def audio(self, request):
        original_media_type = OriginalMediaType.objects.filter(name__en__icontains='audio').select_related('name', 'description').all()

        class OriginalMediaTypeAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = OriginalMediaType
                fields = ('id', 'name', 'description')

        serializer = OriginalMediaTypeAllSerializer(original_media_type, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def image(self, request):
        original_media_type = OriginalMediaType.objects.filter(name__en__icontains='image').select_related('name', 'description').all()

        class OriginalMediaTypeAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = OriginalMediaType
                fields = ('id', 'name', 'description')

        serializer = OriginalMediaTypeAllSerializer(original_media_type, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def text(self, request):
        original_media_type = OriginalMediaType.objects.filter(name__en__icontains='text').select_related('name', 'description').all()

        class OriginalMediaTypeAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = OriginalMediaType
                fields = ('id', 'name', 'description')

        serializer = OriginalMediaTypeAllSerializer(original_media_type, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def video(self, request):
        original_media_type = OriginalMediaType.objects.filter(name__en__icontains='video').select_related('name', 'description').all()

        class OriginalMediaTypeAllSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = OriginalMediaType
                fields = ('id', 'name', 'description')

        serializer = OriginalMediaTypeAllSerializer(original_media_type, many=True)
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

        originalMediaTypes = OriginalMediaType.objects.select_related('name', 'description').filter(
            Q(id__icontains=query) | 
            Q(name__en__icontains=query) | 
            Q(name__es__icontains=query) | 
            Q(name__pt__icontains=query)
        )[:limit]

        class OriginalMediaTypeAutosuggestSerializer(serializers.ModelSerializer):
            name = TextSerializer()
            description = TextSerializer()

            class Meta:
                model = OriginalMediaType
                fields = ('id', 'name', 'description')

        serializer = OriginalMediaTypeAutosuggestSerializer(originalMediaTypes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

