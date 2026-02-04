# API Audit Report - Customer-Facing Endpoints

**Date:** 2026-02-04  
**Base URL:** `/api/v1/`  
**Authentication:** Token-based (for cart, orders, addresses)

---

## 🟢 Public APIs (No Auth Required)

### Master Data APIs

#### 1. Brands
- **Endpoint:** `GET /api/v1/brands/`
- **Purpose:** List all active brands
- **Filters:** `is_active`, search by `name`
- **Usage:** Brand filter in product listing

#### 2. Categories
- **Endpoint:** `GET /api/v1/categories/`
- **Purpose:** List all categories (hierarchical)
- **Filters:** `is_active`, `is_featured`, `parent`
- **Usage:** Category navigation, filters

#### 3. Tags
- **Endpoint:** `GET /api/v1/tags/`
- **Purpose:** List all product tags
- **Usage:** Tag-based filtering

#### 4. Attributes
- **Endpoint:** `GET /api/v1/attributes/`
- **Purpose:** Product attributes (size, color, etc.)
- **Usage:** Product variant selection

#### 5. Payment Methods
- **Endpoint:** `GET /api/v1/paymentmethods/`
- **Purpose:** Available payment options
- **Usage:** Checkout payment selection

#### 6. Shipping Methods
- **Endpoint:** `GET /api/v1/shippingmethods/`
- **Purpose:** Available shipping options
- **Usage:** Checkout shipping selection

---

### Product APIs

#### 7. Products List
- **Endpoint:** `GET /api/v1/products/`
- **Purpose:** List all products with pagination
- **Filters:**
  - `is_active` - Active products only
  - `is_featured` - Featured products
  - `category` - Filter by category ID
  - `brand` - Filter by brand ID
  - `product_type` - Filter by type
  - `search` - Search by name, slug, description
- **Sorting:** `id`, `name`, `created_at`, `is_active`, `is_featured`
- **Response:** List serializer (basic info)
- **Usage:** Main product listing page

#### 8. Product Detail
- **Endpoint:** `GET /api/v1/products/{slug}/`
- **Purpose:** Get detailed product information
- **Query Params:** `attributes` - Comma-separated attribute IDs for variant selection
- **Response:** Detailed serializer with variants, images, specs
- **Usage:** Product detail page

#### 9. Popular Products
- **Endpoint:** `GET /api/v1/popular-products/`
- **Purpose:** List popular/bestselling products
- **Usage:** Homepage featured section

#### 10. New Arrivals
- **Endpoint:** `GET /api/v1/new-arrival-products/`
- **Purpose:** Latest 3 featured products
- **Usage:** Homepage new arrivals section

---

### CMS APIs

#### 11. Main Slider
- **Endpoint:** `GET /api/v1/public-main-slider/`
- **Purpose:** Homepage hero slider images
- **Usage:** Homepage carousel

#### 12. Mega Menu
- **Endpoint:** `GET /api/v1/mega-menu/`
- **Purpose:** Hierarchical navigation menu structure
- **Response:** Sections → Groups → Items
- **Usage:** Main navigation menu

---

## 🔐 Authenticated APIs (Token Required)

### Cart APIs

#### 13. Cart List
- **Endpoint:** `GET /api/v1/cart/`
- **Purpose:** Get current user's cart items
- **Auth:** Required
- **Usage:** Cart page, cart sidebar

#### 14. Add to Cart
- **Endpoint:** `POST /api/v1/cart/`
- **Body:** `{ "product_variant": <id>, "quantity": <num> }`
- **Auth:** Required
- **Usage:** Add product to cart

#### 15. Update Cart Item
- **Endpoint:** `PATCH /api/v1/cart/items/{id}/`
- **Body:** `{ "quantity": <num> }`
- **Auth:** Required
- **Usage:** Update item quantity

#### 16. Remove Cart Item
- **Endpoint:** `DELETE /api/v1/cart/items/{id}/`
- **Auth:** Required
- **Usage:** Remove item from cart

---

### Address APIs

#### 17. Address List
- **Endpoint:** `GET /api/v1/addresses/`
- **Purpose:** Get user's saved addresses
- **Auth:** Required
- **Usage:** Checkout, customer dashboard

#### 18. Create Address
- **Endpoint:** `POST /api/v1/addresses/`
- **Body:** Address fields
- **Auth:** Required
- **Usage:** Add new address

#### 19. Update Address
- **Endpoint:** `PUT/PATCH /api/v1/addresses/{id}/`
- **Auth:** Required
- **Usage:** Edit existing address

#### 20. Delete Address
- **Endpoint:** `DELETE /api/v1/addresses/{id}/`
- **Auth:** Required
- **Usage:** Remove address

---

### Order APIs

#### 21. Order List
- **Endpoint:** `GET /api/v1/orders/`
- **Purpose:** Get user's order history
- **Auth:** Required
- **Usage:** Customer dashboard order history

#### 22. Order Detail
- **Endpoint:** `GET /api/v1/orders/{id}/`
- **Purpose:** Get detailed order information
- **Auth:** Required
- **Usage:** Order detail page

#### 23. Create Order
- **Endpoint:** `POST /api/v1/orders/`
- **Body:** Order data (items, address, payment, shipping)
- **Auth:** Required
- **Usage:** Checkout completion

---

### User APIs

#### 24. User Registration
- **Endpoint:** `POST /api/v1/auth/register/`
- **Body:** User registration data
- **Usage:** Sign up page

#### 25. User Login
- **Endpoint:** `POST /api/v1/auth/login/`
- **Body:** `{ "username": "", "password": "" }`
- **Response:** `{ "token": "..." }`
- **Usage:** Login page

#### 26. User Profile
- **Endpoint:** `GET /api/v1/auth/profile/`
- **Auth:** Required
- **Usage:** Customer dashboard profile

#### 27. Update Profile
- **Endpoint:** `PUT/PATCH /api/v1/auth/profile/`
- **Auth:** Required
- **Usage:** Profile settings

---

## 📋 API Integration Patterns

### Authentication
```javascript
// Store token after login
localStorage.setItem('authToken', response.token);

// Include in requests
headers: {
    'Authorization': `Token ${localStorage.getItem('authToken')}`,
    'Content-Type': 'application/json'
}
```

### Error Handling
```javascript
try {
    const response = await fetch(url, options);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    return data;
} catch (error) {
    console.error('API Error:', error);
    showErrorMessage('Something went wrong. Please try again.');
}
```

### Pagination
```javascript
// APIs return paginated results
{
    "count": 100,
    "next": "/api/v1/products/?page=2",
    "previous": null,
    "results": [...]
}
```

### Filtering & Search
```javascript
// Build query string
const params = new URLSearchParams({
    category: categoryId,
    brand: brandId,
    search: searchTerm,
    ordering: '-created_at'
});
const url = `/api/v1/products/?${params}`;
```

---

## ✅ API Status Summary

| Category | Endpoints | Status | Notes |
|----------|-----------|--------|-------|
| Master Data | 6 | ✅ Ready | Brands, categories, attributes, etc. |
| Products | 4 | ✅ Ready | List, detail, popular, new arrivals |
| CMS | 2 | ✅ Ready | Slider, mega menu |
| Cart | 4 | ✅ Ready | CRUD operations |
| Addresses | 4 | ✅ Ready | CRUD operations |
| Orders | 3 | ✅ Ready | List, detail, create |
| User Auth | 4 | ✅ Ready | Register, login, profile |

**Total:** 27 endpoints ready for frontend integration

---

## 🎯 Frontend Implementation Priority

1. **Phase 1:** Product listing with filters/search
2. **Phase 2:** Product detail with add to cart
3. **Phase 3:** Cart management
4. **Phase 4:** Checkout process
5. **Phase 5:** Customer dashboard

All APIs are production-ready and follow REST best practices! 🚀
