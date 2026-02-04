from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.user.models import Customer, CustomUser


class CustomerRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Customer
        fields = ['username', 'name', 'email', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Customer(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserInfoSerializer(serializers.ModelSerializer):
    user_type = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'uuid', 'username', 'name', 'bio', 'email', 'f_name', 'm_name', 'occupation', 'photo',
                  'cover_photo', 'nid', 'dob', 'address',
                  'is_verified', 'user_type']

    def get_user_type(self, obj):
        if obj.groups.filter(name='seller').exists():
            return 'seller'
        if obj.groups.filter(name='customer').exists():
            return 'customer'
        return 'user'


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            # Try email as username
            try:
                user_obj = CustomUser.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                user = None
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid credentials.'})
        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'name', 'f_name', 'm_name', 'occupation', 'email', 'photo', 'cover_photo', 'signature',
            'nid', 'dob', 'address', 'bio',
        ]
        extra_kwargs = {
            'email': {'required': False},
            'photo': {'required': False},
            'cover_photo': {'required': False},
            'signature': {'required': False},
            'dob': {'required': False},
        }
