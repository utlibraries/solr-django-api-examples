import json
import os
from django.forms import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.logger import logger
from .solr import solr
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from unidecode import unidecode

# Text model to store translations
class Text(models.Model):
    en = models.TextField(blank=True)
    es = models.TextField(blank=True)
    pt = models.TextField(blank=True)

    # Add diacritic-neutral fields
    en_neutral = models.CharField(max_length=300, blank=True, null=True)
    es_neutral = models.CharField(max_length=300, blank=True, null=True)
    pt_neutral = models.CharField(max_length=300, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Populate the diacritic-neutral fields before saving
        en_undiacritic = unidecode(self.en)
        es_undiacritic = unidecode(self.es)
        pt_undiacritic = unidecode(self.pt)
        # Save only if original field is < 300 characters
        self.en_neutral = en_undiacritic if len(en_undiacritic) <= 300 else None
        self.es_neutral = es_undiacritic if len(es_undiacritic) <= 300 else None
        self.pt_neutral = pt_undiacritic if len(pt_undiacritic) <= 300 else None

        super(Text, self).save(*args, **kwargs)

# Controlled Vocabularies
class Genre(models.Model):
    name = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="genre_name")
    description = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="genre_description")

class ParticipantRoles(models.Model):
    name = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="roles_name")
    description = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="roles_description")

class MediaContentType(models.Model):
    name = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="content_name")
    description = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="content_description")

class OriginalMediaType(models.Model):
    name = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="og_media_name")
    description = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="og_media_description")

# Authority Terms
class Countries(models.Model):
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    name = models.ForeignKey(Text, on_delete=models.CASCADE)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    viaf = models.URLField(blank=True, null=True)
    flag_code = models.CharField(max_length=3, null=True, blank=True)
    # Technical MD
    last_updated = models.DateTimeField(auto_now=True, null=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class Languages(models.Model):
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    name = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, blank=True, related_name="lang_name")
    indigenous_name = models.CharField(max_length=300, null=True, blank=True)
    alternative_name = models.CharField(max_length=300, null=True, blank=True)
    language_code = models.CharField(max_length=5, null=True, blank=True)
    macro_language = models.BooleanField()
    language_family = models.ForeignKey("self", blank=True, null=True, on_delete=models.CASCADE)
    description = models.ForeignKey(Text, null=True, on_delete=models.CASCADE, related_name="lang_description")
    countries = models.ManyToManyField(Countries, blank=True)
    # Technical MD
    last_updated = models.DateTimeField(auto_now=True, null=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class Organizations(models.Model):
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    org_name = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="org_name")
    acronym = models.CharField(max_length=20, null=True, blank=True)
    director_names = models.JSONField(default=dict, blank=True)
    funder = models.CharField(max_length=300, null=True, blank=True)
    parent_institution = models.CharField(max_length=300, null=True, blank=True)
    description = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="org_description")
    depositor_status = models.BooleanField()
    research_languages = models.ManyToManyField(Languages)
    # Technical MD
    last_updated = models.DateTimeField(auto_now=True, null=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class Persons(models.Model):
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    given_name = models.CharField(max_length=60, null=True, blank=True)
    surname = models.CharField(max_length=60, null=True, blank=True)
    # Choices should be M, F, Unknown
    birth_year = models.IntegerField(null=True, blank=True)
    alternative_names = models.JSONField(default=dict, blank=True, null=True)
    place_of_origin = models.CharField(max_length=300, null=True, blank=True)
    description = models.ForeignKey(Text, on_delete=models.CASCADE, blank=True, null=True)
    depositor_status = models.BooleanField()
    native_languages = models.ManyToManyField(Languages, related_name="native_languages", blank=True)
    research_languages = models.ManyToManyField(Languages, related_name="research_languages")
    other_languages = models.ManyToManyField(Languages, related_name="other_languages")
    organizations = models.ManyToManyField(Organizations)
    # Technical MD
    last_updated = models.DateTimeField(auto_now=True, null=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

class Rights(models.Model):
    title = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="title")
    uri = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="uri")

# Collections are top level groupings of folders and files
class Collections(models.Model):
    # ex. ailla:12345
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    # ex. CTP001R003
    legacy_id = models.CharField(max_length=20, null=True, blank=True)
    title = models.ForeignKey(Text, on_delete=models.CASCADE, null=True, related_name="collection_title")
    indigenous_title = models.TextField(null=True, blank=True)
    lang_indigenous_title = models.ForeignKey(Languages, on_delete=models.CASCADE, null=True, blank=True, related_name="lang_indigenous_title")
    website = models.URLField(null=True, blank=True)
    collectors_persons = models.ManyToManyField(Persons, blank=True, related_name="collectors_persons")
    collectors_orgs = models.ManyToManyField(Organizations, blank=True, related_name="collectors_orgs")
    depositors_persons = models.ManyToManyField(Persons, blank=True, related_name="depositors_persons")
    depositors_orgs = models.ManyToManyField(Organizations, blank=True,  related_name="depositors_orgs")
    collection_languages = models.ManyToManyField(Languages, blank=True, related_name="collection_languages")
    countries = models.ManyToManyField(Countries, blank=True,)
    description = models.ForeignKey(Text, on_delete=models.CASCADE, null=True)
    indigenous_description = models.TextField(null=True, blank= True)
    lang_indigenous_description = models.ForeignKey(Languages, on_delete=models.CASCADE, null=True, blank=True, related_name="collection_lang_indigenous_description")
    # Technical MD
    fedora_uuid = models.CharField(max_length=300)
    last_updated = models.DateTimeField(auto_now_add=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    draft = models.BooleanField(default=True)

    def get_class_name():
        # return the name of the class as a pretty string
        return "Collections"

    def get_solr_id(self):
        """unique id used in solr add or delete requests"""
        return f"{self.pk}:Collections"
    
    def delete(self):
        solr.delete(id=self.get_solr_id())
        super(Collections, self).delete()

# Folders are groups of items and files meant to organize the collection
class Folders(models.Model):
    # ex. ailla:12345
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    # ex. CTP001R003
    legacy_id = models.CharField(max_length=20, null=True, blank=True)
    title = models.ForeignKey(Text, blank=True, null=True, on_delete=models.CASCADE, related_name="folder_title")
    parent_collection = models.ForeignKey(Collections, on_delete=models.CASCADE, related_name="folders")
    indigenous_title = models.TextField(blank=True)
    lang_indigenous_title = models.ForeignKey(Languages,blank=True, null=True, on_delete=models.CASCADE)
    subject_languages = models.ManyToManyField(Languages,blank=True, related_name="subject_languages")
    countries = models.ManyToManyField(Countries, blank=True)
    description = models.ForeignKey(Text,blank=True, null=True, on_delete=models.CASCADE)
    indigenous_description = models.TextField(blank=True)
    lang_indigenous_description = models.ForeignKey(Languages, blank=True, null=True, on_delete=models.CASCADE, related_name="folder_lang_indigenous_description")
    language_community = models.TextField(blank=True)
    # Technical MD
    fedora_uuid = models.CharField(max_length=300)
    last_updated = models.DateTimeField(auto_now_add=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    draft = models.BooleanField(default=True)
    sip = models.CharField(max_length=300, null=True, blank=True)

    def get_solr_id(self):
        """unique id used in solr add or delete requests"""
        return f"{self.pk}:Folders"

    def delete(self):
        solr.delete(id=self.get_solr_id())
        super(Folders, self).delete()

def get_current_date():
    return timezone.now().date()
    
# Items (or Sets) can have one or more files associated with them, which will all be
# displayed on the same viewer
class Items(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = "PUB", _("Public")
        LOGIN = "LOG", _("Login")
        RESTRICTED = "RST", _("Restricted")
        DRAFT = "DRA", _("Draft")
        EMBARGOED = "EMB", _("Embargoed")

    # ex. ailla:12345
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    # ex. CTP001R003
    legacy_id = models.CharField(max_length=20, null=True, blank=True)
    name = models.ForeignKey(Text, on_delete=models.CASCADE, related_name="item_name")
    parent_folder = models.ForeignKey(Folders, on_delete=models.CASCADE, related_name="items")
    description = models.ForeignKey(Text, on_delete=models.CASCADE)
    indigenous_name = models.CharField(max_length=1000, null=True, blank=True)
    lang_indigenous_name = models.ForeignKey(Languages,blank=True, null=True, on_delete=models.CASCADE)
    indigenous_description = models.TextField(null=True, blank=True)
    lang_indigenous_description = models.ForeignKey(Languages,blank=True, null=True, on_delete=models.CASCADE, related_name="item_lang_indigenous_desc")
    # Technical MD
    last_updated = models.DateTimeField(auto_now=True, null=True)
    user_last_updated = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    fedora_uuid = models.CharField(max_length=300)
    visibility = models.CharField(choices = Visibility.choices, default=Visibility.DRAFT, max_length=3)
    # Example use: datetime.date(1997, 10, 19)
    embargo_date = models.DateField(null=True, blank = True, default=None)
    # Semantic creation date, when was the data in the file gathered?
    date_created = models.IntegerField(blank=True, null=True)
    genre = models.ManyToManyField(Genre, blank=True)
    contributor_persons = models.ManyToManyField(Persons,blank=True,  through='ContributorRole', related_name='person_items')
    contributor_orgs = models.ManyToManyField(Organizations,blank=True,  through='ContributorRole', related_name='org_items')
    draft = models.BooleanField(default=True)

    update_manifest = models.BooleanField(default=False)

    # Possibly useful things to add: method to return visibility
    def get_class_name():
        # return the name of the class as a string
        return "Items"
        
    def get_fcrepo6_id(self):
        fcrepo6_id = self.name

        collection_iterator = self
        while(collection_iterator.collection_id != None):
            collection_iterator = collection_iterator.collection_id
            fcrepo6_id = f"{collection_iterator.name}/{fcrepo6_id}"

        return fcrepo6_id
    
    def get_solr_id(self):
        """unique id used in solr add or delete requests"""
        return f"{self.pk}:Items"
    
    def delete(self):
        solr.delete(id=self.get_solr_id())
        super(Items, self).delete()

class ContributorRole(models.Model):
    person = models.ForeignKey(Persons, on_delete=models.CASCADE, null=True, blank=True)
    organization = models.ForeignKey(Organizations, on_delete=models.CASCADE, null=True, blank=True)
    item = models.ForeignKey(Items, on_delete=models.CASCADE)
    role_name = models.ForeignKey(ParticipantRoles, on_delete=models.CASCADE)

    def clean(self):
        if not (self.person or self.organization):
            raise ValidationError("Role must have either a person or an organization")
        if self.person and self.organization:
            raise ValidationError("Role can't have both a person and an organization")

class File(models.Model):
    # ex. ailla:12345
    islandora_pid = models.CharField(max_length=20, null=True, blank=True)
    # ex. CTP001R003
    legacy_id = models.CharField(max_length=20, null=True, blank=True)
    parent_item = models.ForeignKey(Items, on_delete=models.CASCADE, related_name="files")
    # File type should probably eventually be a choices field?
    filename = models.CharField(max_length=256, blank=True)
    
    source_note = models.TextField(blank=True)
    place_created = models.TextField(blank=True)
    content_type = models.ForeignKey(MediaContentType, blank=True, null=True, on_delete=models.CASCADE)

    media_language = models.ManyToManyField(Languages,blank=True, related_name="media_language_files")
    media_type = models.CharField(max_length=30, blank=True)
    original_medium = models.ForeignKey(OriginalMediaType, blank=True, null=True, on_delete=models.CASCADE)
    tape_label = models.CharField(max_length=60, blank=True)
    
    # DIGITAL file creation date, auto generated for when file was uploaded to AILLA
    date_uploaded = models.DateTimeField(default=get_current_date)
    date_modified = models.DateTimeField(default=get_current_date)
    date_archived = models.DateTimeField(null=True, blank=True)
    date_created = models.IntegerField(null=True, blank=True)
    
    file_size = models.IntegerField(null=True,blank=True) # kilobytes
    extent = models.CharField(max_length=10, null=True,blank=True) # audio/video time-> hh:mm:ss, pdf/text pages-> int
    height = models.IntegerField(blank=True, null=True) # pixels
    width = models.IntegerField(blank=True, null=True) # pixels
    
    # Could be useful to split up size and duration
    fedora_uuid = models.CharField(max_length=300, blank=True)
    fedora_hash_location = models.TextField(null=True, blank=True)

    rights_statements = models.ManyToManyField(Rights, blank=True, related_name="rights_statements")
    rights_statement_note = models.TextField(blank=True, null=True)

    upload_status = models.IntegerField(default=-1)

    def get_solr_id(self):
        """unique id used in solr add or delete requests"""
        return f"{self.pk}:File"
    
    def delete(self):
        solr.delete(id=self.get_solr_id())
        super(File, self).delete()

class UserProfiles(models.Model):
    class UserRoles(models.TextChoices):
        SUPERADMIN = "SUPER", _("SuperAdmin")
        ADMIN = "ADMIN", _("Admin")
        USER = "USER", _("User")

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    affiliation = models.CharField(max_length=256, null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    country = models.CharField(max_length=256, null=True, blank=True)
    role = models.CharField(choices = UserRoles.choices, default="USER", max_length=5)
    verified = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True, null=True)
    disabled = models.BooleanField(default=False)
    
    @receiver(post_save, sender=User)
    def create_or_update_user_profile(sender, instance, created, **kwargs):
        user_profile, created = UserProfiles.objects.get_or_create(user=instance)

        if instance.is_superuser:
            user_profile.role = UserProfiles.UserRoles.SUPERADMIN
            user_profile.verified = True

        user_profile.save()

class UserCollectionRole(models.Model):
    class CollectionRoles(models.TextChoices):
        OWNER = "OWNER", _("Owner")
        EDITOR = "EDITOR", _("Editor")
        VIEWER = "VIEWER", _("Viewer")

    user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name="collection_roles")
    collection = models.ForeignKey(Collections, on_delete=models.CASCADE)
    role = models.CharField(choices=CollectionRoles.choices, max_length=6)

    class Meta:
        unique_together = ('user_profile', 'collection')  # Preventing duplicate users for the same collection

class UserFolderRole(models.Model):
    class FolderRoles(models.TextChoices):
        OWNER = "OWNER", _("Owner")
        EDITOR = "EDITOR", _("Editor")
        VIEWER = "VIEWER", _("Viewer")
        
    user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name="folder_roles")
    folder = models.ForeignKey(Folders, on_delete=models.CASCADE)
    role = models.CharField(choices=FolderRoles.choices, max_length=6)

    class Meta:
        unique_together = ('user_profile', 'folder')  # Preventing duplicate users for the same folder

class UserItemRole(models.Model):
    class ItemRoles(models.TextChoices):
        OWNER = "OWNER", _("Owner")
        EDITOR = "EDITOR", _("Editor")
        VIEWER = "VIEWER", _("Viewer")
        
    user_profile = models.ForeignKey(UserProfiles, on_delete=models.CASCADE, related_name="item_roles")
    item = models.ForeignKey(Items, on_delete=models.CASCADE)
    role = models.CharField(choices=ItemRoles.choices, max_length=6)

    class Meta:
        unique_together = ('user_profile', 'item')  # Preventing duplicate users for the same item

