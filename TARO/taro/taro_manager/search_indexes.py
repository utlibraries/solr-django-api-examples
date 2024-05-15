"""
Haystack Finding Aid Search Index. More info:
https://django-haystack.readthedocs.io/en/v2.3.2/searchindex_api.html
"""
import json
import datetime
from haystack import indexes
from haystack.fields import SearchField
from taro.taro_manager.utilities import resolve_attributes_lookup
from taro.taro_manager.models import FindingAid, Creator, AllowList, Repository, FindingAidDisplayField

# This is patching a method in the Haystack SearchField to class to
# accommodate M2M fields appropriately. 
SearchField.resolve_attributes_lookup = classmethod(resolve_attributes_lookup)


class FindingAidDisplayIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    value = indexes.CharField(model_attr='value')
    repository = indexes.CharField(model_attr='repository__abbr_name')
    filename = indexes.CharField(model_attr='filename')
    taro_identifier = indexes.CharField(model_attr='taro_identifier')
    date_created = indexes.DateTimeField(model_attr='date_created')
    last_modified = indexes.DateTimeField(model_attr='last_modified')

    def get_model(self):
        return FindingAidDisplayField

    def prepare_value(self, object):
        return json.dumps(object.value)


class FindingAidIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Finding Aid Index. Note that only the text field is full text
    searchable. See Haystack docs for more details.
    """
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', faceted=True)
    abstract = indexes.CharField(model_attr='abstract')
    digital = indexes.BooleanField(model_attr='digital')
    repository = indexes.CharField(model_attr='repository__abbr_name', faceted=True)
    repository_name = indexes.CharField(model_attr='repository__name')
    date_added = indexes.DateTimeField(model_attr='date_added')
    filename = indexes.CharField(model_attr='filename')
    languages = indexes.MultiValueField(model_attr='languages', faceted=True)
    creators = indexes.MultiValueField(model_attr='creators', faceted=True)
    start_dates = indexes.MultiValueField(model_attr='start_dates', faceted=True)
    end_dates = indexes.MultiValueField(model_attr='end_dates', faceted=True)
    geographic_areas = indexes.MultiValueField(model_attr='geographic_areas', faceted=True)
    subject_topics = indexes.MultiValueField(model_attr='subject_topics', faceted=True)
    subject_persons = indexes.MultiValueField(model_attr='subject_persons', faceted=True)
    subject_organizations = indexes.MultiValueField(model_attr='subject_organizations', faceted=True)
    extents = indexes.MultiValueField(model_attr='extents', faceted=True)
    genreforms = indexes.MultiValueField(model_attr='genreforms', faceted=True)
    inclusive_dates = indexes.MultiValueField(model_attr='inclusive_dates', faceted=True)
    taro_identifier = indexes.CharField(model_attr='taro_identifier')
    last_modified = indexes.DateTimeField(model_attr='last_modified')

    def get_model(self):
        return FindingAid

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(date_added__lte=datetime.datetime.now())   # pylint: disable=no-member

    def prepare_languages(self, object):
        return [language.label for language in object.languages.all()]
    
    def prepare_creators(self, object):
        return [creator.name for creator in object.creators.all()]
    
    def prepare_start_dates(self, object):
        return [start_date.date for start_date in object.start_dates.all()]
    
    def prepare_end_dates(self, object):
        return [end_date.date for end_date in object.end_dates.all()]

    def prepare_geographic_areas(self, object):
        return [geographic_area.area for geographic_area in object.geographic_areas.all()]
    
    def prepare_subject_topics(self, object):
        return [subject_topic.text for subject_topic in object.subject_topics.all()]
    
    def prepare_subject_persons(self, object):
        return [subject_person.text for subject_person in object.subject_persons.all()]
    
    def prepare_subject_organizations(self, object):
        return [subject_organization.text for subject_organization in object.subject_organizations.all()]
    
    def prepare_extents(self, object):
        return [extent.text for extent in object.extents.all()]
    
    def prepare_genreforms(self, object):
        return [genreform.text for genreform in object.genreforms.all()]
    
    def prepare_inclusive_dates(self, object):
        return [inclusive_date.text for inclusive_date in object.inclusive_dates.all()]


class RepositoryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")
    abbr_name = indexes.CharField(model_attr="abbr_name")
    address = indexes.CharField(model_attr="address")
    description = indexes.CharField(model_attr="description")
    internal_email = indexes.CharField(model_attr="internal_email")
    external_email = indexes.CharField(model_attr="external_email")
    logo = indexes.CharField(model_attr="logo")
    access_link = indexes.CharField(model_attr="access_link")
    home_link = indexes.CharField(model_attr="home_link")
    about_link = indexes.CharField(model_attr="about_link")
    taro_identifier = indexes.CharField(model_attr="taro_identifier")
    date_created = indexes.DateTimeField(model_attr='date_created')
    last_modified = indexes.DateTimeField(model_attr='last_modified')

    def get_model(self):
        return Repository


class CreatorIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr="name")

    def get_model(self):
        return Creator


class AllowListIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    label = indexes.CharField(model_attr="label")
    browse_terms = indexes.MultiValueField(model_attr="browse_terms")

    def get_model(self):
        return AllowList

    def prepare_browse_terms(self, object):
        return [browse_terms.value for browse_terms in object.browse_terms.all()]
