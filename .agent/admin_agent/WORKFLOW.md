---
name: secure-admin-workflow
description: Audit and protect existing admin actions.
---

# Admin Protection Workflow

## Step 1: Permission Audit
- Scan all views in the `admin` or `management` apps.
- Apply `@staff_member_required` to any function missing protection.
- Ensure the `login_url` redirects unauthorized users to the admin login page.

## Step 2: Attribute & Category Lockdown
- Verify that `Attribute`, `Category`, and `Product` CRUD operations are restricted.
- Implement "Staff-Only" validation in the `save()` methods of these models.

## Step 3: Order Management Security
- Ensure only staff can trigger "Order Status Updates" (e.g., changing 'Pending' to 'Shipped').
- Log all status changes for audit purposes (who changed what and when).

## Step 4: Settings Verification
- Protect the Site-Settings singleton.
- Ensure only superusers or specific staff can modify core financial settings (SSL Commerz/Pay Station keys).