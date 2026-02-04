# 🔒 Admin Security - Developer Quick Reference

## When to Use Staff Protection

**ALWAYS use `@staff_member_required` for:**
- Product/Category/Brand management
- Supplier/Warehouse management
- Order management and status updates
- Site settings and configuration
- Inventory and procurement
- Reports and analytics
- Any CRUD operations on master data

**NEVER use just `@login_required` for admin functions!**

---

## Function-Based Views

### ✅ Correct
```python
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required(login_url='staff_login')
def my_admin_view(request):
    # Your admin logic here
    return render(request, 'admin/template.html', context)
```

### ❌ Incorrect
```python
from django.contrib.auth.decorators import login_required

@login_required  # ❌ Not enough! Customers can access!
def my_admin_view(request):
    return render(request, 'admin/template.html', context)
```

---

## Class-Based Views

### ✅ Correct
```python
from apps.helpers.mixins import StaffUserRequiredMixin
from django.views.generic import ListView

class MyAdminView(StaffUserRequiredMixin, ListView):
    model = MyModel
    template_name = 'admin/list.html'
```

### ❌ Incorrect
```python
from django.contrib.auth.mixins import LoginRequiredMixin

class MyAdminView(LoginRequiredMixin, ListView):  # ❌ Not enough!
    model = MyModel
    template_name = 'admin/list.html'
```

---

## API Endpoints

### For Admin-Only APIs
```python
@staff_member_required(login_url='staff_login')
@require_GET
def api_admin_data(request):
    data = {'items': [...]}
    return JsonResponse(data)
```

### For Public APIs (Read-Only)
```python
from rest_framework.permissions import AllowAny

class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    http_method_names = ['get']  # Read-only!
```

---

## Common Patterns

### CRUD Operations
```python
@staff_member_required(login_url='staff_login')
def create_item(request):
    # Create logic
    pass

@staff_member_required(login_url='staff_login')
def edit_item(request, pk):
    # Edit logic
    pass

@staff_member_required(login_url='staff_login')
@require_POST
def delete_item(request, pk):
    # Delete logic
    pass
```

### AJAX Endpoints
```python
@staff_member_required(login_url='staff_login')
def ajax_update_status(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # AJAX logic
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)
```

---

## Testing Your Security

### Manual Testing
1. **Log out completely**
2. **Try to access admin URL directly**
3. **Expected:** Redirect to `/staff/login/`
4. **Log in as regular customer**
5. **Try to access admin URL**
6. **Expected:** 403 Forbidden or redirect
7. **Log in as staff member**
8. **Expected:** Full access granted

### Unit Testing
```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

class AdminSecurityTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.customer = User.objects.create_user(
            username='customer',
            password='test123',
            is_staff=False
        )
        self.staff = User.objects.create_user(
            username='staff',
            password='test123',
            is_staff=True
        )
        self.client = Client()
    
    def test_customer_cannot_access_admin(self):
        self.client.login(username='customer', password='test123')
        response = self.client.get('/master/brands/')
        self.assertEqual(response.status_code, 403)
    
    def test_staff_can_access_admin(self):
        self.client.login(username='staff', password='test123')
        response = self.client.get('/master/brands/')
        self.assertEqual(response.status_code, 200)
```

---

## Checklist for New Admin Views

- [ ] Import `@staff_member_required` decorator
- [ ] Add decorator to view function
- [ ] Set `login_url='staff_login'`
- [ ] Test with non-staff user
- [ ] Test with staff user
- [ ] Verify CSRF protection on forms
- [ ] Add to URL patterns correctly

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using @login_required
```python
@login_required  # Wrong! Customers can access!
def admin_view(request):
    pass
```

### ✅ Fix
```python
@staff_member_required(login_url='staff_login')
def admin_view(request):
    pass
```

---

### ❌ Mistake 2: Forgetting login_url
```python
@staff_member_required  # Will redirect to default /admin/login/
def admin_view(request):
    pass
```

### ✅ Fix
```python
@staff_member_required(login_url='staff_login')  # Correct!
def admin_view(request):
    pass
```

---

### ❌ Mistake 3: No protection at all
```python
def admin_view(request):  # Anyone can access!
    pass
```

### ✅ Fix
```python
@staff_member_required(login_url='staff_login')
def admin_view(request):
    pass
```

---

## Quick Reference Card

| Scenario | Decorator/Mixin | Example |
|----------|----------------|---------|
| Admin function view | `@staff_member_required(login_url='staff_login')` | Product CRUD |
| Admin class view | `StaffUserRequiredMixin` | Dashboard |
| Public API (read) | `AllowAny` + `http_method_names=['get']` | Product list |
| Admin API | `@staff_member_required` | Internal APIs |

---

## Need Help?

1. Check `.agent/admin_agent/SKILL.md` for security directives
2. Review `.agent/admin_agent/SECURITY_AUDIT.md` for examples
3. See `.agent/admin_agent/BEFORE_AFTER.md` for comparisons

---

**Remember:** When in doubt, use `@staff_member_required`! It's better to be too restrictive than too permissive.
