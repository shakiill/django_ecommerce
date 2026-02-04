"""
Custom mixins for staff-only access control.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class StaffUserRequiredMixin(UserPassesTestMixin):
    """
    Mixin that restricts access to staff members only.
    Redirects non-staff users to the staff login page.
    """
    login_url = 'staff_login'
    
    def test_func(self):
        """Check if the user is authenticated and is a staff member."""
        return self.request.user.is_authenticated and self.request.user.is_staff
    
    def handle_no_permission(self):
        """Redirect to staff login if user doesn't have permission."""
        return redirect(self.login_url)
