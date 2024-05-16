from ailla.models import *
from ailla.serializers_collections import CollectionsSolrSerializer
from ailla.serializers_folders import FoldersSolrSerializer
from core.logger import logger
from django.core.management.base import BaseCommand
from ailla.solr import solr

class solr_query_handler:
    """
    stores solr data + submits it in batches
    """
    def __init__(self):
        self.counter = 0
        self.json_data = []
        
    def add(self, data:json):
        """add a result to list, automatically sends to solr if limit is reached"""
        self.json_data.append(data)
        self.counter += 1

        # send data in batches
        if len(self.json_data) > 20:
            solr.add(self.json_data)
            # logger.debug(self.json_data)
            self.json_data = []
            

    def send_remaining(self):
        """submit any remaining data to solr and wipe list"""
        solr.add(self.json_data)
        self.json_data = []


class Command(BaseCommand):
    """
    Management command to trigger solr reindexing
    
    Note: comment out first line if you only want to overwrite, and not delete
    """
    def handle(self, *args, **options):
        solr.delete(q='*:*') # wipes solr

        solr_handler = solr_query_handler()
        
        # Index Collections
        for collection in Collections.objects.filter(draft=False):
            collection:Collections
            solr_handler.add(CollectionsSolrSerializer(collection).data)

        # Index Folders
        for folder in Folders.objects.filter(draft=False):
            folder:Folders
            solr_handler.add(FoldersSolrSerializer(folder).data)

        solr_handler.send_remaining()
        logger.info(f"objects indexed: {solr_handler.counter}")