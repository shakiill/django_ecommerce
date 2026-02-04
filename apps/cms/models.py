from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# Create your models here.
class MainSlider(models.Model):
    serial = models.PositiveIntegerField(default=10)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='main_sliders/')
    link = models.URLField(blank=True, null=True)
    button_text = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class MenuSection(models.Model):
    """Top-level mega menu section (e.g., women, men, accessories)."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True, help_text="Identifier used as key in mega menu JSON")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuGroup(models.Model):
    """Group within a section (e.g., trending, leggings, products, featured)."""
    section = models.ForeignKey(MenuSection, related_name="groups", on_delete=models.CASCADE)
    name = models.CharField(max_length=100, help_text="Internal group name (e.g., trending, featured)")
    title = models.CharField(max_length=150, blank=True, null=True, help_text="Optional display title if different from name")
    is_featured = models.BooleanField(default=False, help_text="Marks this group as 'featured' with image items")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("section", "name")
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.section.slug}:{self.name}"


class MenuItem(models.Model):
    """Item inside a menu group."""
    group = models.ForeignKey(MenuGroup, related_name="items", on_delete=models.CASCADE)
    # For non-featured groups we'll output 'name'; for featured groups we'll output 'title'. Store both for flexibility.
    name = models.CharField(max_length=150, help_text="Name label for standard groups")
    title = models.CharField(max_length=150, blank=True, null=True, help_text="Title label for featured items")
    href = models.CharField(max_length=300, help_text="Relative or absolute URL path")
    badge = models.CharField(max_length=20, blank=True, null=True, help_text="Optional badge emoji or short text")
    style = models.CharField(max_length=120, blank=True, null=True, help_text="Optional CSS utility class")
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True, help_text="Optional image (featured)")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name or self.title or "MenuItem"


MEGA_MENU_CACHE_KEY = "public:mega_menu"


def invalidate_mega_menu_cache():
    if getattr(settings, 'PUBLIC_API_CACHE_ENABLED', True):
        cache.delete(MEGA_MENU_CACHE_KEY)


@receiver(post_save, sender=MenuSection)
@receiver(post_save, sender=MenuGroup)
@receiver(post_save, sender=MenuItem)
@receiver(post_delete, sender=MenuSection)
@receiver(post_delete, sender=MenuGroup)
@receiver(post_delete, sender=MenuItem)
def _mega_menu_changed(sender, **kwargs):  # pragma: no cover - simple signal
    invalidate_mega_menu_cache()
