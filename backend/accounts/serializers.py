from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.conf import settings
from .models import Profile, phone_validator

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email')
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'date_joined', 'created_at', 'updated_at']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        new_email = user_data.get('email')
        if new_email and new_email.lower() != instance.user.email.lower():
            if User.objects.filter(email__iexact=new_email).exclude(pk=instance.user.pk).exists():
                raise serializers.ValidationError({'email': 'This email is already in use by another account.'})
            instance.user.email = new_email.lower()
            instance.user.save()

        instance.full_name = validated_data.get('full_name', instance.full_name)
        if 'phone' in validated_data:
            instance.phone = validated_data.get('phone')
        instance.save()
        return instance

class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255, required=True)
    username = serializers.CharField(max_length=150, required=True)
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, validators=[phone_validator])
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate_username(self, value):
        cleaned = value.strip()
        if User.objects.filter(username__iexact=cleaned).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return cleaned

    def validate_email(self, value):
        cleaned = value.strip().lower()
        if User.objects.filter(email__iexact=cleaned).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return cleaned

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['full_name']
        )
        profile = Profile.objects.create(
            user=user,
            full_name=validated_data['full_name'],
            phone=validated_data.get('phone', '') or None
        )
        refresh = RefreshToken.for_user(user)
        return {
            'user': ProfileSerializer(profile).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }

class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    remember_me = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        ident = attrs.get('username_or_email', '').strip()
        password = attrs.get('password')
        remember_me = attrs.get('remember_me', False)

        user = User.objects.filter(Q(username__iexact=ident) | Q(email__iexact=ident)).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid credentials. Please check your username/email and password.")

        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")

        refresh = RefreshToken.for_user(user)
        if remember_me:
            lifetime = getattr(settings, 'SIMPLE_JWT', {}).get('REFRESH_TOKEN_LIFETIME_REMEMBER_ME', timedelta(days=30))
            refresh.set_exp(lifetime=lifetime)

        profile, _ = Profile.objects.get_or_create(user=user, defaults={'full_name': user.get_full_name() or user.username})

        return {
            'user': ProfileSerializer(profile).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password does not match.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
