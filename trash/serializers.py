from rest_framework import serializers
from .models import *


class TrashFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrashFolder
        fields = ('folder_id', 'trashed_at', 'expired_at', )


class TrashFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrashFile
        fields = ('file_id', 'trashed_at', 'expired_at', )
