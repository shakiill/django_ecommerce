from django import forms
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import MainSlider


class MainSliderForm(forms.ModelForm):
    class Meta:
        model = MainSlider
        fields = ["serial", "title", "description", "image", "link", "button_text", "is_active"]
        widgets = {
            "serial": forms.NumberInput(attrs={"class": "form-control", "placeholder": "serial"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Title"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Description"}),
            "link": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://"}),
            "button_text": forms.TextInput(attrs={"class": "form-control", "placeholder": "Button text"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


def slider_list(request):
    sliders = MainSlider.objects.order_by("-created_at")
    form = MainSliderForm()
    return render(request, "cms/slider.html", {"sliders": sliders, "form": form})


def slider_create(request):
    if request.method != "POST":
        return redirect("cms:slider_list")
    form = MainSliderForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, "Slider created.")
    else:
        messages.error(request, "Create failed. Please fix the errors.")
    return redirect("cms:slider_list")


def slider_edit(request, pk: int):
    slider = get_object_or_404(MainSlider, pk=pk)
    if request.method != "POST":
        return redirect("cms:slider_list")
    form = MainSliderForm(request.POST, request.FILES, instance=slider)
    if form.is_valid():
        form.save()
        messages.success(request, "Slider updated.")
    else:
        messages.error(request, "Update failed. Please fix the errors.")
    return redirect("cms:slider_list")


def slider_delete(request, pk: int):
    slider = get_object_or_404(MainSlider, pk=pk)
    if request.method == "POST":
        slider.delete()
        messages.success(request, "Slider deleted.")
    return redirect("cms:slider_list")
