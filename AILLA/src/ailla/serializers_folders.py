import requests
import re
from django.apps import apps
from rest_framework import serializers
from .models import *
from .serializers import *
from .solr import solr
from core.logger import logger
from django.db import transaction

class SimpleFoldersSerializer(serializers.ModelSerializer):
    title = TextSerializer(required=False)
    description = TextSerializer(required=False)

    class Meta:
        model = Folders

        # Subset of fields that should be shown
        fields = [
            'id',
            'title',
            'description',
        ]
        read_only_fields = fields
        depth = 0

class FoldersSerializer(serializers.ModelSerializer):
    title = TextSerializer(required=False)
    description = TextSerializer(required=False)

    indigenous_title_language = SimpleLanguagesSerializer(source="lang_indigenous_title", required=False, read_only=True)
    indigenous_description_language = SimpleLanguagesSerializer(source="lang_indigenous_description", required=False, read_only=True)

    lang_indigenous_title = serializers.PrimaryKeyRelatedField(write_only=True, allow_null=True, queryset=Languages.objects.all())
    lang_indigenous_description = serializers.PrimaryKeyRelatedField(write_only=True, allow_null=True, queryset=Languages.objects.all())

    parent_collection = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Collections.objects.all())
    
    subject_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Languages.objects.all())
    subject_languages_detail = SimpleLanguagesSerializer(source="subject_languages", required=False, many=True, read_only=True)
    countries = serializers.PrimaryKeyRelatedField(many=True, queryset=Countries.objects.all())
    countries_detail = SimpleCountriesSerializer(source="countries", required=False, many=True, read_only=True)

    folder_languages = serializers.SerializerMethodField('get_languages')
    folder_countries = serializers.SerializerMethodField('get_countries')
    collection_folder_id = serializers.SerializerMethodField('get_collection')

    class Meta:
        model = Folders
        # Add all your fields here, just like in your model
        fields = [
            'id',
            'legacy_id',
            'islandora_pid',
            'title',
            'parent_collection',
            'indigenous_title',
            'indigenous_title_language',
            'lang_indigenous_title',
            'subject_languages',
            'subject_languages_detail',
            'countries',
            'countries_detail',
            'description',
            'indigenous_description',
            'indigenous_description_language',
            'lang_indigenous_description',
            'language_community',
            'last_updated',
            'user_last_updated',
            'folder_languages',
            'folder_countries',
            'collection_folder_id',
            'draft',
            'sip',
        ]
        read_only_fields = ['last_updated','folder_countries','folder_languages', 'items', 'collection_folder_id', 'subject_languages_detail', 'countries_detail']
        depth = 0

    def create(self, validated_data):
        # Get the data and create Text objects

        title_data = validated_data.pop('title', None)
        description_data = validated_data.pop('description', None)

        subject_languages_data = validated_data.pop('subject_languages', [])
        countries_data = validated_data.pop('countries', [])

        title = None
        description = None
        if title_data is not None:
            title = Text.objects.create(**title_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)
        
        # Prepare your Folder data but do not save it yet
        folder = Folders(title=title, description=description, **validated_data)

        # Add the folder to Fedora before saving it in your database
        fcrepo6_api = RestAdapter()

        # Get the endpoint to make a new container
        ENVIRONMENT_PREFIX = os.environ.get("ENVIRONMENT_PREFIX")
        fedora_endpoint = f"{folder.parent_collection.fedora_uuid}/"

        # Make a new container in Fedora that will represent this new folder
        try:
            pattern = r'^(\w+)/(\w+)/([a-fA-F0-9\-]{36})/$'
            match = re.match(pattern, fedora_endpoint)
            if match:
                response: requests.models.Response = fcrepo6_api.make_or_update_container(
                    endpoint=fedora_endpoint, container_type=Container.BASIC
                )
            else:
                raise Exception(f"Invalid fedora_endpoint format: {fedora_endpoint}")
        except Exception as e:
            logger.error(f"Error making Folder's container in Fedora: {e}")
            raise

        # Parse the response of the container creation to find the UUID Fedora created for it
        folder.fedora_uuid = response.content.decode().split("fcrepo/rest/")[-1]

        # Add dc_terms to Fedora
        try:
            new_dc_terms = []
            new_dc_terms.append(("title", folder.title.en))
            rdf_graph = fcrepo6_api.get_rdf_graph(folder.fedora_uuid)
            rdf_graph = rdf.set_dc_terms(rdf_graph, new_dc_terms)
            fcrepo6_api.set_rdf_graph(folder.fedora_uuid, rdf_graph)
        except Exception as e:
            logger.warn("Error adding Folder's DC Terms in Fedora, aborting")

        # Now that Fedora steps are completed successfully, save the Folder in your database
        folder.save()

        # Add ManyToMany relationships
        folder.subject_languages.set(subject_languages_data)
        folder.countries.set(countries_data)

        # Add to Solr metadata if not a draft
        if validated_data['draft'] is False:
            solr_data = FoldersSolrSerializer(folder).data
            solr.add(solr_data)

        return folder


    def update(self, instance, validated_data):
        title_data = validated_data.pop('title', None)
        description_data = validated_data.pop('description', None)
        
        subject_languages_data = validated_data.pop('subject_languages', [])
        countries_data = validated_data.pop('countries', [])

        if title_data is not None:
            instance.title.en = title_data.get('en', instance.title.en)
            instance.title.es = title_data.get('es', instance.title.es)
            instance.title.pt = title_data.get('pt', instance.title.pt)
            instance.title.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        instance.subject_languages.set(subject_languages_data)
        instance.countries.set(countries_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        #UPDATE FEDORA ------
        
        fedora_endpoint = instance.fedora_uuid
        
        new_dc_terms = []
        new_dc_terms.append(("title", instance.title.en))

        try:
            fedora_api = RestAdapter()
            rdf_graph = fedora_api.get_rdf_graph(fedora_endpoint)
            rdf_graph = rdf.set_dc_terms(rdf_graph, new_dc_terms)
            fedora_api.set_rdf_graph(fedora_endpoint, rdf_graph)
        except Exception as e:
            logger.warn(f"Error adding Folder metadata to Fedora: {e}")

        # Update Solr metadata if not a draft
        if instance.draft is False:
            solr_data = FoldersSolrSerializer(instance).data
            solr.add(solr_data)

        return super().update(instance, validated_data)
    
    # def destroy(self, instance):
    #     folder_id = instance.id
    #     with transaction.atomic(): 
    #         folder = Folders.objects.get(id=folder_id)

    #         # Delete all text objects referenced in folder
    #         ## Foreign-key text object fields are: name, description
    #         folder_title_id = folder.title.id
    #         folder_description_id = folder.description.id
            
    #         # Delete items and files
    #         items = Items.objects.filter(parent_folder=folder_id)
    #         if items:
    #             for item in items:
    #                 items_serializer = ItemsSerializer(item)
    #                 items_serializer.destroy(item)

    #         # Delete folder
    #         folder.delete()

    #         # Delete folder title text object
    #         folder_title_text = Text.objects.get(id=folder_title_id)
    #         folder_title_text.delete()

    #         # Delete folder description text object
    #         folder_description_text = Text.objects.get(id=folder_description_id)
    #         folder_description_text.delete()
            
    #         # Delete Fedora terms
    #         fedora_endpoint = instance.fedora_uuid
    #         fedora_id = instance.fedora_uuid

    #         fedora_api = RestAdapter()
    #         delete_response = fedora_api.delete(fedora_endpoint)

    #         return delete_response
  
    def get_countries(self,obj):
        countries = []
        for country in obj.countries.all():
            countries.append({"id": country.id,"code": country.country_code, "en":country.name.en, "es":country.name.es, "pt":country.name.pt, "flag_code":country.flag_code})
        return countries
    
    def get_languages(self,obj):
        languages = []
        for language in obj.subject_languages.all():
            languages.append({"id": language.id, "en":language.name.en, "es":language.name.es, "pt": language.name.pt, "code":language.language_code })
        return languages

    def get_collection(self, obj):
        return {'id':obj.parent_collection.id, 'en':obj.parent_collection.title.en, 'es':obj.parent_collection.title.es, 'pt':obj.parent_collection.title.pt}
    
class FoldersSolrSerializer(serializers.ModelSerializer):
    """Outputs a folder in a flattened json format that is ready to be sent to Solr"""

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

    countries_en = SolrCountriesSerializer(source="countries", many=True, context="en")
    countries_es = SolrCountriesSerializer(source="countries", many=True, context="es")
    countries_pt = SolrCountriesSerializer(source="countries", many=True, context="pt")
    countries_codes = SolrCountriesSerializer(source="countries", many=True, context="country_code")

    languages_en = SolrLanguagesSerializer(source="subject_languages", many=True, context="en")
    languages_es = SolrLanguagesSerializer(source="subject_languages", many=True, context="es")
    languages_pt = SolrLanguagesSerializer(source="subject_languages", many=True, context="pt")
    languages_codes = SolrLanguagesSerializer(source="subject_languages", many=True, context="language_code")

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

    def to_representation(self, obj:Folders):
        """Adds some additional metadata not held in model"""
        solr_data = super().to_representation(obj)
        solr_data["last_updated"] = convert_to_utc(solr_data["last_updated"]) if solr_data.get("last_updated") else None
        solr_data["model"] = Folders.__name__
        solr_data["id"] = obj.get_solr_id()
        return solr_data
