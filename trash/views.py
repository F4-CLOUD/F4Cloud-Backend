import json

from rest_framework.views import APIView
from rest_framework import serializers, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from files.models import File
from files.serializers import FileSerializer, FileMoveSerializer
from folders.models import Folder
from folders.serializers import FolderSerializer, FolderMoveSerializer


class Trash(APIView):
    # 폴더 불러오기
    def get_object_folder(self, folder_id):
        folder = get_object_or_404(Folder, folder_id=folder_id)
        return folder

    # 파일 불러오기
    def get_object_file(self, file_id):
        file = get_object_or_404(File, file_id=file_id)
        return file

    def validate_ids(self, id_list, type):
        if type == "file":
            for file_id in id_list:
                try:
                    File.objects.get(file_id=file_id)
                except File.DoesNotExist:
                    raise status.HTTP_400_BAD_REQUEST
            return True
        elif type == "folder":
            for folder_id in id_list:
                try:
                    Folder.objects.get(folder_id=folder_id)
                except Folder.DoesNotExist:
                    raise status.HTTP_400_BAD_REQUEST
            return True

    # 휴지통에서 복원
    def post(self, request):
        # TODO : Permission 확인

        # 복원할 위치 확인
        location = request.data['location']

        # 휴지통 복원
        # 1. 파일 복원
        files = []
        self.validate_ids(id_list=request.data['files'], type='file')
        for file_id in request.data['files']:
            obj = FileMoveSerializer(
                self.get_object_file(file_id=file_id),
                {'folder_id': location, }
            )
            if obj.is_valid():
                obj.save()
            files.append(obj.data)

        # 2. 폴더 복원
        folders = []
        self.validate_ids(id_list=request.data['folders'], type='folder')
        for folder_id in request.data['folders']:
            obj = FolderMoveSerializer(
                self.get_object_folder(folder_id=folder_id),
                {'parent_id': location, }
            )
            if obj.is_valid():
                obj.save()
            folders.append(obj.data)

        return Response({
            "files": files,
            "folders": folders,
        }, content_type="application/json", status=status.HTTP_202_ACCEPTED)

    # 휴지통에서 선택 항목 삭제
    def delete(self, request):
        # TODO : Permission 확인

        # 휴지통 ID 확인
        trash_id = request.data['trash_id']

        # 삭제 방식 확인
        target = request.data['target']

        # 휴지통 전체 삭제
        if target == 'all':
            # 1. 파일 삭제
            # 휴지통에 있는 파일 선택
            files = File.objects.filter(folder_id=trash_id)

            # 파일 삭제
            if files:
                files.delete()

            # 2. 폴더 삭제
            # 휴지통에 있는 폴더 선택
            folders = Folder.objects.filter(parent_id=trash_id)

            # 폴더 삭제
            if folders:
                folders.delete()

            return Response("OK", content_type="application/json", status=status.HTTP_200_OK)

        # 휴지통에서 선택 항목 삭제
        elif target == 'select':
            # 1. 파일 삭제
            for file_id in request.data['files']:
                self.get_object_file(file_id=file_id).delete()

            # 2. 폴더 삭제
            for folder_id in request.data['folders']:
                self.get_object_folder(folder_id=folder_id).delete()

            return Response("OK", content_type="application/json", status=status.HTTP_200_OK)
