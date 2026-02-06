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


class HomeSection(models.Model):
    SECTION_CHOICES = [
        ('hero', 'Hero Slider'),
        ('flash_sale', 'Flash Sale'),
        ('categories', 'Featured Categories'),
        ('new_arrivals', 'New Arrivals'),
        ('popular', 'Popular Products'),
        ('testimonials', 'Testimonials'),
        ('payment_trust', 'Payment & Trust'),
        ('features', 'Features'),
        ('lookbook', 'Lookbook Collection'),
        ('brand_story', 'Brand Story Video'),
        ('instagram', 'Instagram Feed'),
    ]
    section_type = models.CharField(max_length=50, choices=SECTION_CHOICES, unique=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.get_section_type_display()


class Contact(models.Model):
    """Model to store contact form submissions."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    staff_notes = models.TextField(blank=True, null=True, help_text="Internal notes for staff members")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'

    def __str__(self):
        return f"{self.name} - {self.subject}"


class SiteSetting(models.Model):
    """Global site settings for storefront and CMS."""
    business_name = models.CharField(max_length=200, default="My Store")
    logo = models.ImageField(upload_to='site_settings/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site_settings/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    working_hours = models.TextField(blank=True, null=True)

    # Social links
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)

    # Theme colors
    primary_color = models.CharField(max_length=20, default="#ff4e50", help_text="Primary theme color")
    secondary_color = models.CharField(max_length=20, default="#111111", help_text="Secondary theme color")
    accent_color = models.CharField(max_length=20, default="#f9d423", help_text="Accent color (e.g. for badges)")

    # Meta / SEO
    footer_text = models.TextField(blank=True, null=True)
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.business_name

    def save(self, *args, **kwargs):
        # Optional: enforce singleton pattern at model level
        if not self.pk and SiteSetting.objects.exists():
            # You could raise an error or just update the existing one
            # For simplicity in admin, we'll let the admin handle it or just return
            return
        super().save(*args, **kwargs)
