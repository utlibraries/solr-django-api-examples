import pysolr
import os

"""Solr connection instance using environement settings: SOLR_URL and SOLR_COLLECTION"""
solr = pysolr.Solr(
    url=f"{os.environ.get('SOLR_URL')}/{os.environ.get('SOLR_COLLECTION')}",
    always_commit=True,
    timeout=30,
    auth=None,
)
