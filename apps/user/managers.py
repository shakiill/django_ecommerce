from django.contrib.auth.base_user import BaseUserManager


class CustomerManager(BaseUserManager):
    def get_queryset(self):
        return super(CustomerManager, self).get_queryset().filter(groups__name='customer')


class StaffManager(BaseUserManager):
    def get_queryset(self):
        return super(StaffManager, self).get_queryset().filter(groups__name='staff')
