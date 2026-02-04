import json
from django.core.management.base import BaseCommand
from apps.cms.models import MenuSection, MenuGroup, MenuItem

SAMPLE_DATA = {
  "women": {
    "trending": [
      { "name": "New Arrivals", "href": "/collections/new-arrivals" },
      { "name": "Best Sellers", "href": "/category/women-bestsellers" },
      { "name": "Cosy Luxe X Soft Sculpt", "href": "/collections/cosy-luxe", "badge": "🔥" },
      { "name": "Whitney Simmons", "href": "/collections/whitney-simmons" },
      { "name": "The Analis Cruz Collection", "href": "/collections/analis-cruz" },
      { "name": "Cherry Purple Gym Sets", "href": "/collections/cherry-purple", "style": "text-purple-600" },
      { "name": "Winter Shop", "href": "/collections/winter" }
    ],
    "leggings": [
      { "name": "All Leggings", "href": "/category/leggings" },
      { "name": "High-Waisted Leggings", "href": "/collections/high-waisted-leggings" },
      { "name": "Scrunch Butt Leggings", "href": "/collections/scrunch-butt" },
      { "name": "Black Leggings", "href": "/collections/black-leggings" },
      { "name": "Flare Leggings", "href": "/collections/flare-leggings" },
      { "name": "Seamless Leggings", "href": "/collections/seamless-leggings" },
      { "name": "Leggings With Pockets", "href": "/collections/leggings-pockets" },
      { "name": "Tall Leggings", "href": "/collections/tall-leggings" }
    ],
    "products": [
      { "name": "All Products", "href": "/category/women-all" },
      { "name": "Leggings", "href": "/category/leggings" },
      { "name": "T-Shirts & Tops", "href": "/category/tops" },
      { "name": "Sports Bras", "href": "/category/sports-bras" },
      { "name": "Long Sleeves", "href": "/category/long-sleeves" },
      { "name": "Shorts", "href": "/category/shorts" },
      { "name": "Matching Sets", "href": "/category/matching-sets" }
    ],
    "explore": [
      { "name": "Leggings Guide", "href": "/guides/leggings" },
      { "name": "Sports Bra Guide", "href": "/guides/sports-bra" },
      { "name": "Your Edit", "href": "/your-edit" },
      { "name": "Gymshark Loyalty", "href": "/loyalty" },
      { "name": "As Seen On Social", "href": "/social" }
    ],
    "featured": [
      { "title": "COSY LUXE", "image": None, "href": "/collections/cosy-luxe" }
    ]
  },
  "men": {
    "trending": [
      { "name": "New Arrivals", "href": "/collections/men-new-arrivals" },
      { "name": "Best Sellers", "href": "/category/men-bestsellers" },
      { "name": "Winter Shop", "href": "/collections/men-winter" }
    ],
    "products": [
      { "name": "All Products", "href": "/category/men-all" },
      { "name": "T-Shirts & Tops", "href": "/category/men-tops" },
      { "name": "Shorts", "href": "/category/men-shorts" },
      { "name": "Hoodies & Sweatshirts", "href": "/category/men-hoodies" }
    ],
    "featured": [
      { "title": "MEN'S ESSENTIALS", "image": None, "href": "/collections/men-essentials" }
    ]
  },
  "accessories": {
    "products": [
      { "name": "All Accessories", "href": "/collections/new-accessories" },
      { "name": "Bags & Backpacks", "href": "/category/bags" },
      { "name": "Water Bottles", "href": "/category/bottles" },
      { "name": "Gym Equipment", "href": "/category/equipment" }
    ],
    "featured": [
      { "title": "ACCESSORIES", "image": None, "href": "/collections/new-accessories" }
    ]
  }
}


class Command(BaseCommand):
    help = "Seed the mega menu with sample data. Optionally provide a JSON file path with --file."

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, help='Path to JSON file containing mega menu data')
        parser.add_argument('--flush', action='store_true', help='Delete existing menu data first')

    def handle(self, *args, **options):
        file_path = options.get('file')
        flush = options.get('flush')
        data = SAMPLE_DATA
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        if flush:
            MenuItem.objects.all().delete()
            MenuGroup.objects.all().delete()
            MenuSection.objects.all().delete()
        for section_slug, groups in data.items():
            section, _ = MenuSection.objects.get_or_create(slug=section_slug, defaults={'name': section_slug.title()})
            order_counter = 0
            for group_name, items in groups.items():
                is_featured = group_name == 'featured'
                group, _ = MenuGroup.objects.get_or_create(section=section, name=group_name, defaults={'is_featured': is_featured, 'order': order_counter})
                group.is_featured = is_featured
                group.order = order_counter
                group.save()
                item_order = 0
                for item in items:
                    if is_featured:
                        MenuItem.objects.create(
                            group=group,
                            name=item.get('title') or item.get('name') or group_name,
                            title=item.get('title') or item.get('name'),
                            href=item['href'],
                            order=item_order,
                        )
                    else:
                        MenuItem.objects.create(
                            group=group,
                            name=item.get('name') or item.get('title') or 'Item',
                            title=item.get('title'),
                            href=item['href'],
                            badge=item.get('badge'),
                            style=item.get('style'),
                            order=item_order,
                        )
                    item_order += 1
                order_counter += 1
        self.stdout.write(self.style.SUCCESS('Mega menu seeded successfully.'))

