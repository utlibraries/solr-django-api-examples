from rest_framework import viewsets, status, serializers
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from django.core.cache import cache

from ailla.solr import solr

''' Performs a simple search using the q parameter in the solr syntax.

On AILLA, queries might look like search/?q=Nahuatl or search/?q=Bolivia. 

Searches can also be complex. For example search/?q=Nahuatl&genre_en:'wordlist' will find
all documents related to Nahuatl that also have the solr field genre_en set to the value 
wordlist. You can search on any solr field with this general pattern:
    [SOLR FIELD NAME]:'value'

Solr also allows other types of complex queries. See the solr documentation for examples.
'''
class SearchView(ListAPIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        cache_key = f'solr_search_{query}'
        results = cache.get(cache_key)

        if results is not None:
            return Response(results)

        start, rows = 0, 1000  # Fetch 1000 documents at a time (adjust as needed)
        results = []

        while True:
            response_data = solr.search(query, rows=rows, start=start).raw_response.get('response', {})
            docs = response_data.get('docs', [])

            results.extend(docs)

            num_found = response_data.get('numFound', 0)
            start += len(docs)

            if start >= num_found:
                break

        cache.set(cache_key, results, timeout=300)
        
        return Response(results)
    
class AuthorityFileFacetsView(ListAPIView):
    def get(self, request):
        query = request.query_params.get('q', '')
        facet_fields = [
            "collectors_orgs_en_facet",
            "collectors_orgs_es_facet",
            "collectors_orgs_pt_facet",
            "collectors_persons_facet",
            "contributors_orgs_en_facet",
            "contributors_orgs_es_facet",
            "contributors_orgs_pt_facet",
            "contributors_persons_facet",
            "countries_en_facet",
            "countries_es_facet",
            "countries_pt_facet",
            "languages_en_facet",
            "languages_es_facet",
            "languages_pt_facet",
        ]
        cache_key = f'solr_facets_{query}'
        facet_data = cache.get(cache_key)

        if facet_data is None:
            try:
                facet_data = {}
                for facet_field in facet_fields:
                    facet_counts_dict = {}
                    start = 0
                    rows = 1000  # Fetch 1000 documents at a time (adjust as needed)
                    while True:
                        params = {
                            "indent": "true",
                            "facet": "true",
                            "rows": rows,
                            "start": start,
                            "facet.field": facet_field,
                        }
                        response = solr.search(query, **params)
                        
                        if response is None:
                            break
                        
                        solr_dict = response.raw_response
                        facet_counts = solr_dict.get('facet_counts', {}).get('facet_fields', {}).get(facet_field, [])
                        facet_counts_dict.update({facet_counts[i]: facet_counts[i + 1] for i in range(0, len(facet_counts), 2) if facet_counts[i]})
                        facet_counts_dict = dict(sorted(facet_counts_dict.items()))

                        if len(facet_counts) < rows:
                            break  # No more facet data to fetch
                        
                        start += rows
                    
                    facet_data[facet_field] = facet_counts_dict

                cache.set(cache_key, facet_data, timeout=300)

                return Response(facet_data)

            except Exception as e:
                return Response({"Error fetching authority file facets: ": str(e)}, status=500)
    
        return Response(facet_data)