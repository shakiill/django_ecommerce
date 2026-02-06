from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from .models import SiteSetting
from django import forms

class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = [
            'business_name', 'logo', 'favicon', 'address', 'email', 'phone', 'working_hours',
            'facebook_url', 'twitter_url', 'instagram_url', 'youtube_url',
            'footer_text', 'meta_title', 'meta_description'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'working_hours': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'footer_text': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'business_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control'}),
            'meta_title': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'favicon': forms.FileInput(attrs={'class': 'form-control'}),
        }

@user_passes_test(lambda u: u.is_staff)
def site_settings_update(request):
    settings_obj = SiteSetting.objects.first()
    if not settings_obj:
        # Create a default settings object if none exists
        settings_obj = SiteSetting.objects.create(business_name="My Store")
    
    if request.method == 'POST':
        form = SiteSettingForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Site settings updated successfully.")
            return redirect('cms:site_settings')
    else:
        form = SiteSettingForm(instance=settings_obj)
    
    return render(request, 'cms/site_settings.html', {
        'form': form,
        'settings': settings_obj
    })
