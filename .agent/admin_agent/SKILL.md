---
name: admin-security-skill
description: Security-first skill to manage and protect admin operations.
---

# Admin Security & Management Skill
You are responsible for ensuring that all management views and API endpoints are strictly inaccessible to regular customers.

## Security Directives:
- **Permission Enforcement:** Every view in the admin app must be decorated with `@staff_member_required` or inherit from `StaffUserRequiredMixin`.
- **Proxy Logic:** Use the `Admin` Proxy model to filter user-related data. 
- **Data Integrity:** Ensure that site settings (Site Info, Attributes, Categories) can only be modified via POST requests by authenticated staff.
- **CSRF Protection:** All AJAX actions performed in the admin panel must validate the CSRF token.

## UI Directive:
- Maintain a consistent "Management Dashboard" look using Bootstrap, distinct from the customer storefront.