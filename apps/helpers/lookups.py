from apps.helpers.widgets import CustomSelect2Mixin
# from apps.location.models import Country, State, City
#
#
# class CountrySelect2Widget(CustomSelect2Mixin):
#     model = Country
#     queryset = Country.objects.all().order_by('name')
#     search_fields = ['name__icontains', ]
#
#
# class StateSelect2Widget(CustomSelect2Mixin):
#     model = State
#     queryset = State.objects.all().order_by('name')
#     search_fields = ['name__icontains', ]
#     dependent_fields = {'country': 'country_id'}
#
#
# class CitySelect2Widget(CustomSelect2Mixin):
#     model = City
#     queryset = City.objects.all().order_by('name')
#     search_fields = ['name__icontains', ]
#     dependent_fields = {'state': 'state_id'}
