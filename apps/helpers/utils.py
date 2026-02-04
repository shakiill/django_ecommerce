import calendar
import re

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from rest_framework.authentication import SessionAuthentication


def choices_with_label(choices):
    return [("", "Select from items"), ] + list(choices)[1:]


def reverse_querystring(view, urlconf=None, args=None, kwargs=None, current_app=None, query_kwargs=None):
    """Custom reverse to handle query strings.
    Usage:
        reverse('app.views.my_view', kwargs={'pk': 123}, query_kwargs={'search': 'Bob'})
    """
    base_url = reverse(view, urlconf=urlconf, args=args, kwargs=kwargs, current_app=current_app)
    if query_kwargs:
        return '{}?{}'.format(base_url, urlencode(query_kwargs))
    return base_url


def month_list():
    months = []
    for month_idx in range(1, 13):
        months.append((month_idx, calendar.month_name[month_idx]))
    return months


def day_list():
    day = []
    for index in range(1, 32):
        day.append((index, index))
    return day


def last_year_month():
    now = timezone.now()
    month = now.month - 1
    year = now.year
    if now.month == 1:
        month = 12
        year = now.year - 1
    return {
        'year': year,
        'month': month
    }


def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        pass


class BoundedFloatField(models.FloatField):
    def __init__(self, min_value=None, max_value=None, *args, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value': self.max_value}
        defaults.update(kwargs)
        return super().formfield(**defaults)


from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    """
    Allows access only to staff users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)
