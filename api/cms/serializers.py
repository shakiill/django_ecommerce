from rest_framework import serializers

from apps.cms.models import MainSlider, MenuSection, MenuGroup, MenuItem, Contact, SiteSetting


class SiteSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSetting
        fields = '__all__'


class MainSliderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainSlider
        fields = '__all__'


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions."""
    class Meta:
        model = Contact
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']


class ContactListSerializer(serializers.ModelSerializer):
    """Serializer for staff to view contact submissions."""
    class Meta:
        model = Contact
        fields = '__all__'


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ("id", "name", "title", "href", "badge", "style", "image", "order")


class MenuGroupSerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = MenuGroup
        fields = ("id", "name", "title", "is_featured", "order", "items")


class MenuSectionSerializer(serializers.ModelSerializer):
    groups = MenuGroupSerializer(many=True, read_only=True)

    class Meta:
        model = MenuSection
        fields = ("id", "name", "slug", "order", "groups")


def build_mega_menu_structure(sections):
    """Return dict keyed by section.slug following frontend requirements.

    Structure:
    {
      "women": {
         "trending": [ { name, href, badge?, style? }, ... ],
         "featured": [ { title, image, href }, ... ],
         ... other groups ...
      },
      "men": { ... }
    }
    """
    output = {}
    for section in sections:
        section_obj = {}
        for group in section.groups.all():
            if not group.is_active:
                continue
            active_items = [item for item in group.items.all() if item.is_active]
            if group.is_featured:
                # Featured: use title/image/href
                section_obj[group.name] = [
                    {
                        "title": item.title or item.name,
                        "image": item.image.url if item.image else None,
                        "href": item.href,
                    }
                    for item in active_items
                ]
            else:
                section_obj[group.name] = [
                    {
                        "name": item.name or item.title,
                        "href": item.href,
                        **({"badge": item.badge} if item.badge else {}),
                        **({"style": item.style} if item.style else {}),
                    }
                    for item in active_items
                ]
        output[section.slug] = section_obj
    return output
