from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'user_password', 'user_email',)


class UserWithoutPwSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'user_email',)


class PasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_password',)
