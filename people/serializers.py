from rest_framework import serializers
from .models import GroupInfo, FaceInfo


class FaceInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceInfo
        fields = ['id', 'user_id', 'file_id', 'group_id', 'face_id', ]


class GroupListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInfo
        fields = ['group_id', 'rep_fileid', 'rep_faceaddress',
                  'display_name', 'user_id', 'rep_faceid']
