from django import template
import calendar
from django.contrib.auth.models import Group

register = template.Library()


# @register.filter
# def sort_by_sequence(queryset):
#     return queryset.order_by('sequence')
#
#
# @register.filter
# def month_name(month_number):
#     a = int(month_number)
#     return calendar.month_name[a]
#
#
# @register.filter
# def test_tag(a, b):
#     a = int(a) + int(b)
#     return a

# @register.filter(name='has_group')
# def has_group(user, group_name):
#     try:
#         group = Group.objects.get(name=group_name)
#         return group in user.groups.all()
#     except Group.DoesNotExist:
#         return False
