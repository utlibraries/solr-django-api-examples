# solr-django-api-examples
Examples of using Python/Django to create an API layer for Solr queries.

## AILLA

## TARO
This is a stripped down version of the Search API that the Texas Archival Resources Online application uses to power the search & display functionality for the front end site ([txarchives.org](txarchives.org)) and provides metadata to the TARO OAI-PMH service.

This Search API uses a mix of [Django Haystack](https://django-haystack.readthedocs.io/en/master/) and custom solr queries which can be seen in views.py. solr_query.py contains the conversion logic that builds a solr query out of the parameters passed to the API for the custom query (FindingAidSearchViewSet). 

