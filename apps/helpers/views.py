from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test
from django_tables2 import SingleTableMixin


class PageHeaderMixin:
    page_title = None
    add_link = None
    list_link = None
    add_perms = None
    request = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page_title
        if self.add_perms and self.request.user.has_perm(self.add_perms):
            context['add_link'] = self.add_link
        context['list_link'] = self.list_link
        return context


class PageHeaderNoPerMixin:
    page_title = None
    add_link = None
    list_link = None
    add_perms = None
    request = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.page_title
        context['add_link'] = self.add_link
        context['list_link'] = self.list_link
        return context


class CustomSingleTableMixin(SingleTableMixin):
    request = None
    view_perms = None
    edit_perms = None
    delete_perms = None

    def get_table_kwargs(self):
        ctx = super().get_table_kwargs()
        if self.view_perms:
            ctx['view_perms'] = self.request.user.has_perm(self.view_perms)
        if self.edit_perms:
            ctx['edit_perms'] = self.request.user.has_perm(self.edit_perms)
        if self.delete_perms:
            ctx['delete_perms'] = self.request.user.has_perm(self.delete_perms)
        if not ctx.get('view_perms', None) and not ctx.get('edit_perms', None) and not ctx.get('delete_perms', None):
            return {'exclude': ('action',)}
        else:
            return ctx


class CustomSingleNoPerTableMixin(SingleTableMixin):
    request = None
    view_perms = None
    edit_perms = None
    delete_perms = None

    def get_table_kwargs(self):
        ctx = super().get_table_kwargs()
        ctx['view_perms'] = self.request.user.has_perm(self.view_perms)
        ctx['edit_perms'] = self.request.user.has_perm(self.edit_perms)
        ctx['delete_perms'] = self.request.user.has_perm(self.delete_perms)
        if not ctx.get('view_perms', None) and not ctx.get('edit_perms', None) and not ctx.get('delete_perms', None):
            return {'exclude': ('action',)}
        else:
            return ctx


def staff_required(
        function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None
):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url=login_url,
        redirect_field_name=redirect_field_name,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
