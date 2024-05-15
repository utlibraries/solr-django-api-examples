"""
Taro Custom Utilities - functions that can be useful throughout application go here.
"""
import logging
import os
import random
import string
import xml.etree.ElementTree as ET

from rest_framework.throttling import UserRateThrottle
from django.contrib.auth.models import AnonymousUser
from taro import settings
from taro.taro_manager.logger import logger


class ExceptionalUserRateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        """
        Overriding DRF's default UserRateThrottle so that we
        can set per-user throttling (helpful in the case of apps
        like the React front-end display).
        """
        if self.rate is None:
            return True

        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        self.history = self.cache.get(self.key, [])
        self.now = self.timer()

        override_rate = settings.REST_FRAMEWORK['OVERRIDE_THROTTLE_RATES'].get(
            request.user.username,
            None,
        )
        if override_rate is not None:  # Set throttling for react-site
            self.num_requests, self.duration = self.parse_rate(override_rate)
        elif isinstance(request.user, AnonymousUser):  # Set throttling for anon requests
            override_rate= settings.REST_FRAMEWORK['OVERRIDE_THROTTLE_RATES'].get(
                'anon',
                '100/hour',
            )
            self.num_requests, self.duration = self.parse_rate(override_rate)
        else:  # Set throttling for authorized users
            override_rate = settings.REST_FRAMEWORK['OVERRIDE_THROTTLE_RATES'].get(
                'user',
                '10000/hour',
            )
            self.num_requests, self.duration = self.parse_rate(override_rate)

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            logger.debug(f"Requests from {request.user} throttled.")
            return self.throttle_failure()
        return self.throttle_success()


def resolve_attributes_lookup(self, current_objects, attributes):
    """
    This is copy-pasted from https://github.com/django-haystack/django-haystack/blob/master/haystack/fields.py.
    Lines 52-55 have been modified to fix a known bug: https://github.com/SocialSchools/django-haystack/commit/1515c100e02ebde0b31023ff7aa771da39a1e0ae

    Recursive method that looks, for one or more objects, for an attribute that can be multiple
    objects (relations) deep.
    """
    values = []

    for current_object in current_objects:
        if not hasattr(current_object, attributes[0]):
            raise SearchFieldError(
                "The model '%r' does not have a model_attr '%s'."
                % (repr(current_object), attributes[0])
            )
        if len(attributes) > 1:
            current_objects_in_attr = self.get_iterable_objects(
                getattr(current_object, attributes[0])
            )
            values.extend(
                self.resolve_attributes_lookup(
                    current_objects_in_attr, attributes[1:]
                )
            )
            continue
        current_object = getattr(current_object, attributes[0])
        if current_object is None:
            current_object = None
        try:
            values.append(current_object())
        except TypeError:
            values.append(current_object)

    return values


def return_xml_values_as_text(xml):
    """
    Returns XML values as text
    """
    data = ''
    elem = ET.ElementTree(ET.fromstring(xml))
    for elt in elem.iter():
        if elt.text:
            if str(elt.text).isspace() is False:
                # removes all whitespace > 1 space, line breaks, tabs, etc.
                clean_text = " ".join(str(elt.text).split())
                # ensures there's at least 1 whitespace between values
                clean_text += " "
                data += clean_text
    return data.strip()


def get_random_alphanumeric_string(string_length=6):
    """
    Get random alpanumeric string
    """
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join((random.choice(letters_and_digits) for i in range(string_length)))


def find_dict_key(obj, key):
    """
    Utility function to recursively search through a dictionary for a specified key
    """
    if key in obj:
        return obj[key]
    for keys, value in obj.items():   # pylint: disable=unused-variable
        if isinstance(value, dict):
            item = find_dict_key(value, key)
            if item is not None:
                return item
    return None


def is_deployed_react_app(request):
    """
    Utility function to check if request is coming from a deployed React environment.
    """
    staging = "Token " + os.environ.get('REACT_STAGING') if os.environ.get('REACT_STAGING') else None
    production = "Token " + os.environ.get('REACT_PROD') if os.environ.get('REACT_PROD') else None
    if request.headers.get('Authorization') == staging or request.headers.get('Authorization') == production:
        return True
    return False
