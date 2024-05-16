from rest_framework import viewsets
from .models import ContributorRole
from .serializers import ContributorRoleSerializer

class ContributorRoleViewSet(viewsets.ModelViewSet):
    depth = 1
    queryset = ContributorRole.objects.all()
    serializer_class = ContributorRoleSerializer