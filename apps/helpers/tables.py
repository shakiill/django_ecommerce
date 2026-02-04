import django_tables2 as tables
from django.urls import reverse
from django.utils.safestring import mark_safe
import itertools


class CustomTable(tables.Table):
    def __init__(self, *args, **kwargs):
        self.edit_perms = kwargs.pop('edit_perms', None)
        self.delete_perms = kwargs.pop('delete_perms', None)
        self.view_perms = kwargs.pop('view_perms', None)
        super().__init__(*args, **kwargs)

    detail_url = None
    edit_url = None
    delete_url = None

    view_perms = None
    edit_perms = None
    delete_perms = None
    action = tables.Column(empty_values=(), orderable=False, attrs={"td": {"width": "120"}})
    counter = tables.Column(empty_values=(), verbose_name='#', orderable=False)

    def render_action(self, record):
        url = ''
        if self.view_perms and self.detail_url:
            detail_url = reverse(self.detail_url, args=[record.pk])
            url += '''<a href="%s" class="btn btn-sm btn-light-info"><i class="flaticon-eye"></i></a>''' % detail_url
        if self.edit_perms and self.edit_url:
            if self.detail_url:
                url += ' '
            edit_url = reverse(self.edit_url, args=[record.pk])
            url += '''<a href="%s" class="btn btn-sm btn-light-warning"><i class="flaticon-edit"></i></a>''' % edit_url
        if self.delete_perms and self.delete_url:
            del_url = reverse(self.delete_url, args=[record.pk])
            if self.edit_url:
                url += ' '
            url += '''<a href="%s" class="btn btn-sm btn-light-danger"><i class="flaticon-delete"></i></a>''' % del_url
        return mark_safe(url)

    def render_counter(self):
        self.row_counter = getattr(self, 'row_counter',
                                   itertools.count(self.page.start_index()))
        return next(self.row_counter)
