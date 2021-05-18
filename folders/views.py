import json

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import Folder
from .serializers import *
from files.models import File
from files.serializers import FileSerializer


class FolderCreate(APIView):
    # 폴더 생성
    def post(self, request):
        # TODO : Permission 확인

        # 폴더 생성
        serializers = FolderSerializer(data=request.data)
        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, content_type="application/json", status=status.HTTP_201_CREATED)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FolderDetail(APIView):
    # 폴더 불러오기
    def get_object(self, folder_id):
        folder = get_object_or_404(Folder, folder_id=folder_id)
        return folder

    # 폴더 정보 조회
    def get(self, request, folder_id):
        # TODO : Permission 확인

        # 폴더 불러오기
        folder = self.get_object(folder_id)
        serializers = FolderSerializer(folder)
        return Response(serializers.data, content_type="application/json", status=status.HTTP_200_OK)

    # 폴더 이름 변경
    def put(self, request, folder_id=None):
        # TODO : Permission 확인

        # 폴더 불러오기
        folder = self.get_object(folder_id)

        # Serializer와 매칭
        serializers = FolderNameSerializer(
            folder, {'name': request.data['new_name']}
        )
        if serializers.is_valid():
            serializers.save()
            return Response("OK", content_type="application/json", status=status.HTTP_202_ACCEPTED)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    # 폴더 휴지통으로 이동
    def delete(self, request, folder_id=None):
        # TODO : Permission 확인

        # 사용자의 휴지통 정보 가져오기
        trash = request.data['trash']

        # 휴지통으로 옮기려는 폴더 찾기
        folder = self.get_object(folder_id)

        # Serializer와 매칭
        serializers = FolderMoveSerializer(folder, {'parent_id': trash})

        if serializers.is_valid():
            serializers.save()
            return Response("OK", content_type="application/json", status=status.HTTP_202_ACCEPTED)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FolderElements(APIView):
    # 폴더 내 구성 요소 조회
    def get(self, request, folder_id):
        # TODO : Permission 확인

        # 1. 폴더 목록 조회
        folders = Folder.objects.filter(parent_id=folder_id)
        folder_serializers = FolderSerializer(folders, many=True)

        # 2. 파일 목록 조회
        files = File.objects.filter(folder_id=folder_id)
        files_serializers = FileSerializer(files, many=True)

        # 3. 결과 응답
        return Response({
            'folders': folder_serializers.data,
            'files': files_serializers.data,
        }, content_type="application/json", status=status.HTTP_202_ACCEPTED)


class FolderMove(APIView):
    # 폴더 불러오기
    def get_object(self, folder_id):
        folder = get_object_or_404(Folder, folder_id=folder_id)
        return folder

    # 폴더 이동
    def post(self, request, folder_id=None):
        # TODO : Permission 확인

        # 폴더 불러오기
        folder = self.get_object(folder_id)

        # Serializer와 매칭
        serializers = FolderMoveSerializer(
            folder, {
                'parent_id': request.data['location'],
            }
        )

        if serializers.is_valid():
            serializers.save()
            return Response("OK", content_type="application/json", status=status.HTTP_202_ACCEPTED)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)
