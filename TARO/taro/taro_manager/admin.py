"""
Custom Taro Admin. For more info: https://docs.djangoproject.com/en/3.1/ref/contrib/admin/ or
https://github.com/originalankur/awesome-django-admin for additional ways to customize Django admin
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_email.models import EmailDevice

from taro.taro_manager.models import User, FindingAid, Repository, BrowseTerm, AllowList


class TaroAdminSite(OTPAdminSite):
    """
    Inheriting from OTPAdminSite. This is passed to urls.py and used
    to patch admin.site directly to enforce 2FA
    """
    pass


class TaroAdmin(UserAdmin):
    """
    Overriding default user creation to customize fields in the admin GUI and to
    automate user password creation and 2-factor device setup
    """
    pass

class FindingAidAdmin(admin.ModelAdmin):
    """
    FindingAid Admin Configuration
    """
    pass

class RepositoryAdmin(admin.ModelAdmin):
    """
    Repository Admin. List shows repository name.
    """
    pass


class BrowseTermsAdmin(admin.ModelAdmin):
    """
    BrowseTermsAdmin Configuration
    """
    pass


class AllowListsAdmin(admin.ModelAdmin):
    """
    AllowListsAdmin Configuration
    """
    pass


admin.site.register(FindingAid, FindingAidAdmin)
admin.site.register(Repository, RepositoryAdmin)
admin.site.register(User, TaroAdmin)
admin.site.register(BrowseTerm, BrowseTermsAdmin)
admin.site.register(AllowList, AllowListsAdmin)
admin.site.unregister(TOTPDevice)
admin.site.unregister(EmailDevice)
