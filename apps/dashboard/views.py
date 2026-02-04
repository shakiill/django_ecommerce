from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, DetailView

from apps.helpers.mixins import StaffUserRequiredMixin


# Create your views here.
class DashboardHomeView(StaffUserRequiredMixin, TemplateView):
    template_name = 'dashboard.html'
