from django.urls import path
from . import slider as slider_views
from . import menu as menu_views
from . import contact as contact_views

app_name = "cms"

urlpatterns = [
    path("contacts/", contact_views.contact_list, name="contact_list"),
    path("sliders/", slider_views.slider_list, name="slider_list"),
    path("sliders/create/", slider_views.slider_create, name="slider_create"),
    path("sliders/<int:pk>/edit/", slider_views.slider_edit, name="slider_edit"),
    path("sliders/<int:pk>/delete/", slider_views.slider_delete, name="slider_delete"),

    # Mega menu management
    path("mega-menu/", menu_views.mega_menu, name="mega_menu"),
    path("mega-menu/sections/create/", menu_views.section_create, name="section_create"),
    path("mega-menu/sections/<int:pk>/edit/", menu_views.section_edit, name="section_edit"),
    path("mega-menu/sections/<int:pk>/delete/", menu_views.section_delete, name="section_delete"),
    path("mega-menu/groups/create/", menu_views.group_create, name="group_create"),
    path("mega-menu/groups/<int:pk>/edit/", menu_views.group_edit, name="group_edit"),
    path("mega-menu/groups/<int:pk>/delete/", menu_views.group_delete, name="group_delete"),
    path("mega-menu/items/create/", menu_views.item_create, name="item_create"),
    path("mega-menu/items/<int:pk>/edit/", menu_views.item_edit, name="item_edit"),
    path("mega-menu/items/<int:pk>/delete/", menu_views.item_delete, name="item_delete"),
]
