# AILLA

## Purpose
This folder contains some snippets of our [AILLA](ailla.lib.utexas.edu) site's backend code, specifically the code that pertains to the solr
integration. You can run the application locally using Docker and docker-compose. You can check that the application came up as expected 
by hitting the /health endpoint, which should reuturn OK.

## Setting up Solr
In this repo we use pysolr to connect to solr cloud. We connect to solr in the AILLA/src/ailla/solr.py file. You will need to fill out two variables in 
settings.py in order to connect to your own solr instance: SOLR_URL and SOLR_COLLECTION.

## Solr Serialization Examples
AILLA's metadata structure is defined in a relational database which can be seen in models.py. Each model has several serializers,
including a solr serializer which flattens the data structure. We have left these models/serializers in this repo as examples of how 
you can serialize a model to be added to solr, and how we use these serializers to store data in solr. However, we've removed the 
views and other code that interacts with these models, so you won't be able to use the methods or serializers without adding additional code.

## Search Endpoint Example
There are two search endpoints, which trigger views in ailla/search.py. These search endpoints accept queries that are already formatted 
in solr's search syntax. Example queries are provided as comments in search.py. More information about formatting solr queries can be found 
in the [Standard Query Parser documentation](https://solr.apache.org/guide/6_6/the-standard-query-parser.html#TheStandardQueryParser-StandardQueryParserParameters). AILLA's search allows searching the Collections, Folders, Items/Sets and Files models stored in AILLA.

Our frontend search calls both of these methods when performing a search. The SearchView performs a simple search on the query, and the 
AuthorityFileFacetsView performs a facet search on the same query using AILLA's authority objects (Persons, Organizations, Countries, 
and Languages). The facet search is performed on 14 solr fields that store authority file information for the Collections/Folders/Sets/Items/Files 
on the site. The solr fields that represent facets end in _facet, to distinguish them from other fields. 

We return the results of the simple search, as well as the number of search results relevant to each facet, every time a search is performed. 
Users can then use the frontend features to change which results are displayed using the facets.

## Solr Management Command
This repo contains a solr management command, located at AILLA/src/ailla/management/commands/solr_index.py, which triggers solr reindexing.
This command reads our database and re-adds all the information to solr. It does this in batches to avoid overwhelming the solr server.

## Other Information
AILLA has many other features, such as ingesting and transforming new AV/image content, user administration/account management, metadata 
management, and allowing for viewing images and AV on the site using iiif, wowza and cantaloupe. We have removed most of these features from
this repo to keep things relevant to the django/solr integration, but some imports still remain. 

AILLA is also a trilingual site. Data is stored in English, Spanish and Portuguese. We have seprate fields for the metadata in each langauge,
but the facet fields in solr take the data from all three languages and concatenate it to faciliate faceting.

Feel free to contact us if you have any questions at LIT-Squid-Storm@austin.utexas.edu.

## Running Locally
After cloning this repo, navigate to the AILLA directory where Dockerfile.local is located. Make sure you have Docker and docker compose installed 
locally. Then, you can run this project with ``docker compose up``. 

In AILLA/src/core/settings.py, you will need to fill in the SOLR_COLLECTION and the SOLR_URL in order to query your own solr instance. 
