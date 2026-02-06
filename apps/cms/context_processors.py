from .models import SiteSetting

def site_settings(request):
    """
    Context processor to make site settings available in all templates.
    """
    settings = SiteSetting.objects.first()
    return {
        'site_settings': settings
    }
