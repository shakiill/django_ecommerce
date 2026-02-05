from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .forms import PhoneAuthenticationForm

class UserLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = PhoneAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        # 1. Check for 'next' parameter in URL
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
            
        # 2. Default logic based on role
        user = self.request.user
        if user.is_staff:
            return reverse_lazy('dashboard:home')
        return reverse_lazy('customer_dashboard')
        
    def form_valid(self, form):
        """
        Override to handle verification logic based on user role.
        """
        user = form.get_user()
        
        # 1. Superuser: Always allow login
        if user.is_superuser:
            return super().form_valid(form)
            
        # 2. Staff: If unverified, show error (No OTP)
        if user.is_staff:
            if not user.is_verified:
                from django.contrib import messages
                messages.error(self.request, "Your account is not verified. Please contact administration.")
                return self.render_to_response(self.get_context_data(form=form))
            return super().form_valid(form)
            
        # 3. Customer: If unverified, Send OTP & Redirect
        if not user.is_verified:
            # Generate OTP
            from apps.user.models import OtpToken
            OtpToken.create_otp_for_user(user.username)
            
            # Store in session
            self.request.session['pending_verification_username'] = user.username
            
            # Store 'next' in session if provided
            next_url = self.request.GET.get('next')
            if next_url:
                self.request.session['login_next_url'] = next_url
            
            # Redirect to verify page
            return redirect('verify_otp')
            
        return super().form_valid(form)

class UserLogoutView(LogoutView):
    template_name = 'logout.html'
    http_method_names = ['get', 'post', 'head', 'options']

    def get(self, request, *args, **kwargs):
        """
        Logout on GET (Django 5 blocks this by default -> 405).
        Shows confirmation page instead of redirect so users see status.
        """
        logout(request)
        context = self.get_context_data()
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        # Standard POST logout (kept for forms)
        return super().post(request, *args, **kwargs)
