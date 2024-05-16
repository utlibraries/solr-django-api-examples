from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from math import ceil

# Create your views here.
class SmallResultsSetPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'per_page'
    max_page_size = 100

    def get_paginated_response(self, data):
        client_page_size = self.request.query_params.get(self.page_size_query_param)
        page_size = int(client_page_size) if client_page_size else self.page_size

        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': ceil(self.page.paginator.count / page_size),
            'results': data
        })