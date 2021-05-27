from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id', 'collection_id',)


class UserOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('user_id',)
