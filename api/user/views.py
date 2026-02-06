from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

from api.user.serializers import CustomerRegistrationSerializer, UserInfoSerializer, \
    LoginSerializer, ProfileUpdateSerializer
from apps.user.models import Customer, OtpToken



class CustomerRegistrationView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    queryset = Customer.objects.all()
    serializer_class = CustomerRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save(is_verified=False)
        OtpToken.create_otp_for_user(user.username)
        # TODO: Integrate SMS sending here


class OtpVerificationView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserInfoSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        otp = request.data.get('otp')
        if not username or not otp:
            return Response({'detail': 'Username and OTP required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = OtpToken.objects.filter(user=username, otp=otp, used=False).latest('timestamp')
        except OtpToken.DoesNotExist:
            return Response({'detail': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        token.used = True
        token.save()
        from apps.user.models import CustomUser
        user = CustomUser.objects.get(username=username)
        user.is_verified = True
        user.save()
        user_data = self.get_serializer(user).data
        # Create or get token for the user
        from rest_framework.authtoken.models import Token as AuthToken
        auth_token, created = AuthToken.objects.get_or_create(user=user)
        return Response({
            'detail': 'OTP verified successfully.',
            'user': user_data,
            'token': auth_token.key
        }, status=status.HTTP_200_OK)


class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        device = request.data.get('device', None)
        username = request.data.get('username', None)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if not user.is_verified:
            OtpToken.create_otp_for_user(user.username)
            raise ValidationError({"detail": {
                'message': 'OTP sent successfully',
                'is_active': False
            }})
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserInfoSerializer(user).data
        return Response({
            'token': token.key,
            'user': user_data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        try:
            token = Token.objects.get(user=request.user)
            token.delete()
        except Token.DoesNotExist:
            pass
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class TokenValidView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        # Check if the token exists and is valid
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return Response(False)
        token_key = auth_header.split(' ')[1]
        from rest_framework.authtoken.models import Token
        if Token.objects.filter(key=token_key, user=request.user).exists():
            return Response(True)
        return Response(False)


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    # Support both session auth for dashboard and token for other apps
    from rest_framework.authentication import SessionAuthentication
    authentication_classes = [TokenAuthentication, SessionAuthentication] 
    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
