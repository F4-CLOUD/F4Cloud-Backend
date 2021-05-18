from rest_framework import serializers
from .models import File


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('file_id', 'folder_id', 's3_address',
                  'name', 'created_at', 'modified_at', 'size')


class FileNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('name', )


class FileMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('folder_id', )
