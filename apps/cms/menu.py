from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import MenuSection, MenuGroup, MenuItem


class MenuSectionForm(forms.ModelForm):
    class Meta:
        model = MenuSection
        fields = ["name", "slug", "order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Name"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "slug (optional)"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Order"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MenuGroupForm(forms.ModelForm):
    class Meta:
        model = MenuGroup
        fields = ["section", "name", "title", "is_featured", "order", "is_active"]
        widgets = {
            "section": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Group key (e.g. trending)"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Display title (optional)"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Order"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["group", "name", "title", "href", "badge", "style", "image", "order", "is_active"]
        widgets = {
            "group": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Name"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Title (featured)"}),
            "href": forms.TextInput(attrs={"class": "form-control", "placeholder": "/path"}),
            "badge": forms.TextInput(attrs={"class": "form-control", "placeholder": "Badge (emoji/text)"}),
            "style": forms.TextInput(attrs={"class": "form-control", "placeholder": "CSS utility class"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Order"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# List page

@login_required
def mega_menu(request):
    sections = MenuSection.objects.order_by("order", "id").prefetch_related("groups__items")
    section_form = MenuSectionForm()
    group_form = MenuGroupForm()
    item_form = MenuItemForm()
    return render(
        request,
        "cms/mega_menu.html",
        {
            "sections": sections,
            "section_form": section_form,
            "group_form": group_form,
            "item_form": item_form,
        },
    )


# Section CRUD

@login_required
def section_create(request):
    if request.method != "POST":
        return redirect("cms:mega_menu")
    form = MenuSectionForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Section created.")
    else:
        messages.error(request, "Failed to create section.")
    return redirect("cms:mega_menu")


@login_required
def section_edit(request, pk: int):
    section = get_object_or_404(MenuSection, pk=pk)
    if request.method != "POST":
        return redirect("cms:mega_menu")
    form = MenuSectionForm(request.POST, instance=section)
    if form.is_valid():
        form.save()
        messages.success(request, "Section updated.")
    else:
        messages.error(request, "Failed to update section.")
    return redirect("cms:mega_menu")


@login_required
def section_delete(request, pk: int):
    section = get_object_or_404(MenuSection, pk=pk)
    if request.method == "POST":
        section.delete()
        messages.success(request, "Section deleted.")
    return redirect("cms:mega_menu")


# Group CRUD

@login_required
def group_create(request):
    if request.method != "POST":
        return redirect("cms:mega_menu")
    form = MenuGroupForm(request.POST)
    if form.is_valid():
        try:
            form.save()
            messages.success(request, "Group created.")
        except Exception as e:
            messages.error(request, f"Create failed: {e}")
    else:
        messages.error(request, "Failed to create group.")
    return redirect("cms:mega_menu")


@login_required
def group_edit(request, pk: int):
    group = get_object_or_404(MenuGroup, pk=pk)
    if request.method != "POST":
        return redirect("cms:mega_menu")
    form = MenuGroupForm(request.POST, instance=group)
    if form.is_valid():
        form.save()
        messages.success(request, "Group updated.")
    else:
        messages.error(request, "Failed to update group.")
    return redirect("cms:mega_menu")


@login_required
def group_delete(request, pk: int):
    group = get_object_or_404(MenuGroup, pk=pk)
    if request.method == "POST":
        group.delete()
        messages.success(request, "Group deleted.")
    return redirect("cms:mega_menu")


# Item CRUD

@login_required
def item_create(request):
    if request.method != "POST":
        return redirect("cms:mega_menu")
    form = MenuItemForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, "Item created.")
    else:
        messages.error(request, "Failed to create item.")
    return redirect("cms:mega_menu")


@login_required
def item_edit(request, pk: int):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method != "POST":
        return redirect("cms:mega_menu")
    form = MenuItemForm(request.POST, request.FILES, instance=item)
    if form.is_valid():
        form.save()
        messages.success(request, "Item updated.")
    else:
        messages.error(request, "Failed to update item.")
    return redirect("cms:mega_menu")


@login_required
def item_delete(request, pk: int):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Item deleted.")
    return redirect("cms:mega_menu")
