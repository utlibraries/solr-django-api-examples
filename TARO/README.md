# TARO

## Purpose
This is a stripped down version of the Search API that the Texas Archival Resources Online application uses to power the search & display functionality for the front end site ([txarchives.org](txarchives.org)) and provides metadata to the TARO OAI-PMH service.

This Search API uses a mix of [Django Haystack](https://django-haystack.readthedocs.io/en/master/) AND custom solr queries which can be seen in views.py. solr_query.py contains the conversion logic that builds a solr query out of the parameters passed to the API for the custom query (FindingAidSearchViewSet). 

## Setting up Solr
To test the Solr integration, you would need to add a local_settings.py file in the same directory as settings.py and define two environment variables: SOLR_URL and SOLR_COLLECTION. These variables are used to point haystack and the custom solr queries at the appropriate Solr collection.

## Search & Display Endpoint Examples
TARO uses both [Django Haystack](https://django-haystack.readthedocs.io/en/master/) and the (now no longer supported) [DRF-Haystack](https://drf-haystack.readthedocs.io/en/latest/) libraries to integrate with Solr in a Django-y way. All endpoints defined in views.py inherit from HaystackViewSet. The FindingAidSearchViewSet view was later refactored to bypass the haystack functionality and make a custom solr query instead, which is defined in solr_query.py.

Most of these endpoints are used for search; however, TARO also has a FindingAidDisplayViewSet endpoint, which is used to provide a blob of json that the front end site uses to generate ReactJS components. 

finding_aid_display/search: returns blob of json used for display
finding_aid/search: the custom Solr query for searching finding aids
repository/search: DRF-Haystack query for repositories
creators/search: DRF-Haystack query for creators
allowlists/search: DRF-Haystack query for allowlists (pre-canned browse/search queries)

## Solr Management Command
Management commands are built-in via [Haystack](https://django-haystack.readthedocs.io/en/latest/management_commands.html)

## Other Information
Some of this repository was originally built inside of the taro-2 back end service that also hosts the administrative portal for the site. This Search API was later abstracted out of that service and stood up on its own - so there may be some remnants from the original repository that were left in this repository.

Our experience with haystack was mixed. The built-in management commands are convenient, and the back end service (not featured in this repository) uses a combination of Django signals and haystack to make automatic indexing/reindexing of the Solr collection easy. That said, haystack has yet to offer support for Solr versions past 7, and the search endpoints were not very performant (hence the custom solr query to replace it).

In retrospect, this service would probably be best built as a pure API (without any DB integration), using a lighter-weight framework like Flask and making all custom solr queries.

## Running Locally
We use Docker for development and docker compose for local development. After closing this repository, you can run this project with ``docker compose up``. 