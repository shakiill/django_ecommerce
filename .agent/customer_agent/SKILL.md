---
name: frontend-ui-ux-skill
description: Expert in AJAX-driven Django frontends, Bootstrap 5, and API integration.
---

# Frontend & API Integration Skill
You are responsible for the public storefront and the private Customer Dashboard.

## Technical Directives:
- **API First:** Audit all existing Django ViewSets/APIs. Use `Fetch API` for dynamic data loading.
- **State Management:** Use AJAX for "Add to Cart," "Filter Products," and "Search" to prevent page reloads.
- **Authentication:** For public pages (Home/Products), ensure data is fetched via public APIs. For the Customer Dashboard, use the existing Django Auth system but redirected to a separate UI.
- **Styling:** Use Bootstrap 5. Implement a "Skeleton Loader" effect while AJAX data is fetching.