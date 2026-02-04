from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    # List and AJAX data
    path('requisitions/', views.requisition_list, name='requisition_list'),
    path('requisitions/data/', views.requisition_list_data, name='requisition_list_data'),

    # CRUD
    path('requisitions/create/', views.requisition_create, name='requisition_create'),
    path('requisitions/<int:pk>/edit/', views.requisition_edit, name='requisition_edit'),
    path('requisitions/<int:pk>/delete/', views.requisition_delete, name='requisition_delete'),

    # Detail + status change
    path('requisitions/<int:pk>/', views.requisition_detail, name='requisition_detail'),
    path('requisitions/<int:pk>/status/', views.requisition_status_change, name='requisition_status_change'),

    # PDF
    path('requisitions/<int:pk>/pdf/', views.requisition_pdf, name='requisition_pdf'),

    # Purchase Orders
    path('pos/', views.po_list, name='po_list'),
    path('pos/data/', views.po_list_data, name='po_list_data'),
    path('pos/create/', views.po_create, name='po_create'),
    path('pos/<int:pk>/', views.po_detail, name='po_detail'),
    path('pos/<int:pk>/edit/', views.po_edit, name='po_edit'),
    path('pos/<int:pk>/delete/', views.po_delete, name='po_delete'),
    path('pos/<int:pk>/status/', views.po_status_change, name='po_status_change'),
    path('pos/<int:pk>/pdf/', views.po_pdf, name='po_pdf'),

    # APIs for bulk import/search
    path('api/variants/', views.api_get_variants, name='api_get_variants'),
    path('api/products/search/', views.api_search_products, name='api_search_products'),
    path('api/products/<int:product_id>/variants/', views.api_get_product_variants, name='api_get_product_variants'),

    # APIs for requisition import into PO
    path('api/requisitions/search/', views.api_requisitions_search, name='api_requisitions_search'),
    path('api/requisitions/<int:requisition_id>/outstanding/', views.api_requisition_outstanding_items, name='api_requisition_outstanding_items'),
]
