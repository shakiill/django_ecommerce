from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from .models import Contact

@staff_member_required
def contact_list(request):
    """
    Staff-only view to list contact submissions.
    """
    contacts = Contact.objects.all().order_by('-created_at')
    return render(request, 'cms/contact_list.html', {'contacts': contacts})
