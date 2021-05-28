from rest_framework import serializers
from .models import File


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = (
            'file_id', 'folder_id', 'user_id', 'name', 's3_url', 'path',
            'created_at', 'modified_at', 'size', 'hash_tag',
        )


class FileNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('s3_url', 'name', )


class FileMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('s3_url', 'folder_id', 'path')
