"""
Taro Models. More information on Django models:
https://docs.djangoproject.com/en/3.1/topics/db/models/
"""
import os
import shutil
from pathlib import Path

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone


from taro.taro_manager.finding_aid_parser import ParsedFindingAid
from taro.taro_manager.exception_converter import ConvertExceptions
from taro.taro_manager.logger import logger


class Repository(models.Model):
    """
    Repository model. Fields: name, abbreviated name, description, contact email, logo, home page
    link and about page link.
    """
    UT_AUSTIN = 'utexas'
    TEXAS_TECH = 'ttu'
    BAYLOR = 'baylor'
    HOUSTON = 'uh'
    RICE = 'rice'
    TAMU = 'tamu'
    INSTITUTION_CHOICES = [
        (UT_AUSTIN, 'University of Texas at Austin'),
        (TEXAS_TECH, 'Texas Tech'),
        (BAYLOR, 'Baylor University'),
        (HOUSTON, 'University of Houston'),
        (RICE, 'Rice University'),
        (TAMU, 'Texas A&M'),
    ]
    name = models.CharField(max_length=200)
    abbr_name = models.CharField(max_length=10, unique=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField()
    internal_email = models.EmailField(max_length=50, null=True)
    external_email = models.EmailField(max_length=50, null=True)
    logo = models.ImageField(null=True)
    access_link = models.URLField(max_length=200, null=True)
    home_link = models.URLField(max_length=200)
    about_link = models.URLField(max_length=200)
    legacy_institution_member = models.BooleanField(default=False, null=True)
    legacy_institution = models.CharField(max_length=6, choices=INSTITUTION_CHOICES, null=True)
    legacy_unit = models.CharField(max_length=6, null=True)
    taro_identifier = models.CharField(max_length=60, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Overwriting default save() to create a path for repository where XMLs are stored on mount
        when a new repository is created.
        """
        created = self._state.adding  # returns True on creation (not update)
        if created:
            # create static file directories in the file mount if they don't already exist
            Path(f"{os.environ.get('MEDIA_ROOT')}/{self.abbr_name}/xml_files").mkdir(parents=True, exist_ok=True)
            Path(f"{os.environ.get('MEDIA_ROOT')}/{self.abbr_name}/logo").mkdir(parents=True, exist_ok=True)
            logger.debug(f"Repository {self.abbr_name} has been created.")
        super().save()
        if self.logo:
            filename = self.logo.name.replace(f'{self.abbr_name}/logo/', '')
            if self.logo.name != f'{self.abbr_name}/logo/{filename}':
                initial_path = self.logo.path
                self.logo.name = f'{self.abbr_name}/logo/{filename}'
                try:
                    new_path = f'/{os.environ.get("MEDIA_ROOT")}/{self.logo.name}'
                    shutil.move(initial_path, new_path)
                except FileNotFoundError:  # /app/ is needed when running locally
                    new_path = f'/app/{os.environ.get("MEDIA_ROOT")}/{self.logo.name}'
                    shutil.move(initial_path, new_path)
                self.save()

    def __str__(self):
        return str(self.name)

    class Meta:   # pylint: disable=too-few-public-methods
        """
        This makes sure that Repository's name on Admin site is Repositories (Django default is
        Repositorys).
        """
        verbose_name_plural = "Repositories"


class Language(models.Model):
    """
    Language Model. Many to many relationship to finding aids.
    """
    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.label)


class Creator(models.Model):
    """
    Creator Model. Many to many relationship to finding aids.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.name)


class StartDate(models.Model):
    """
    StartDate Model. Many to many relationship to finding aids.
    """
    date = models.IntegerField(validators=[MaxValueValidator(255)])

    def __str__(self):
        return str(self.date)


class EndDate(models.Model):
    """
    EndDate Model. Many to many relationship to finding aids.
    """
    date = models.IntegerField(validators=[MaxValueValidator(255)])

    def __str__(self):
        return str(self.date)


class GeographicArea(models.Model):
    """
    GeographicArea Model. Many to many relationship to finding aids.
    """
    area = models.CharField(max_length=255)

    def __str__(self):
        return str(self.area)


class SubjectTopic(models.Model):
    """
    Subject Topics Model. Many to many relationship to finding aids.
    """
    text = models.CharField(max_length=255)

    def __str__(self):
        return str(self.text)


class SubjectPerson(models.Model):
    """
    Subject Person Model. Many to many relationship to finding aids.
    """
    text = models.CharField(max_length=255)

    def __str__(self):
        return str(self.text)


class SubjectOrganization(models.Model):
    """
    Subject Organizations Model. Many to many relationship to finding aids.
    """
    text = models.CharField(max_length=255)

    def __str__(self):
        return str(self.text)


class FindingAidDisplayField(models.Model):
    value = models.JSONField(null=True)
    repository = models.ForeignKey(Repository, on_delete=models.PROTECT, related_name="display_fields", null=True)
    filename = models.CharField(max_length=255, null=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, reparse=False):
        """
        Overwriting default save(). This will delete any duplicate display field objects.
        """
        if reparse is False:
            matches = FindingAidDisplayField.objects.filter(repository=self.repository, filename=self.filename)
            if matches:
                for match in matches:
                    match.delete()
        super().save()


class FindingAid(models.Model):
    """
    Finding Aid Model. Fields: title, abstract, digital (boolean), taro identifier, repository,
    xml, all content (text of entire finding aid), date added and file name.
    """
    title = models.TextField(null=True)
    abstract = models.TextField(null=True)
    digital = models.BooleanField(default=False)
    taro_identifier = models.CharField(max_length=50, unique=True)
    repository = models.ForeignKey(Repository, on_delete=models.PROTECT, related_name="finding_aids")
    json = models.JSONField(null=True)
    display_fields = models.OneToOneField(
        FindingAidDisplayField,
        on_delete=models.CASCADE,
        null=True,
    )
    all_content = models.TextField(null=True)
    date_added = models.DateTimeField(default=timezone.now)
    filename = models.CharField(max_length=50, null=False)
    override_warnings = models.BooleanField(default=False)
    languages = models.ManyToManyField(Language)
    creators = models.ManyToManyField(Creator)
    start_dates = models.ManyToManyField(StartDate)
    end_dates = models.ManyToManyField(EndDate)
    geographic_areas = models.ManyToManyField(GeographicArea)
    subject_topics = models.ManyToManyField(SubjectTopic)
    subject_persons = models.ManyToManyField(SubjectPerson)
    subject_organizations = models.ManyToManyField(SubjectOrganization)
    xml = models.FileField()

    def __str__(self):
        return str(self.title)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """
        Overwriting default save(). This will move the XML file to repository's XML path on mount.
        """
        logger.debug(f"Finding aid {self.filename} for repository {self.repository} has been "
                     f"saved.")
        super().save()
        if self.xml.name != f'{self.repository.abbr_name}/xml_files/{self.filename}':
            initial_path = self.xml.path
            self.xml.name = f'{self.repository.abbr_name}/xml_files/{self.filename}'
            try:
                new_path = f'/{os.environ.get("MEDIA_ROOT")}/{self.xml.name}'
                shutil.move(initial_path, new_path)
            except FileNotFoundError:  # /app/ is needed when running locally
                new_path = f'/app/{os.environ.get("MEDIA_ROOT")}/{self.xml.name}'
                shutil.move(initial_path, new_path)
            self.save()


    @staticmethod
    @ConvertExceptions(IndexError, (None, 'Error Parsing XML'))
    def create_dict_from_xml(xml_file, repository):
        """
        Creates dictionary of values from the XML file.
        :param xml_file:
        :param repository: repository object
        :return: single fields and multivalue fields
        """
        parsed = ParsedFindingAid(xml_file)

        # These fields are set with information external to the finding aid content
        try:
            parsed.fields['repository'] = repository
            parsed.fields['xml'] = xml_file
            parsed.fields['filename'] = xml_file._name
        except AttributeError:
            parsed.fields['repository'] = repository
            parsed.fields['xml'] = xml_file
            parsed.fields['filename'] = xml_file.name

        return parsed.fields, parsed.multivalue_fields

    class Meta:   # pylint: disable=too-few-public-methods
        """
        This makes sure that Finding Aid's name on Admin site is Finding Aids (Django default is
        FindingAids).
        """
        verbose_name_plural = "Finding Aids"


class BrowseTerm(models.Model):
    value = models.CharField(max_length=255)

    def __str__(self):
        return str(self.value)


class AllowList(models.Model):
    label = models.CharField(max_length=255)
    browse_terms = models.ManyToManyField(BrowseTerm)

    def __str__(self):
        return str(self.label)


class User(AbstractUser):
    """
    See https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#substituting-a-custom-user-model   # pylint: disable=line-too-long
    """
    repositories = models.ManyToManyField(Repository, blank=True)
    email = models.EmailField(unique=True)
    dual_auth = models.BooleanField(
        default=False)  # do they have a secure (not temporary) password and dual authentication?
    is_staff = models.BooleanField(default=True)  # we don't have any users that are not also staff
    # Note: can use built-in is_staff field to determine access to admin site.