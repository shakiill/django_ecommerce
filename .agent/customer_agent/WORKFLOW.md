---
name: build-frontend-journey
description: Step-by-step UI construction and API binding.
---

# Frontend Development Workflow

## Step 1: API Audit & Mapping
- Scan `views.py` and `urls.py` to identify endpoints for Products, Categories, and Cart.
- Create a JS utility file (`api.js`) to centralize all AJAX fetch calls.

## Step 2: Public Storefront Construction
- **Home Page:** Featured categories and latest products.
- **Shop Page:** Implement a Sidebar with AJAX filters (Category, Price Range) and a real-time Search bar.
- **Product Details:** Dynamic attribute selection (Color/Size) that updates price/stock via API.

## Step 3: Shopping Experience
- **Cart Page:** AJAX-based quantity updates and "Remove Item" logic.
- **Checkout Page:** Multi-step form integrated with SSL Commerz and Pay Station APIs.

## Step 4: Separate Customer Dashboard
- Create a unique set of templates in `/templates/customer_dashboard/`.
- Repurpose the existing Admin logic but apply a "Customer-facing" CSS theme.
- Features: Order History, Profile Edit, and Track My Order.