from django.contrib import admin
from .models import MainSlider, MenuSection, MenuGroup, MenuItem, HomeSection, Contact, SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'email', 'phone', 'updated_at')

    def has_add_permission(self, request):
        # Allow adding only if no settings exist
        if SiteSetting.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of settings
        return False


@admin.register(MainSlider)
class MainSliderAdmin(admin.ModelAdmin):
    list_display = ("serial", "title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("serial",)


@admin.register(HomeSection)
class HomeSectionAdmin(admin.ModelAdmin):
    list_display = ("section_type", "title", "is_active", "order")
    list_editable = ("is_active", "order")
    list_filter = ("is_active", "section_type")
    search_fields = ("title", "section_type")
    ordering = ("order",)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ("name", "title", "href", "badge", "style", "image", "order", "is_active")


class MenuGroupInline(admin.StackedInline):
    model = MenuGroup
    extra = 1
    fields = ("name", "title", "is_featured", "order", "is_active")
    show_change_link = True


@admin.register(MenuSection)
class MenuSectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    inlines = [MenuGroupInline]
    ordering = ("order",)


@admin.register(MenuGroup)
class MenuGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "section", "is_featured", "order", "is_active")
    list_filter = ("section", "is_featured", "is_active")
    search_fields = ("name", "title", "section__name", "section__slug")
    inlines = [MenuItemInline]
    ordering = ("section", "order")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "href", "badge", "order", "is_active")
    list_filter = ("group__section", "group", "is_active")
    search_fields = ("name", "title", "href", "group__name", "group__section__slug")
    ordering = ("group", "order")


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "phone", "subject", "message", "created_at", "updated_at")
    list_editable = ("status",)
    ordering = ("-created_at",)
    
    fieldsets = (
        ("Contact Information", {
            "fields": ("name", "email", "phone")
        }),
        ("Message", {
            "fields": ("subject", "message")
        }),
        ("Status & Notes", {
            "fields": ("status", "staff_notes")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
