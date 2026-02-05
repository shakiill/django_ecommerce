"""
Customer registration views using Django authentication (not API).
"""
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from apps.user.models import Customer, OtpToken
import json


class CustomerRegistrationView(View):
    """
    Handle customer registration with OTP verification.
    Uses Django sessions, not API tokens.
    """
    template_name = 'storefront/register.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    def post(self, request):
        """Handle registration form submission"""
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # AJAX request
            try:
                # Store 'next' in session if provided
                next_url = request.GET.get('next')
                if next_url:
                    request.session['login_next_url'] = next_url
                
                data = json.loads(request.body)
                name = data.get('name')
                username = data.get('username')
                email = data.get('email')
                password = data.get('password')
                
                # Validate required fields
                if not all([name, username, email, password]):
                    return JsonResponse({
                        'success': False,
                        'error': 'All fields are required'
                    }, status=400)
                
                # Check if username exists
                if Customer.objects.filter(username=username).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Username already exists'
                    }, status=400)
                
                # Check if email exists
                if Customer.objects.filter(email=email).exists():
                    return JsonResponse({
                        'success': False,
                        'error': 'Email already exists'
                    }, status=400)
                
                # Create user
                user = Customer(
                    username=username,
                    email=email,
                    name=name,
                    is_verified=False
                )
                user.set_password(password)
                user.save()
                
                # Generate OTP
                OtpToken.create_otp_for_user(username)
                
                # Store username in session for OTP verification
                request.session['pending_verification_username'] = username
                
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful. Please verify OTP.'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        return JsonResponse({'error': 'Invalid request'}, status=400)


class OtpVerificationView(View):
    """
    Handle OTP verification and login user.
    """
    template_name = 'storefront/otp_verify.html'

    def get(self, request):
        if 'pending_verification_username' not in request.session:
            return redirect('staff_login')
            
        # Capture next param if present in URL
        next_url = request.GET.get('next')
        if next_url:
            request.session['login_next_url'] = next_url
            
        return render(request, self.template_name)

    def post(self, request):
        """Verify OTP and login user"""
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                otp = data.get('otp')
                
                if not username or not otp:
                    return JsonResponse({
                        'success': False,
                        'error': 'Username and OTP required'
                    }, status=400)
                
                # Verify OTP
                try:
                    token = OtpToken.objects.filter(
                        user=username,
                        otp=otp,
                        used=False
                    ).latest('timestamp')
                except OtpToken.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid OTP'
                    }, status=400)
                
                # Mark OTP as used
                token.used = True
                token.save()
                
                # Get user and mark as verified
                user = Customer.objects.get(username=username)
                user.is_verified = True
                user.save()
                
                # Login user using Django session
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                # Determine redirect URL
                redirect_url = request.session.get('login_next_url', '/my-account/')
                
                # Clear pending verification and next url from session
                if 'pending_verification_username' in request.session:
                    del request.session['pending_verification_username']
                if 'login_next_url' in request.session:
                    del request.session['login_next_url']
                
                return JsonResponse({
                    'success': True,
                    'message': 'OTP verified successfully. You are now logged in!',
                    'redirect_url': redirect_url
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        
        return JsonResponse({'error': 'Invalid request'}, status=400)
