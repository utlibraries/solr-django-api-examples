"""
Taro Custom Serializers. More info: https://www.django-rest-framework.org/api-guide/serializers/
"""
from drf_haystack.serializers import HaystackSerializer, HaystackFacetSerializer

from taro.taro_manager.search_indexes import FindingAidIndex, CreatorIndex, \
    AllowListIndex, RepositoryIndex, FindingAidDisplayIndex


class FindingAidSearchSerializer(HaystackSerializer):   # pylint: disable=abstract-method
    """
    Finding Aid Haystack Search Serializer
    """
    class Meta:   # pylint: disable=abstract-method,too-few-public-methods
        """
        Set index class as FindingAidIndex and set fields as: text, title, abstract, digital,
        repo, date added and file name
        """
        index_classes = [FindingAidIndex]
        fields = ['text', 'title', 'digital', 'abstract', 'repository', 'repository_name', 'date_added', 'last_modified', 'filename', 'languages',
                  'creators', 'start_dates', 'end_dates', 'geographic_areas', 'subject_topics',
                  'subject_persons', 'subject_organizations', 'extents', 'genreforms', 'inclusive_dates', 'taro_identifier']


class FindingAidDisplaySerializer(HaystackSerializer):   # pylint: disable=abstract-method
    """
    Finding Aid Haystack Display Serializer
    """
    class Meta:   # pylint: disable=abstract-method,too-few-public-methods
        """
        Returns fields needed for TARO front-end display
        """
        index_classes = [FindingAidDisplayIndex]
        fields = ['text', 'value', 'repository', 'filename',]


class FindingAidFacetSerializer(HaystackFacetSerializer):
    class Meta:
        index_classes = [FindingAidIndex]
        fields = ["title", "repository", "languages", "start_dates", "end_dates", "geographic_areas", "subject_topics", "subject_persons", "subject_organizations", "extents", "genreforms", "inclusive_dates"]
        field_options = {
            "title": {},
            "repository": {},
            "languages": {},
            "start_dates": {},
            "end_dates": {},
            "geographic_areas": {},
            "subject_topics": {},
            "subject_persons": {},
            "subject_organizations": {},
            "extents": {},
            "genreforms": {},
            "inclusive_dates": {}
        }


class RepositorySearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [RepositoryIndex]
        fields = ['name', 'description', 'external_email', 'logo', 'home_link', 'about_link', 'access_link', 'address',
                  'abbr_name', 'taro_identifier',]


class CreatorSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [CreatorIndex]
        fields = ['name',]


class AllowListSearchSerializer(HaystackSerializer):
    class Meta:
        index_classes = [AllowListIndex]
        fields = ['label', 'browse_terms',]
        