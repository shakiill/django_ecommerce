---
name: frontend-storefront-skill
description: Build modern, AJAX-powered storefront and customer dashboard for e-commerce
---

# Frontend Storefront & Customer Dashboard Skill

You are responsible for building a beautiful, modern, and highly interactive customer-facing storefront and dashboard.

## Design Directives:
- **Modern UI/UX:** Use contemporary design patterns with smooth animations and transitions
- **AJAX-Powered:** All filtering, searching, and cart operations must use AJAX (no page reloads)
- **Responsive Design:** Mobile-first approach, works perfectly on all devices
- **Performance:** Lazy loading, caching, and optimized API calls
- **User Experience:** Intuitive navigation, clear CTAs, instant feedback

## Technical Requirements:
- **Vanilla JavaScript:** Use modern ES6+ JavaScript (no jQuery unless absolutely necessary)
- **CSS Framework:** Use Bootstrap 5 for responsive grid and components
- **API Integration:** Consume REST APIs from `/api/v1/` endpoints
- **State Management:** Maintain cart state, filters, and user preferences
- **Error Handling:** Graceful error messages and fallbacks

## Storefront Components:
1. **Homepage:** Hero slider, featured products, new arrivals, categories
2. **Product Listing:** Grid/list view, filters (brand, category, price), search, sorting, pagination
3. **Product Detail:** Image gallery, variant selection, add to cart, related products
4. **Shopping Cart:** AJAX add/remove, quantity updates, real-time total calculation
5. **Checkout:** Multi-step process, address management, payment/shipping selection
6. **Customer Dashboard:** Order history, addresses, profile management

## AJAX Patterns:
- Use `fetch()` API for all HTTP requests
- Show loading indicators during API calls
- Update UI without page refresh
- Handle errors gracefully with user-friendly messages
- Implement debouncing for search inputs

## UI/UX Standards:
- Clean, modern design with consistent color scheme
- Smooth transitions and micro-animations
- Clear visual hierarchy
- Accessible (ARIA labels, keyboard navigation)
- Fast loading times (< 3s initial load)
