from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver


@receiver(pre_delete)
def delete_files_on_object_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding object is deleted.
    """
    for field in sender._meta.get_fields():
        if isinstance(field, (models.ImageField, models.FileField)):
            field_value = getattr(instance, field.name)
            if field_value:
                field_value.delete(save=False)
