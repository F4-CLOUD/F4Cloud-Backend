from rest_framework import serializers
from .models import Folder


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('folder_id', 'parent', 'user', 'name', 'path',
                  'created_at', 'modified_at')


class FolderNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('name',)


class FolderMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('parent',)
