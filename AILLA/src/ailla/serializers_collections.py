import requests
from django.apps import apps
from rest_framework import serializers
from .models import *
from .serializers import *
from .serializers_folders import FoldersSerializer
from .solr import solr

class SimpleCollectionsSerializer(serializers.ModelSerializer):
    title = TextSerializer(required=False)
    description = TextSerializer(required=False)
    class Meta:
        model = Collections
        fields = ('id', 'title', 'description')

class FastCollectionsSerializer(serializers.ModelSerializer):
    title = TextSerializer(required=False)
    description = TextSerializer(required=False)
    collection_languages = LanguagesSerializer(many=True, required=False)
    countries = CountriesSerializer(many=True, required=False)
    contributors = serializers.SerializerMethodField('get_contributors')

    class Meta:
        model = Collections
        fields = [
            "id",
            "title",
            "collection_languages",
            "countries",
            "description",
            "user_last_updated",
            "last_updated",
            "contributors"
        ]
        read_only_fields = fields
        depth = 2

    def get_contributors(self, obj):
        collectors = []
        for person in obj.collectors_persons.all():
            collectors.append({"type": "collector", "model": "persons", "id": person.id, "given_name": person.given_name, "surname":person.surname})
        for organization in obj.collectors_orgs.all():
            collectors.append({"type": "collector", "model": "organizations", "id":organization.id, "en":organization.org_name.en, "es":organization.org_name.es, "pt":organization.org_name.pt})
        for person in obj.depositors_persons.all():
            collectors.append({"type": "depositor", "model": "persons", "id": person.id, "given_name": person.given_name, "surname":person.surname})
        for organization in obj.depositors_orgs.all():
            collectors.append({"type": "depositor", "model": "organizations", "id":organization.id, "en":organization.org_name.en, "es":organization.org_name.es, "pt":organization.org_name.pt})
        return collectors

class CollectionsSerializer(serializers.ModelSerializer):
    title = TextSerializer(required=False)
    description = TextSerializer(required=False)
    indigenous_title_language = SimpleLanguagesSerializer(source="lang_indigenous_title", read_only=True)
    indigenous_description_language = SimpleLanguagesSerializer(source="lang_indigenous_description", read_only=True)

    #Using these to grab populate the forms
    collectors_persons_detail = SimplePersonsSerializer(source="collectors_persons", many=True, read_only=True)
    collectors_orgs_detail = SimpleOrganizationsSerializer(source="collectors_orgs", many=True, read_only=True)
    depositors_persons_detail = SimplePersonsSerializer(source="depositors_persons", many=True, read_only=True)
    depositors_orgs_detail = SimpleOrganizationsSerializer(source="depositors_orgs", many=True, read_only=True)
    collection_languages_detail = SimpleLanguagesSerializer(source="collection_languages", many=True, read_only=True)
    countries_detail = SimpleCountriesSerializer(source="countries", many=True, read_only=True)

    #using these to write on submit
    lang_indigenous_title = serializers.PrimaryKeyRelatedField(write_only=True, allow_null=True, required=False, queryset=Languages.objects.all())
    lang_indigenous_description = serializers.PrimaryKeyRelatedField(write_only=True, allow_null=True, required=False, queryset=Languages.objects.all())
    collectors_persons = serializers.PrimaryKeyRelatedField(many=True, queryset=Persons.objects.all())
    collectors_orgs = serializers.PrimaryKeyRelatedField(many=True, queryset=Organizations.objects.all())
    depositors_persons = serializers.PrimaryKeyRelatedField(many=True, queryset=Persons.objects.all())
    depositors_orgs = serializers.PrimaryKeyRelatedField(many=True, queryset=Organizations.objects.all())
    collection_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Languages.objects.all())
    countries = serializers.PrimaryKeyRelatedField(many=True, queryset=Countries.objects.all())

    contributors = serializers.SerializerMethodField()
    collection_countries = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()

    class Meta:
        model = Collections
        fields = [
            "id",
            "islandora_pid",
            "legacy_id",
            "title",
            "indigenous_title",
            "lang_indigenous_title",
            "website",
            "collectors_persons",
            "collectors_persons_detail",
            "collectors_orgs",
            "collectors_orgs_detail",
            "depositors_persons",
            "depositors_persons_detail",
            "depositors_orgs",
            "depositors_orgs_detail",
            "collection_languages",
            "collection_languages_detail",
            "countries",
            "countries_detail",
            "description",
            "indigenous_description",
            "lang_indigenous_description",
            "user_last_updated",
            "last_updated",
            "contributors",
            "collection_countries",
            "languages",
            "indigenous_title_language",
            "indigenous_description_language",
            "draft"
        ]
        read_only_fields = [ "last_updated", "contributors", "collection_countries", "languages"]
        depth = 0

    def create(self, validated_data):
        #GET DATA --------------------------
        title_data = validated_data.pop('title', None)
        description_data = validated_data.pop('description', None)
        collectors_persons_data = validated_data.pop('collectors_persons', [])
        collectors_orgs_data = validated_data.pop('collectors_orgs', [])
        depositors_persons_data = validated_data.pop('depositors_persons', [])
        depositors_orgs_data = validated_data.pop('depositors_orgs', [])
        collection_languages_data = validated_data.pop('collection_languages', [])
        countries_data = validated_data.pop('countries', [])
        
        #CREATE TEXT OBJECTS ------------
        title = None
        description = None
        if title_data is not None:
            title = Text.objects.create(**title_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)

        collection = Collections(title=title, description=description, **validated_data)

        # add ManyToMany relationships
        collection.collectors_persons.set(collectors_persons_data)
        collection.collectors_orgs.set(collectors_orgs_data)
        collection.depositors_persons.set(depositors_persons_data)
        collection.depositors_orgs.set(depositors_orgs_data)
        collection.collection_languages.set(collection_languages_data)
        collection.countries.set(countries_data)

        return collection

class CollectionsSolrSerializer(serializers.ModelSerializer):
    """Outputs a collection in a flattened json format that is ready to be sent to Solr"""
    title_en = SolrTextSerializer(source="title", context="en")
    title_es = SolrTextSerializer(source="title", context="es")
    title_pt = SolrTextSerializer(source="title", context="pt")
    title_indig = serializers.CharField(source="indigenous_title")
    title_indig_language_en = SolrLanguagesSerializer(source="lang_indigenous_title", context="en")
    title_indig_language_es = SolrLanguagesSerializer(source="lang_indigenous_title", context="es")
    title_indig_language_pt = SolrLanguagesSerializer(source="lang_indigenous_title", context="pt")
    title_indig_language_code = SolrLanguagesSerializer(source="lang_indigenous_title", context="language_code")

    description_en = SolrTextSerializer(source="description", context="en")
    description_es = SolrTextSerializer(source="description", context="es")
    description_pt = SolrTextSerializer(source="description", context="pt")
    description_indig = serializers.CharField(source="indigenous_description")
    description_indig_language_en = SolrLanguagesSerializer(source="lang_indigenous_description", context="en")
    description_indig_language_es = SolrLanguagesSerializer(source="lang_indigenous_description", context="es")
    description_indig_language_pt = SolrLanguagesSerializer(source="lang_indigenous_description", context="pt")
    description_indig_language_code = SolrLanguagesSerializer(source="lang_indigenous_description", context="language_code")

    collectors_persons = SolrPersonsSerializer(many=True, read_only=True)
    collectors_orgs_en = SolrOrganizationsSerializer(source="collectors_orgs", many=True, context="en")
    collectors_orgs_es = SolrOrganizationsSerializer(source="collectors_orgs", many=True, context="es")
    collectors_orgs_pt = SolrOrganizationsSerializer(source="collectors_orgs", many=True, context="pt")

    depositors_persons = SolrPersonsSerializer(many=True, read_only=True)
    depositors_orgs_en = SolrOrganizationsSerializer(source="depositors_orgs", many=True, context="en")
    depositors_orgs_es = SolrOrganizationsSerializer(source="depositors_orgs", many=True, context="es")
    depositors_orgs_pt = SolrOrganizationsSerializer(source="depositors_orgs", many=True, context="pt")

    countries_en = SolrCountriesSerializer(source="countries", many=True, context="en")
    countries_es = SolrCountriesSerializer(source="countries", many=True, context="es")
    countries_pt = SolrCountriesSerializer(source="countries", many=True, context="pt")
    countries_codes = SolrCountriesSerializer(source="countries", many=True, context="country_code")

    languages_en = SolrLanguagesSerializer(source="collection_languages", many=True, context="en")
    languages_es = SolrLanguagesSerializer(source="collection_languages", many=True, context="es")
    languages_pt = SolrLanguagesSerializer(source="collection_languages", many=True, context="pt")
    languages_codes = SolrLanguagesSerializer(source="collection_languages", many=True, context="language_code")

    class Meta:
        model = Collections
        fields = [
            "pk",
            "islandora_pid",
            "legacy_id",

            "title_en",
            "title_es",
            "title_pt",
            "title_indig",
            "title_indig_language_en",
            "title_indig_language_es",
            "title_indig_language_pt",
            "title_indig_language_code",

            "description_en",
            "description_es",
            "description_pt",
            "description_indig",
            "description_indig_language_en",
            "description_indig_language_es",
            "description_indig_language_pt",
            "description_indig_language_code",

            "collectors_persons",
            "collectors_orgs_en",
            "collectors_orgs_es",
            "collectors_orgs_pt",

            "depositors_persons",
            "depositors_orgs_en",
            "depositors_orgs_es",
            "depositors_orgs_pt",

            "countries_en",
            "countries_es",
            "countries_pt",
            "countries_codes",

            "languages_en",
            "languages_es",
            "languages_pt",
            "languages_codes",

            "last_updated",
        ] 
        depth = 0

    def to_representation(self, obj:Collections):
        """Adds some additional metadata not held in model"""
        solr_data = super().to_representation(obj)
        solr_data["last_updated"] = convert_to_utc(solr_data["last_updated"]) if solr_data.get("last_updated") else None
        solr_data["model"] = Collections.__name__
        solr_data["id"] = obj.get_solr_id()
        return solr_data
