# Cart & Order API (Frontend Guide)

Public URL: https://ecom.shezan.me/api/v1/docs/

This document explains how to use the cart and order endpoints for BOTH logged-in users and guests.

## 0. Glossary (Simple)
- Guest Token: Random string (UUID) you generate on the frontend for anonymous visitors. Acts like a temporary user id.
- Variant: A purchasable SKU (size/color etc.).
- Cart Item: One variant + quantity inside the cart.
- Coupon: Discount code applied to the cart or captured at order time.
- Order: Final snapshot created from the cart during checkout.

--- 

## 0.1 Headers Quick Reference
- As guest: 
  - X-Guest-Token: <your-uuid>
  - Content-Type: application/json (for POST/PUT/PATCH)
- As user:
  - Authorization: Bearer <jwt>
  - Content-Type: application/json (for POST/PUT/PATCH)

---

## 1. Ownership Rules
Choose ONE path per request:
- Authenticated user: send normal auth (e.g. Authorization header). DO NOT send X-Guest-Token.
- Guest: send header X-Guest-Token: <token> OR ?guest_token=<token> in URL.

If neither provided => 400 error.
If both provided => user path wins (guest token ignored).

---

## 2. Quick Start (Guest Flow)
1. Generate a guest token when the session starts (e.g. localStorage.setItem('guest_token', uuidv4())).
2. Use that token for all cart calls (header X-Guest-Token).
3. When the user logs in, call POST /cart/merge/ with the old guest token to keep their items.
4. After checkout, the cart becomes empty (order consumes items).

---

## 3. Cart Endpoints

Base URL segment: /cart/

Always GET the cart after mutations to refresh subtotal, discount, and totals.

### 3.1 Get Cart
GET /cart/
Headers (guest): X-Guest-Token: abcd-1234
+Request:
+- Headers:
+  - X-Guest-Token: abcd-1234
+  - Accept: application/json
+  - (no body)
 Response 200:
 {
   "items": [
     {
       "id": 11,
       "variant_id": 55,
       "sku": "TSHIRT-RED-M",
       "product_name": "T-Shirt Red M",
       "quantity": 2,
       "unit_price": "19.99",
       "line_total": "39.98"
     }
   ],
   "subtotal": "39.98",
   "discount": "0.00",
   "shipping": "0.00",
   "tax": "0.00",
   "total": "39.98",
   "coupon": ""
 }
 
 curl example (guest):
 curl -H "X-Guest-Token: abcd-1234" http://localhost:8000/api/v1/cart/

### 3.2 Add / Increment Item
POST /cart/
Body:
{ "variant_id": 55, "quantity": 2 }

Rules:
- If the variant already exists in cart -> quantity is increased.
- quantity must be >= 1 and respect product min/max + stock.
+Request:
+{
+  "variant_id": 55,
+  "quantity": 2
+}
+Response 201:
+{
+  "items": [
+    {
+      "id": 11,
+      "variant_id": 55,
+      "sku": "TSHIRT-RED-M",
+      "product_name": "T-Shirt Red M",
+      "quantity": 2,
+      "unit_price": "19.99",
+      "line_total": "39.98"
+    }
+  ],
+  "subtotal": "39.98",
+  "discount": "0.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "39.98",
+  "coupon": ""
+}

curl:
curl -X POST -H "Content-Type: application/json" -H "X-Guest-Token: abcd-1234" -d '{"variant_id":55,"quantity":2}' http://localhost:8000/api/v1/cart/

### 3.3 Update Item Quantity
PATCH /cart/items/{cart_item_id}/
Body:
{ "quantity": 5 }
+Request (PATCH):
+{
+  "quantity": 5
+}
+Response 200:
+{
+  "items": [
+    {
+      "id": 11,
+      "variant_id": 55,
+      "sku": "TSHIRT-RED-M",
+      "product_name": "T-Shirt Red M",
+      "quantity": 5,
+      "unit_price": "19.99",
+      "line_total": "99.95"
+    }
+  ],
+  "subtotal": "99.95",
+  "discount": "0.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "99.95",
+  "coupon": ""
+}

curl:
curl -X PATCH -H "Content-Type: application/json" -H "X-Guest-Token: abcd-1234" -d '{"quantity":5}' http://localhost:8000/api/v1/cart/items/11/

### 3.4 Delete Item
DELETE /cart/items/{cart_item_id}/
Removes the item. Returns updated summary.
+Response 200:
+{
+  "items": [],
+  "subtotal": "0.00",
+  "discount": "0.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "0.00",
+  "coupon": ""
+}

curl:
curl -X DELETE -H "X-Guest-Token: abcd-1234" http://localhost:8000/api/v1/cart/items/11/

### 3.5 Apply Coupon
POST /cart/apply-coupon/
Body:
{ "code": "SAVE5" }

If valid -> discount recalculated.
Error 400 if invalid:
{ "detail": "Invalid or ineligible coupon." }
+Request:
+{ "code": "SAVE5" }
+Response 200 (valid):
+{
+  "items": [
+    { "id": 11, "variant_id": 55, "sku": "TSHIRT-RED-M", "product_name": "T-Shirt Red M", "quantity": 2, "unit_price": "19.99", "line_total": "39.98" }
+  ],
+  "subtotal": "39.98",
+  "discount": "5.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "34.98",
+  "coupon": "SAVE5"
+}

curl:
curl -X POST -H "Content-Type: application/json" -H "X-Guest-Token: abcd-1234" -d '{"code":"SAVE5"}' http://localhost:8000/api/v1/cart/apply-coupon/

### 3.6 Remove Coupon
POST /cart/remove-coupon/
Removes any applied coupon.
+Request: (no body)
+Response 200:
+{
+  "items": [
+    { "id": 11, "variant_id": 55, "sku": "TSHIRT-RED-M", "product_name": "T-Shirt Red M", "quantity": 2, "unit_price": "19.99", "line_total": "39.98" }
+  ],
+  "subtotal": "39.98",
+  "discount": "0.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "39.98",
+  "coupon": ""
+}

curl:
curl -X POST -H "X-Guest-Token: abcd-1234" http://localhost:8000/api/v1/cart/remove-coupon/

### 3.7 Clear Cart
POST /cart/clear/
Removes all items and coupon.
+Request: (no body)
+Response 200:
+{
+  "items": [],
+  "subtotal": "0.00",
+  "discount": "0.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "0.00",
+  "coupon": ""
+}

curl:
curl -X POST -H "X-Guest-Token: abcd-1234" http://localhost:8000/api/v1/cart/clear/

### 3.8 Merge Guest Cart (After Login)
POST /cart/merge/
Requires authenticated user.
Body:
{ "guest_token": "abcd-1234" }

Moves items + coupon (if valid) into the user's cart.
+Request:
+{ "guest_token": "abcd-1234" }
+Response 200:
+{
+  "items": [
+    { "id": 21, "variant_id": 55, "sku": "TSHIRT-RED-M", "product_name": "T-Shirt Red M", "quantity": 3, "unit_price": "19.99", "line_total": "59.97" }
+  ],
+  "subtotal": "59.97",
+  "discount": "5.00",
+  "shipping": "0.00",
+  "tax": "0.00",
+  "total": "54.97",
+  "coupon": "SAVE5"
+}

curl (user):
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"guest_token":"abcd-1234"}' http://localhost:8000/api/v1/cart/merge/

---

## 4. Order Endpoints

Base URL segment: /orders/

### 4.1 List Orders
GET /orders/
User: returns all of their orders.
Guest: returns orders created with the guest_token.
+Response 200:
+[
+  {
+    "id": 9,
+    "order_number": "ORD-AB12CD34EF56",
+    "status": "pending",
+    "payment_status": "unpaid",
+    "currency": "USD",
+    "subtotal_amount": "59.97",
+    "discount_amount": "5.00",
+    "shipping_amount": "0.00",
+    "tax_amount": "0.00",
+    "total_amount": "54.97",
+    "coupon_code": "SAVE5",
+    "created_at": "2025-01-10T12:34:56Z",
+    "items": [
+      { "product_name": "T-Shirt Red M", "sku": "TSHIRT-RED-M", "unit_price": "19.99", "quantity": 3, "line_total": "59.97" }
+    ],
+    "shipping_address": { "id": 44, "full_name": "John Doe", "email": "john@example.com", "phone": "+12025550123", "line1": "123 Main St", "line2": "", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US" },
+    "billing_address": { "id": 44, "full_name": "John Doe", "email": "john@example.com", "phone": "+12025550123", "line1": "123 Main St", "line2": "", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US" }
+  }
+]

curl (guest):
curl -H "X-Guest-Token: abcd-1234" http://localhost:8000/api/v1/orders/

### 4.2 Retrieve Order
GET /orders/{id}/
+Response 200:
+{
+  "id": 9,
+  "order_number": "ORD-AB12CD34EF56",
+  "status": "pending",
+  "payment_status": "unpaid",
+  "currency": "USD",
+  "subtotal_amount": "59.97",
+  "discount_amount": "5.00",
+  "shipping_amount": "0.00",
+  "tax_amount": "0.00",
+  "total_amount": "54.97",
+  "coupon_code": "SAVE5",
+  "created_at": "2025-01-10T12:34:56Z",
+  "items": [
+    { "product_name": "T-Shirt Red M", "sku": "TSHIRT-RED-M", "unit_price": "19.99", "quantity": 3, "line_total": "59.97" }
+  ],
+  "shipping_address": { "id": 44, "full_name": "John Doe", "email": "john@example.com", "phone": "+12025550123", "line1": "123 Main St", "line2": "", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US" },
+  "billing_address": { "id": 44, "full_name": "John Doe", "email": "john@example.com", "phone": "+12025550123", "line1": "123 Main St", "line2": "", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US" }
+}

curl:
curl -H "X-Guest-Token: abcd-1234" http://localhost:8000/api/v1/orders/7/

### 4.3 Create Order (Checkout)
POST /orders/
Body (guest example):
{
  "guest_email": "guest@example.com",
  "shipping_address": {
    "full_name": "John Guest",
    "email": "guest@example.com",
    "phone": "+12025550123",
    "line1": "123 Main St",
    "line2": "",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  "use_shipping_as_billing": true
}

Authenticated user using a previous guest cart WITHOUT merging:
Send source_guest_token (the old guest token) in the body. This consumes that guest cart directly.
Body (user example):
{
  "source_guest_token": "abcd-1234",
  "shipping_address": {
    "full_name": "John Guest",
    "email": "guest@example.com",
    "phone": "+12025550123",
    "line1": "123 Main St",
    "line2": "",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  },
  "use_shipping_as_billing": true
}

Authenticated user (use existing saved address IDs):
Body (using IDs):
{
  "shipping_address_id": 12,
  "billing_address_id": 18,
  "use_shipping_as_billing": false
}

Authenticated user (new addresses inline):
{
  "shipping_address": { ...full fields... },
  "use_shipping_as_billing": true
}

Guest (must send full object):
{
  "guest_email": "guest@example.com",
  "shipping_address": { ...full fields... },
  "use_shipping_as_billing": true
}
+Response 201 (full):
+{
+  "id": 9,
+  "order_number": "ORD-AB12CD34EF56",
+  "status": "pending",
+  "payment_status": "unpaid",
+  "currency": "USD",
+  "subtotal_amount": "39.98",
+  "discount_amount": "5.00",
+  "shipping_amount": "0.00",
+  "tax_amount": "0.00",
+  "total_amount": "34.98",
+  "coupon_code": "SAVE5",
+  "created_at": "2025-01-10T12:34:56Z",
+  "items": [
+    { "product_name": "T-Shirt Red M", "sku": "TSHIRT-RED-M", "unit_price": "19.99", "quantity": 2, "line_total": "39.98" }
+  ],
+  "shipping_address": {
+    "id": 44, "full_name": "John Guest", "email": "guest@example.com", "phone": "+12025550123",
+    "line1": "123 Main St", "line2": "", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US"
+  },
+  "billing_address": {
+    "id": 44, "full_name": "John Guest", "email": "guest@example.com", "phone": "+12025550123",
+    "line1": "123 Main St", "line2": "", "city": "New York", "state": "NY", "postal_code": "10001", "country": "US"
+  }
+}

Rules:
- Guest: shipping_address object + guest_email required.
- User: provide either shipping_address_id OR shipping_address object.
- For different billing:
  - Provide billing_address_id OR billing_address object AND set use_shipping_as_billing=false.

Errors:
{ "shipping_address": "Provide shipping_address_id or shipping_address object." } -> user forgot both.
{ "shipping_address_id": "Address not found or not owned by user." } -> invalid id.
{ "billing_address_id": "Billing address not found or not owned by user." } -> invalid id.

curl (user with existing address IDs):
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"shipping_address_id":12,"billing_address_id":18,"use_shipping_as_billing":false}' \
  http://localhost:8000/api/v1/orders/

curl (user with new inline shipping address):
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"shipping_address":{"full_name":"John Doe","email":"john@example.com","phone":"+12025550123","line1":"123 Main St","line2":"","city":"New York","state":"NY","postal_code":"10001","country":"US"},"use_shipping_as_billing":true}' \
  http://localhost:8000/api/v1/orders/

curl (guest):
curl -X POST -H "X-Guest-Token: abcd-1234" -H "Content-Type: application/json" \
  -d '{"guest_email":"guest@example.com","shipping_address":{"full_name":"John Guest","email":"guest@example.com","phone":"+12025550123","line1":"123 Main St","line2":"","city":"New York","state":"NY","postal_code":"10001","country":"US"},"use_shipping_as_billing":true}' \
  http://localhost:8000/api/v1/orders/

Successful Response 201 (additional field semantics unchanged):
{
  "id": 9,
  "order_number": "ORD-AB12CD34EF56",
  "status": "pending",
  "payment_status": "unpaid",
  "subtotal_amount": "39.98",
  "discount_amount": "5.00",
  "shipping_amount": "0.00",
  "tax_amount": "0.00",
  "total_amount": "34.98",
  "coupon_code": "SAVE5",
  "items": [ ... ],
  "shipping_address": { ... },
  "billing_address": { ... }
}

---

## 5. Typical Flow (Guest -> Order)
1. Generate guest token and store locally.
2. Add items (POST /cart/).
3. Show cart summary (GET /cart/).
4. (Optional) Apply coupon (POST /cart/apply-coupon/).
5. Collect address form.
6. POST /orders/ to create order.
7. Empty cart UI (GET /cart/ again).
8. Redirect to order confirmation page using returned order_number.

Login transition:
- User logs in.
- POST /cart/merge/ with old guest token.
- Continue checkout as authenticated user.

---

## 6. Common Errors & Fixes
Error: { "detail": "guest_token header or query param is required for guest cart." }
Fix: Send X-Guest-Token header.

Error: { "detail": "Invalid or ineligible coupon." }
Fix: Check spelling, active dates, subtotal >= min_subtotal.

Error: { "guest_email": "guest_email is required for guest checkout." }
Fix: Include guest_email when NOT authenticated.

Error: "Minimum order quantity is X."
Fix: Increase quantity to at least product.min_order_quantity.

Error: "Maximum order quantity is X."
Fix: Decrease quantity to product.max_order_quantity.

Error: "Requested quantity exceeds available stock."
Fix: Reduce quantity (stock limit) or remove item.

Error: "Cart is empty."
Fix: Ensure at least one item added before checkout.

---

## 7. Frontend Implementation Tips
- Always re-fetch cart after any modification (add/update/delete/apply/remove).
- Store coupon code in state after successful apply; show discount line.
- Disable checkout button if cart.items.length === 0.
- On order success, clear local cart state and navigate to confirmation.
- Keep guest token stable across page reloads (localStorage).

---

## 8. Payment (Future)
The order comes back with payment_status = unpaid.
A separate payment endpoint (not yet documented) will mark it paid and update payment_status to paid.

---

## 9. Minimal Data Contracts (Keys You Render)
Cart Item: { id, product_name, sku, quantity, unit_price, line_total }
Cart Summary: { subtotal, discount, total, coupon }
Order: { order_number, status, total_amount, items[], shipping_address, billing_address }

---

## 10. Security Notes
- Do NOT allow users to edit unit_price or line_total client-side; they are computed server-side.
- Guest token should not expose user identity—random UUID is enough.

---

## Owner Helper Properties (Backend Convenience)
You do not need an extra "type" field. Backend exposes:
- Cart.is_guest / Order.is_guest -> boolean
- Cart.owner_type / Order.owner_type -> "guest" or "user"
- Cart.owner_email -> user email or null (guests have no stored email at cart stage)
- Order.owner_email -> user email or guest_email
- Cart.owner_identifier / Order.owner_identifier -> user id (string) or guest_token
Use these when you need a simple flag without checking user vs guest_token.

---

## 11. FAQ: Do I need to merge carts?

Short answer:
- No, if you will checkout guest cart directly after login using source_guest_token.
- No, if the user was always logged in (just normal checkout).
- Yes, only if you prefer to consolidate guest items into the user cart before browsing more.

Two options after login:
1. POST /cart/merge/ then checkout normally (no source_guest_token).
2. Skip merge and send source_guest_token in order create.

Choose ONE; do not both merge and use source_guest_token.

---

## 12. Address API (Authenticated Users Only)

Purpose: Store reusable shipping/billing addresses for logged-in users. Guests send address inside order body and cannot store addresses.

### 12.1 List Addresses
GET /addresses/
Headers: Authorization: Bearer <token>
Response 200:
[
  {
    "id": 4,
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+12025550123",
    "line1": "123 Main St",
    "line2": "",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  }
]

curl:
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/addresses/

### 12.2 Retrieve One
GET /addresses/{id}/
404 if not owned by user.
+Response 200:
+{
+  "id": 4,
+  "full_name": "John Doe",
+  "email": "john@example.com",
+  "phone": "+12025550123",
+  "line1": "123 Main St",
+  "line2": "",
+  "city": "New York",
+  "state": "NY",
+  "postal_code": "10001",
+  "country": "US"
+}

curl:
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/addresses/4/

### 12.3 Create Address
POST /addresses/
Body:
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+12025550123",
  "line1": "123 Main St",
  "line2": "",
  "city": "New York",
  "state": "NY",
  "postal_code": "10001",
  "country": "US"
}
Response 201: same fields + id.
+Response 201 (example):
+{
+  "id": 4,
+  "full_name": "John Doe",
+  "email": "john@example.com",
+  "phone": "+12025550123",
+  "line1": "123 Main St",
+  "line2": "",
+  "city": "New York",
+  "state": "NY",
+  "postal_code": "10001",
+  "country": "US"
+}

curl:
curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"full_name":"John Doe","email":"john@example.com","phone":"+12025550123","line1":"123 Main St","line2":"","city":"New York","state":"NY","postal_code":"10001","country":"US"}' \
  http://localhost:8000/api/v1/addresses/

### 12.4 Update Address
PUT /addresses/{id}/ (send all fields)  
PATCH /addresses/{id}/ (send only changed fields)

Body (PUT example):
{
  "full_name": "John D.",
  "email": "john@example.com",
  "phone": "+12025550123",
  "line1": "456 New Ave",
  "line2": "Apt 9",
  "city": "New York",
  "state": "NY",
  "postal_code": "10002",
  "country": "US"
}

Body (PATCH example):
{ "line1": "456 New Ave", "postal_code": "10002" }
+Response 200 (example):
+{
+  "id": 4,
+  "full_name": "John D.",
+  "email": "john@example.com",
+  "phone": "+12025550123",
+  "line1": "456 New Ave",
+  "line2": "Apt 9",
+  "city": "New York",
+  "state": "NY",
+  "postal_code": "10002",
+  "country": "US"
+}

curl (PUT):
curl -X PUT -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"full_name":"John D.","email":"john@example.com","phone":"+12025550123","line1":"456 New Ave","line2":"Apt 9","city":"New York","state":"NY","postal_code":"10002","country":"US"}' \
  http://localhost:8000/api/v1/addresses/4/

curl (PATCH):
curl -X PATCH -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"line1":"456 New Ave","postal_code":"10002"}' \
  http://localhost:8000/api/v1/addresses/4/

### 12.5 Delete Address
DELETE /addresses/{id}/
Response 204 on success.
+Response: (no body)

curl:
curl -X DELETE -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/addresses/4/

### 12.6 Usage in Checkout
Option A: User selects a stored address id -> frontend loads it and sends full fields in order body (current order API expects full address object).
Option B (future): Extend order API to accept address_id instead of full object (not implemented yet).

### 12.7 Errors
401 Unauthorized -> Missing/invalid auth.
404 Not Found -> Address does not belong to user.
400 Validation -> Missing required fields.

### 12.8 Guest Behavior
Guests cannot use /addresses/ (no auth). They send address inline when creating an order.

---

## Guest Address Handling (How Guests Provide Addresses)

Guests do NOT store reusable addresses server-side. Each guest checkout:
1. Provide guest_email and shipping_address object in POST /orders/ body.
2. (Optional) Provide billing_address OR set use_shipping_as_billing=true.
3. Backend creates Address rows with user = null purely as snapshots for that order.
4. To "reuse" an address, frontend simply re-sends the same JSON again; there is no guest address listing endpoint.
5. After the guest logs in (becomes a user), future addresses should be managed via /addresses/ (authenticated).

Example guest order body:
{
  "guest_email": "guest@example.com",
  "shipping_address": {
    "full_name": "Alice Guest",
    "email": "guest@example.com",
    "phone": "+12025550123",
    "line1": "12 First Ave",
    "line2": "",
    "city": "Austin",
    "state": "TX",
    "postal_code": "73301",
    "country": "US"
  },
  "use_shipping_as_billing": true
}

Future extension (if needed by UX):
- Add guest_token field to Address model to allow listing past guest addresses prior to login.
- Not implemented now to keep storage minimal.

---

Need More?
Ask backend: add payment endpoint / capture logic / order cancel endpoint enhancements later.
