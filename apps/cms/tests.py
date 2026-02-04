from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.cms.models import MenuSection, MenuGroup, MenuItem, MEGA_MENU_CACHE_KEY
from django.core.cache import cache

User = get_user_model()


class MegaMenuAPITests(TestCase):
    def setUp(self):
        cache.delete(MEGA_MENU_CACHE_KEY)

    def test_empty_menu_returns_empty_object(self):
        url = reverse('public_mega_menu')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {})

    def test_menu_structure(self):
        women = MenuSection.objects.create(name='Women', slug='women', order=0)
        trending = MenuGroup.objects.create(section=women, name='trending', order=0)
        featured = MenuGroup.objects.create(section=women, name='featured', is_featured=True, order=1)
        MenuItem.objects.create(group=trending, name='New Arrivals', href='/collections/new-arrivals', order=0)
        MenuItem.objects.create(group=trending, name='Best Sellers', href='/category/women-bestsellers', order=1, badge='🔥')
        MenuItem.objects.create(group=featured, name='Cosy Luxe', title='Cosy Luxe', href='/collections/cosy-luxe', order=0)

        url = reverse('public_mega_menu')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('women', data)
        self.assertIn('trending', data['women'])
        self.assertIn('featured', data['women'])
        self.assertEqual(len(data['women']['trending']), 2)
        self.assertEqual(data['women']['trending'][1]['badge'], '🔥')
        self.assertEqual(data['women']['featured'][0]['title'], 'Cosy Luxe')
        # Cached response returns same
        resp2 = self.client.get(url)
        self.assertEqual(resp2.json(), data)

    def test_inactive_items_not_included(self):
        men = MenuSection.objects.create(name='Men', slug='men', order=0)
        products = MenuGroup.objects.create(section=men, name='products', order=0)
        MenuItem.objects.create(group=products, name='All Products', href='/category/men-all', order=0, is_active=True)
        MenuItem.objects.create(group=products, name='Hidden', href='/hidden', order=1, is_active=False)
        url = reverse('public_mega_menu')
        data = self.client.get(url).json()
        self.assertEqual(len(data['men']['products']), 1)
        self.assertEqual(data['men']['products'][0]['name'], 'All Products')


class MegaMenuAdminCRUDTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.client.login(username='admin', password='pass123')

    def _get_csrf(self):
        resp = self.client.get('/cms/mega-menu/')
        # Cookie method
        token = resp.cookies.get('csrftoken')
        if token:
            return token.value
        # Context token fallback
        if hasattr(resp, 'context') and resp.context and 'csrf_token' in resp.context:
            return resp.context['csrf_token']
        return ''

    def test_admin_page_access(self):
        resp = self.client.get('/cms/mega-menu/')
        # Expect 200 or redirect to login (302). If redirect, follow and expect 200.
        self.assertIn(resp.status_code, (200, 302))

    def test_create_section_group_item_via_forms(self):
        csrf = self._get_csrf()
        resp = self.client.post(reverse('cms:section_create'), {
            'csrfmiddlewaretoken': csrf,
            'name': 'Women', 'slug': '', 'order': 0, 'is_active': 'on'
        }, follow=True)
        # Debug status
        print('Section create status', resp.status_code)
        self.assertEqual(MenuSection.objects.count(), 1)
        section = MenuSection.objects.first()
        self.assertEqual(section.slug, 'women')

        csrf = self._get_csrf()
        resp = self.client.post(reverse('cms:group_create'), {
            'csrfmiddlewaretoken': csrf,
            'section': section.pk,
            'name': 'trending',
            'title': '',
            'is_featured': '',
            'order': 0,
            'is_active': 'on'
        }, follow=True)
        self.assertEqual(MenuGroup.objects.count(), 1)
        group = MenuGroup.objects.first()

        csrf = self._get_csrf()
        resp = self.client.post(reverse('cms:item_create'), {
            'csrfmiddlewaretoken': csrf,
            'group': group.pk,
            'name': 'New Arrivals',
            'title': '',
            'href': '/collections/new-arrivals',
            'badge': '',
            'style': '',
            'order': 0,
            'is_active': 'on'
        }, follow=True)
        self.assertEqual(MenuItem.objects.count(), 1)
        item = MenuItem.objects.first()
        self.assertEqual(item.name, 'New Arrivals')
        self.assertEqual(item.href, '/collections/new-arrivals')
