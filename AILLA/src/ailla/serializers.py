from django.apps import apps
from rest_framework import serializers
from datetime import datetime
from .models import *

class DefaultSerializer(serializers.ModelSerializer):
    class Meta:
        model = None
        fields = '__all__'

class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = ['id', 'en','es','pt']

class SolrTextSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    class Meta:
        model = Text
        fields = ['en','es','pt']
    
    def to_representation(self, instance):
        """returns only the field passed via context"""
        field = self._context
        data = super().to_representation(instance)
        return data[field]

class SimpleCountriesSerializer(serializers.ModelSerializer):
    name = TextSerializer()

    class Meta:
        model = Countries
        fields = ['id', 'name', 'country_code', 'flag_code']
        depth=0

class SolrCountriesSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    name = TextSerializer()

    class Meta:
        model = Countries
        fields = ['name', 'country_code', 'flag_code']
        depth = 0

    def to_representation(self, instance):
        """returns only the field passed via context"""
        field = self._context
        data = super().to_representation(instance)

        if field in ['en', 'es', 'pt']:
            data = data['name']

        return data[field]

class CountriesSerializer(serializers.ModelSerializer):
    name = TextSerializer()

    class Meta:
        model = Countries
        fields = '__all__'
        depth = 0
    
    def create(self, validated_data):
        name_data = validated_data.pop('name',None)
        name = None
        if name_data is not None:
            name = Text.objects.create(**name_data)
        country = Countries.objects.create( name=name, **validated_data)
        
        return country
    
    def update(self, instance, validated_data):
        name_data = validated_data.pop('name', None)

        if name_data is not None:
            instance.name.en = name_data.get('en', instance.name.en)
            instance.name.es = name_data.get('es', instance.name.es)
            instance.name.pt = name_data.get('pt', instance.name.pt)
            instance.name.save()

        return super().update(instance, validated_data)

class SimpleLanguagesSerializer(serializers.ModelSerializer):
    name = TextSerializer(read_only=True)

    class Meta:
        model = Languages
        fields = ['id', 'name', 'language_code']

class LanguagesSerializer(serializers.ModelSerializer):
    name = TextSerializer(required=False)
    description = TextSerializer(required=False)
    countries = serializers.PrimaryKeyRelatedField(many=True, queryset=Countries.objects.all())
    countries_detail = SimpleCountriesSerializer(source="countries", read_only=True, many=True)
    language_family = serializers.PrimaryKeyRelatedField(queryset=Languages.objects.all(), required=False, allow_null=True)
    language_family_detail = SimpleLanguagesSerializer(source="language_family", read_only=True)

    class Meta:
        model = Languages
        fields = '__all__'
        depth = 0

    def create(self, validated_data):
        name_data = validated_data.pop('name',None)
        description_data = validated_data.pop('description',None)
        countries_data = validated_data.pop('countries',[])

        name = None
        description = None
        if name_data is not None:
            name = Text.objects.create(**name_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)

        language = Languages.objects.create(name=name, description=description, **validated_data)

        language.countries.set(countries_data)
        
        return language
    
    def update(self, instance, validated_data):
        name_data = validated_data.pop('name', None)
        description_data = validated_data.pop('description', None)
        countries_data = validated_data.pop('countries', [])

        if name_data is not None:
            instance.name.en = name_data.get('en', instance.name.en)
            instance.name.es = name_data.get('es', instance.name.es)
            instance.name.pt = name_data.get('pt', instance.name.pt)
            instance.name.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        # Update countries
        if countries_data is not None:
            instance.countries.clear()
            instance.countries.set(countries_data)

        return super().update(instance, validated_data)

class SolrLanguagesSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    name = TextSerializer(read_only=True)
    language_code = serializers.CharField()

    class Meta:
        model = Languages
        fields = ["name", "language_code"]
    
    def to_representation(self, instance):
        """returns only the field passed via context"""
        field = self._context
        data = super().to_representation(instance)

        if field is not "language_code":
            data = data["name"]

        return data[field]

class SimpleOrganizationsSerializer(serializers.ModelSerializer):
    org_name = TextSerializer()

    class Meta:
        model = Organizations
        fields = ['id', 'org_name']
        depth = 0

class SolrOrganizationsSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    org_name = TextSerializer()

    class Meta:
        model = Organizations
        fields = ["org_name"]
        depth = 0

    def to_representation(self, instance):
        """returns only the field passed via context"""
        field = self._context
        data = super().to_representation(instance)["org_name"]
        return data[field]

class OrganizationsSerializer(serializers.ModelSerializer):
    org_name = TextSerializer()
    description = TextSerializer()
    research_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Languages.objects.all(), allow_null=True)
    research_languages_detail = SimpleLanguagesSerializer(source="research_languages", many=True, read_only=True)

    class Meta:
        model = Organizations
        fields = '__all__'
        depth = 0

    def create(self, validated_data):
        org_name_data = validated_data.pop('org_name',None)
        description_data = validated_data.pop('description',None)
        research_languages_data = validated_data.pop('research_languages',[])
        org_name = None
        description = None
        
        if org_name_data is not None:
            org_name = Text.objects.create(**org_name_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)
        
        organization = Organizations.objects.create(org_name=org_name, description=description, **validated_data)

        organization.research_languages.set(research_languages_data)
        
        return organization
    
    def update(self, instance, validated_data):
        org_name_data = validated_data.pop('org_name', None)
        description_data = validated_data.pop('description', None)
        research_languages_data = validated_data.pop('research_languages', [])

        if org_name_data is not None:
            instance.org_name.en = org_name_data.get('en', instance.org_name.en)
            instance.org_name.es = org_name_data.get('es', instance.org_name.es)
            instance.org_name.pt = org_name_data.get('pt', instance.org_name.pt)
            instance.org_name.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        if research_languages_data is not None:
            instance.research_languages.clear()
            instance.research_languages.set(research_languages_data)

        return super().update(instance, validated_data)

class PersonsSerializer(serializers.ModelSerializer):
    description = TextSerializer()
    native_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Languages.objects.all())
    research_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Languages.objects.all())
    other_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Languages.objects.all())
    organizations = serializers.PrimaryKeyRelatedField(many=True, queryset=Organizations.objects.all())
    research_languages_detail = SimpleLanguagesSerializer(source="research_languages", many=True, read_only=True)
    other_languages_detail = SimpleLanguagesSerializer(source="other_languages", many=True, read_only=True)
    native_languages_detail = SimpleLanguagesSerializer(source="native_languages", many=True, read_only=True)
    organizations_detail = SimpleOrganizationsSerializer(source="organizations", many=True, read_only=True)

    class Meta:
        model = Persons
        fields = '__all__'
        depth = 0
    
    def create(self, validated_data):
        description_data = validated_data.pop('description',None)
        native_languages_data = validated_data.pop('native_languages',[])
        research_languages_data = validated_data.pop('research_languages',[])
        other_languages_data = validated_data.pop('other_languages',[])
        organizations_data = validated_data.pop('organizations',[])

        description = None
        if description_data is not None:
            description = Text.objects.create(**description_data)
        person = Persons.objects.create( description=description, **validated_data)

        person.native_languages.set(native_languages_data)
        person.research_languages.set(research_languages_data)
        person.other_languages.set(other_languages_data)
        person.organizations.set(organizations_data)
        
        return person
    
    def update(self, instance, validated_data):
        description_data = validated_data.pop('description', None)
        native_languages_data = validated_data.pop('native_languages', [])
        research_languages_data = validated_data.pop('research_languages', [])
        other_languages_data = validated_data.pop('other_languages', [])
        organizations_data = validated_data.pop('organizations', [])

        if description_data is not None:
            if instance.description is not None:
                for attr, value in description_data.items():
                    setattr(instance.description, attr, value)
                instance.description.save()
            else:
                instance.description = Text.objects.create(**description_data)

        instance.native_languages.set(native_languages_data)
        instance.research_languages.set(research_languages_data)
        instance.other_languages.set(other_languages_data)
        instance.organizations.set(organizations_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

class SimplePersonsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persons
        fields = ['id', 'given_name','surname']
        depth = 0

class SolrPersonsSerializer(serializers.ModelSerializer):
    """returns first and last name as one string, used for solr"""
    class Meta:
        model = Persons
        fields = ['given_name','surname']
        depth = 0
    
    def to_representation(self, instance):
        """combines name and surname, returns string"""
        json_data = super().to_representation(instance)
        return f"{json_data.pop('given_name')} {json_data.pop('surname')}"

class ContributorRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributorRole
        fields = '__all__'
        depth = 0

class SimpleGenreSerializer(serializers.ModelSerializer):
    name = TextSerializer()

    class Meta:
        model = Genre
        fields = ['id','name']
        depth = 0


class GenreSerializer(serializers.ModelSerializer):
    name = TextSerializer()
    description = TextSerializer()

    class Meta:
        model = Genre
        fields = '__all__'
        depth = 0

    def create(self, validated_data):
        name_data = validated_data.pop('name',None)
        description_data = validated_data.pop('description',None)
        name = None
        description = None
        if name_data is not None:
            name = Text.objects.create(**name_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)
        genre = Genre.objects.create(name=name, description=description, **validated_data)
        return genre
    
    def update(self, instance, validated_data):
        name_data = validated_data.pop('name', None)
        description_data = validated_data.pop('description', None)

        if name_data is not None:
            instance.name.en = name_data.get('en', instance.name.en)
            instance.name.es = name_data.get('es', instance.name.es)
            instance.name.pt = name_data.get('pt', instance.name.pt)
            instance.name.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        return super().update(instance, validated_data)
    
class SolrGenreSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    name = TextSerializer()

    class Meta:
        model = Genre
        fields = ["name"]
        depth = 0

    def to_representation(self, instance):
        """returns only the field passed via context"""
        field = self._context
        data = super().to_representation(instance)["name"]
        return data[field]
    
class MediaContentTypeSerializer(serializers.ModelSerializer):
    name = TextSerializer()
    description = TextSerializer()

    class Meta:
        model = MediaContentType
        fields = '__all__'
        depth = 0

    def create(self, validated_data):
        name_data = validated_data.pop('name',None)
        description_data = validated_data.pop('description',None)
        name = None
        description = None
        if name_data is not None:
            name = Text.objects.create(**name_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)
        mediaContentType = MediaContentType.objects.create(name=name, description=description, **validated_data)
        return mediaContentType

    def update(self, instance, validated_data):
        name_data = validated_data.pop('name', None)
        description_data = validated_data.pop('description', None)

        if name_data is not None:
            instance.name.en = name_data.get('en', instance.name.en)
            instance.name.es = name_data.get('es', instance.name.es)
            instance.name.pt = name_data.get('pt', instance.name.pt)
            instance.name.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        return super().update(instance, validated_data)
    
class MediaContentTypeNameSerializer(serializers.ModelSerializer):
    name = TextSerializer()

    class Meta:
        model = MediaContentType
        fields = ['id', 'name']
        depth = 0

class SolrMediaContentTypeSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    name = TextSerializer()

    class Meta:
        model = MediaContentType
        fields = ["name"]
        depth = 0
    
    def to_representation(self, instance):
        """returns only the field passed via context, and only the name"""
        data = super().to_representation(instance)["name"]
        field = self._context
        return data[field]

class ParticipantRolesSerializer(serializers.ModelSerializer):
    name = TextSerializer()
    description = TextSerializer()

    class Meta:
        model = ParticipantRoles
        fields = '__all__'
        depth = 0

    def create(self, validated_data):
        name_data = validated_data.pop('name',None)
        description_data = validated_data.pop('description',None)
        name = None
        description = None
        if name_data is not None:
            name = Text.objects.create(**name_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)
        participantRole = ParticipantRoles.objects.create(name=name, description=description, **validated_data)
        return participantRole

    def update(self, instance, validated_data):
        name_data = validated_data.pop('name', None)
        description_data = validated_data.pop('description', None)

        if name_data is not None:
            instance.name.en = name_data.get('en', instance.name.en)
            instance.name.es = name_data.get('es', instance.name.es)
            instance.name.pt = name_data.get('pt', instance.name.pt)
            instance.name.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        return super().update(instance, validated_data)
    
class ParticipantRolesNameSerializer(serializers.ModelSerializer):
    name = TextSerializer()

    class Meta:
        model = ParticipantRoles
        fields = ['name']
        depth = 0

class OriginalMediaTypeSerializer(serializers.ModelSerializer):
    name = TextSerializer()
    description = TextSerializer()

    class Meta:
        model = OriginalMediaType
        fields = '__all__'
        depth = 0

    def create(self, validated_data):
        name_data = validated_data.pop('name')
        description_data = validated_data.pop('description')
        name = None
        description = None
        if name_data is not None:
            name = Text.objects.create(**name_data)
        if description_data is not None:
            description = Text.objects.create(**description_data)
        originalMediaType = OriginalMediaType.objects.create(name=name, description=description, **validated_data)
        return originalMediaType

    def update(self, instance, validated_data):
        name_data = validated_data.pop('name', None)
        description_data = validated_data.pop('description', None)

        if name_data is not None:
            instance.name.en = name_data.get('en', instance.name.en)
            instance.name.es = name_data.get('es', instance.name.es)
            instance.name.pt = name_data.get('pt', instance.name.pt)
            instance.name.save()

        if description_data is not None:
            instance.description.en = description_data.get('en', instance.description.en)
            instance.description.es = description_data.get('es', instance.description.es)
            instance.description.pt = description_data.get('pt', instance.description.pt)
            instance.description.save()

        return super().update(instance, validated_data)
    
class OriginalMediaTypeNameSerializer(serializers.ModelSerializer):
    name = TextSerializer()

    class Meta:
        model = OriginalMediaType
        fields = ['id', 'name']
        depth = 0

class SolrOriginalMediaTypeSerializer(serializers.ModelSerializer):
    """returns one string value, determined by context, used for solr"""
    name = TextSerializer()

    class Meta:
        model = OriginalMediaType
        fields = ["name"]
        depth = 0
    
    def to_representation(self, instance):
        """returns only the field passed via context, and only the name"""
        data = super().to_representation(instance)["name"]
        field = self._context
        return data[field]


class SimpleRightsSerializer(serializers.ModelSerializer):
    title = TextSerializer()
    uri = TextSerializer()
    
    class Meta:
        model = Rights
        fields = '__all__'
        depth = 0

class EmailSerializer(serializers.Serializer):
    to_email = serializers.EmailField()
    user_data = serializers.DictField()
    subject = serializers.CharField()
    message = serializers.CharField()
    object_url = serializers.URLField()

class EmailOwnersSerializer(serializers.Serializer):
    owner_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of user IDs who are the owners."
    )
    object_id = serializers.IntegerField(
        required=True,
        help_text="ID of the object being requested."
    )
    object_url = serializers.URLField(
        required=True,
        help_text="URL to the object."
    )
    object_type = serializers.CharField(
        required=True,
        help_text="Type of the object (e.g. 'Document', 'Image')."
    )
    object_title = serializers.CharField(
        required=True,
        help_text="Title of the object."
    )
    subject = serializers.CharField(
        required=True,
        help_text="Subject of the email."
    )
    body = serializers.CharField(
        required=True,
        style={'base_template': 'textarea.html'},
        help_text="Main content of the email."
    )

class RegisterSuccessEmailSerializer(serializers.Serializer):
    account_email = serializers.EmailField(
        required=True,
        help_text="Email address of account."
    )
    url = serializers.URLField(
        required=True,
        help_text="URL to the object."
    )

class SolrRightsSerializer(serializers.ModelSerializer):
    """returns one string value (all lang + uri smashed together), used for solr"""
    title = TextSerializer()
    uri = TextSerializer()
    
    class Meta:
        model = Rights
        fields = '__all__'
        depth = 0

    def to_representation(self, instance):
        """returns uri information smashed together in multiple languages"""
        data = super().to_representation(instance)

        result = ""
        for key in data["title"].keys():
            if key is not "id":
                result += data["title"][key]
                result += " "
        for key in data["uri"].keys():
            if key is not "id":
                result += data["uri"][key]
                result += " "

        return result

class SolrDateSerializer(serializers.DateField):
    """convert dates to ISO-8601 format (for solr 'pdate' field)"""
    def to_representation(self, value):
        date_created = super().to_representation(value)
        if date_created:
            date_created = f"{date_created}T00:00:00Z"
        return date_created
    
class SolrDatestringSerializer(serializers.DateField):
    """convert dates to ISO-8601 format (for solr 'pdate' field)"""
    def to_representation(self, value):
        # date_created = super().to_representation(value)
        date_created = str(value)

        # Pad the date string with zeros if needed
        date_created = date_created.rjust(8, '0')

        # Check if the date_created is in the format YYYYMMDD
        if len(date_created) == 8 and date_created.isdigit():
            year = int(date_created[0:4])
            month = int(date_created[4:6])
            day = int(date_created[6:8])

            # Check if the date components are valid
            if 1 <= month <= 12 and 1 <= day <= 31:
                # Format the date as ISO-8601 with 'T00:00:00Z'
                date_created = f"{year:04d}-{month:02d}-{day:02d}T00:00:00Z"
            else:
                # Use placeholders '01' for month and day if the date is incomplete
                date_created = f"{date_created[0:4]}-01-01T00:00:00Z"
        else:
            raise ValueError("Invalid date format")
        return date_created
