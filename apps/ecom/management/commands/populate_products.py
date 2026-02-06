import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker
from apps.master.models import Category, Brand, Unit, Tax, Attribute, AttributeValue, Warehouse
from apps.ecom.models import Product, ProductVariant
from apps.inventory.models import Stock

class Command(BaseCommand):
    help = 'Populates the database with sample product data'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=50, help='Number of products to create')
        parser.add_argument('--clean', action='store_true', help='Delete existing products first')

    def handle(self, *args, **kwargs):
        fake = Faker()
        count = kwargs['count']
        clean = kwargs['clean']

        if clean:
            self.stdout.write('Cleaning existing data...')
            # Be careful with deletion order due to CASCADE
            Stock.objects.all().delete()
            ProductVariant.objects.all().delete()
            Product.objects.all().delete()
            # We don't delete master data to avoid breaking other things, or we can if strictly requested.
            # For now, let's keep master data or ensure we defaults.
            
        self.stdout.write('Creating master data...')
        
        # Warehouses
        warehouse1, _ = Warehouse.objects.get_or_create(
            code='WH-MAIN', defaults={'name': 'Main Warehouse', 'address': fake.address(), 'is_default': True}
        )
        warehouse2, _ = Warehouse.objects.get_or_create(
            code='WH-SEC', defaults={'name': 'Secondary Warehouse', 'address': fake.address()}
        )
        warehouses = [warehouse1, warehouse2]

        # Taxes
        tax, _ = Tax.objects.get_or_create(
            code='VAT-15', defaults={'name': 'VAT 15%', 'rate': 15.0}
        )
        
        # Units
        unit, _ = Unit.objects.get_or_create(name='Piece', defaults={'short_name': 'pcs'})
        
        # Attributes
        color_attr, _ = Attribute.objects.get_or_create(name='Color', defaults={'slug': 'color'})
        size_attr, _ = Attribute.objects.get_or_create(name='Size', defaults={'slug': 'size'})
        
        colors = ['Red', 'Blue', 'Green', 'Black', 'White', 'Yellow', 'Purple']
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        
        color_values = []
        for c in colors:
            val, _ = AttributeValue.objects.get_or_create(attribute=color_attr, value=c, defaults={'display_order': 0})
            color_values.append(val)
            
        size_values = []
        for i, s in enumerate(sizes):
            val, _ = AttributeValue.objects.get_or_create(attribute=size_attr, value=s, defaults={'display_order': i})
            size_values.append(val)

        # Categories
        categories = []
        cat_structure = {
            'Electronics': ['Phones', 'Laptops', 'Cameras', 'Accessories'],
            'Clothing': ['Men', 'Women', 'Kids', 'Shoes'],
            'Home': ['Furniture', 'Decor', 'Kitchen'],
            'Sports': ['Gym', 'Running', 'Football'],
            'Beauty': ['Makeup', 'Skincare']
        }
        
        for parent_name, subs in cat_structure.items():
            parent_cat, _ = Category.objects.get_or_create(
                slug=slugify(parent_name), defaults={'name': parent_name, 'is_active': True}
            )
            categories.append(parent_cat)
            for sub in subs:
                # Parent is M2M, so we can't set it in defaults
                sub_cat, created = Category.objects.get_or_create(
                    slug=slugify(f"{parent_name}-{sub}"), 
                    defaults={'name': sub, 'is_active': True}
                )
                if created:
                    sub_cat.parent.add(parent_cat)
                categories.append(sub_cat)
            
        # Brands
        brands = []
        brand_names = ['Aurora', 'NexTech', 'UrbanStyle', 'GreenLive', 'ProActive', 'LuxeLine', 'Basics']
        for name in brand_names:
            brand, _ = Brand.objects.get_or_create(
                slug=slugify(name), defaults={'name': name, 'is_active': True}
            )
            brands.append(brand)

        self.stdout.write(f'Creating {count} products...')
        
        for i in range(count):
            name = fake.company() + ' ' + fake.word().capitalize()
            # Ensure unique name slightly
            name = f"{name} {random.randint(1, 9999)}"
            description = fake.text(max_nb_chars=500)
            category = random.choice(categories)
            brand = random.choice(brands)
            
            product = Product.objects.create(
                name=name,
                slug=slugify(name),
                category=category,
                brand=brand,
                unit=unit,
                selling_tax=tax,
                description=description,
                is_active=True,
                is_featured=random.choice([True, False, False]) # 1/3 chance
            )
            
            # Decide if simple or variable
            # Simple products have 1 variant with no specific attributes typically, or just base.
            # But the model allows attributes for any variant.
            # Let's say 50% are complex with multiple variants (Color/Size).
            
            is_complex = random.choice([True, False])
            
            if is_complex and category.name not in ['Electronics', 'Home']: # Clothing/Sports usually have sizes/colors
                # Create multiple variants based on Size/Color
                
                # Pick a random color and all sizes, or random size and all colors... or just random combos.
                # Let's do random pairs to avoid explosion.
                
                num_vars = random.randint(3, 8)
                seen_combos = set()
                
                for _ in range(num_vars):
                    v_color = random.choice(color_values)
                    v_size = random.choice(size_values)
                    
                    if (v_color.id, v_size.id) in seen_combos:
                        continue
                    seen_combos.add((v_color.id, v_size.id))
                    
                    price = Decimal(random.randint(20, 500))
                    sku = f"SKU-{slugify(product.name[:10])}-{v_color.value[:1]}-{v_size.value}-{random.randint(100,999)}".upper()
                    
                    variant = ProductVariant.objects.create(
                        product=product,
                        sku=sku,
                        price=price,
                        purchase_price=price * Decimal('0.6'),
                        weight=Decimal(random.randint(1, 5)),
                        is_active=True
                    )
                    variant.attributes.add(v_color, v_size)
                    
                    # Stock
                    for wh in warehouses:
                        Stock.objects.create(
                            product_variant=variant,
                            warehouse=wh,
                            quantity_on_hand=Decimal(random.randint(0, 50))
                        )
            else:
                # Single variant
                sku = f"SKU-{slugify(product.name[:10])}-{random.randint(1000,9999)}".upper()
                price = Decimal(random.randint(50, 2000))
                
                variant = ProductVariant.objects.create(
                    product=product,
                    sku=sku,
                    price=price,
                    purchase_price=price * Decimal('0.7'),
                    weight=Decimal(random.randint(1, 20)),
                    is_active=True
                )
                
                # Maybe add just one attribute like "Color: Black" if it's electronics
                if random.random() > 0.5:
                     v_color = random.choice(color_values)
                     variant.attributes.add(v_color)
                
                # Stock
                for wh in warehouses:
                    Stock.objects.create(
                        product_variant=variant,
                        warehouse=wh,
                        quantity_on_hand=Decimal(random.randint(0, 100))
                    )
                    
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} products with variants and stock.'))
