Ecommerce website and ERP
---
1. Clone Project from github
2. Create virtualenv
      ```sh
    $ virtualenv venv
    ```
3. Activate Virtualenv
   ```sh
    $ source venv/Scripts/activate
    ```
4. Install Requirements
   ```sh
    $ pip install -r requirements.txt
    ```

5. Add project specific information in .env
6. Make migration
    ```sh
    $ python manage.py makemigrations
    ```
7. Migrate
    ```sh
    $ python manage.py migrate
    ```
8. Create Superuser
    ```sh
    $ python manage.py createsuperuser
    ```
9. Start Server
    ```sh
    $ python manage.py runserver
    ```

10. Run Celery for the background tasks
    ```sh
    $ celery -A real_estate_erp worker -l info -P threads  
    $ celery -A real_estate_erp beat -l info

    $ stripe listen --forward-to http://localhost:8000/api/v1/webhooks/stripe/
    ```

11. Stripe Webhook CLI Commands
    ```sh
    $ stripe login

    $ stripe listen --forward-to http://localhost:8000/api/v1/webhooks/stripe/
    ```

# Ecommerce Admin

## Mega Menu API

A read-only mega menu endpoint is available at `/api/mega-menu/` returning a nested JSON structure keyed by top-level section slugs.

Example response snippet:

```
{
  "women": {
    "trending": [
      { "name": "New Arrivals", "href": "/collections/new-arrivals" },
      { "name": "Best Sellers", "href": "/category/women-bestsellers" },
      { "name": "Cosy Luxe X Soft Sculpt", "href": "/collections/cosy-luxe", "badge": "🔥" }
    ],
    "featured": [
      { "title": "COSY LUXE", "image": null, "href": "/collections/cosy-luxe" }
    ]
  }
}
```

### Models
- `MenuSection` - top level categories (women, men, accessories)
- `MenuGroup` - groups inside a section (trending, products, featured). `is_featured=True` changes item schema.
- `MenuItem` - individual links; featured items can have `title`, optional `image`.

All models include `order` and `is_active` fields for sorting and visibility. Cache invalidates automatically on create/update/delete.

### Caching
The endpoint is cached under key `public:mega_menu` respecting `PUBLIC_API_CACHE_TIMEOUT` and `PUBLIC_API_CACHE_ENABLED` settings.

### Seeding Sample Data
Run the management command to seed sample mega menu data:

```
python manage.py seed_mega_menu --flush
```

Optionally provide a JSON file path:

```
python manage.py seed_mega_menu --file path/to/mega_menu.json --flush
```

### Frontend Integration
Use the endpoint data directly to construct a mega menu. Featured groups provide objects with `title`, `image`, `href`; other groups provide `name`, `href` plus optional `badge` and `style` keys.

### Tests
Automated tests in `apps/cms/tests.py` cover structure, caching, and inactive filtering.
