from django.contrib import admin
from .models import MainSlider, MenuSection, MenuGroup, MenuItem


@admin.register(MainSlider)
class MainSliderAdmin(admin.ModelAdmin):
    list_display = ("serial", "title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "description")
    ordering = ("serial",)


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
