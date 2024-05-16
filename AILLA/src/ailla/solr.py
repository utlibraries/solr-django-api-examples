import pysolr
import os

from django.conf import settings

"""Solr connection instance using environement settings: SOLR_URL and SOLR_COLLECTION"""
solr = pysolr.Solr(
    url=f"{settings.SOLR_URL}/{settings.SOLR_COLLECTION}",
    always_commit=True,
    timeout=30,
    auth=None,
)
