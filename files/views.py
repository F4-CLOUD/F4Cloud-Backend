import json

from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .serializers import *
from .models import File


class FileCreate(APIView):
    # 파일 업로드
    def post(self, request):
        # Permission 확인

        # 파일 정보 확인
        serializers = FileSerializer(data=request.data)
        # file = request.FILES['file']

        # TODO : 파일 저장 가능 여부 확인

        # TODO : S3에 업로드

        # DB에 데이터 저장
        if serializers.is_valid():
            serializers.save()

            # 완료 응답
            return Response(serializers.data, content_type="application/json", status=status.HTTP_201_CREATED)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FileDetail(APIView):
    # 파일 불러오기
    def get_object(self, file_id):
        file = get_object_or_404(File, file_id=file_id)
        return file

    # 파일 정보 조회
    def get(self, request, file_id):
        # TODO : Permission 확인

        # 파일 정보 확인
        file = self.get_object(file_id)
        serializers = FileSerializer(file)

        # 완료 응답
        return Response(serializers.data, content_type="application/json", status=status.HTTP_202_ACCEPTED)

    # TODO : 파일 다운로드

    def post(self, request, file_id):
        # Permission 확인

        # 파일 정보 확인

        # S3 파일 위치 추출

        # 완료 응답
        return

    # 파일 이름 변경
    def put(self, request, file_id):
        # TODO : Permission 확인

        # 파일 불러오기
        file = self.get_object(file_id)

        # 파일 이름 수정
        serializers = FileNameSerializer(
            file, {'name': request.data['new_name'], }
        )

        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, content_type="application/json", status=status.HTTP_200_OK)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    # 파일 삭제
    def delete(self, request, file_id):
        # TODO : Permission 확인

        # 사용자의 휴지통 정보 가져오기
        trash = request.data['trash']

        # 파일 불러오기
        file = self.get_object(file_id)

        # Folder 위치 수정
        serializers = FileMoveSerializer(
            file, {'folder_id': trash, }
        )

        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, content_type="application/json", status=status.HTTP_200_OK)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FileMove(APIView):
    # 파일 불러오기
    def get_object(self, file_id):
        file = get_object_or_404(File, file_id=file_id)
        return file

    # 파일 이동
    def post(self, request, file_id):
        # TODO : Permission 확인

        # 파일 불러오기
        file = self.get_object(file_id)

        # Folder 위치 수정
        serializers = FileMoveSerializer(
            file, {'folder_id': request.data['location'], }
        )

        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, content_type="application/json", status=status.HTTP_200_OK)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FileCopy(APIView):
    # 파일 불러오기
    def get_object(self, file_id):
        file = get_object_or_404(File, file_id=file_id)
        return file

    # 파일 복사
    def post(self, request, file_id):
        # TODO : Permission 확인

        # 파일 정보 확인
        file = self.get_object(file_id)
        serializers = FileSerializer(file)

        # 파일 이름 수정
        file_name = serializers.data['name'].split('.')
        if len(file_name) > 2:
            file_name.insert(len(file_name) - 2, "_copy")
            new_name = ''.join(file_name)
        else:
            new_name = serializers.data['name'] + '_copy'

        new_file = {
            'folder_id': serializers.data['folder_id'],
            'name': new_name,
            'size': serializers.data['size'],
        }

        # TODO : S3에 복사본 생성
        s3_address = 'test_address'
        new_file['s3_address'] = s3_address

        # DB에 데이터 저장
        new_serializers = FileSerializer(data=new_file)
        if new_serializers.is_valid():
            new_serializers.save()

            # 완료 응답
            return Response(new_serializers.data, content_type="application/json", status=status.HTTP_202_ACCEPTED)
        return Response(new_serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)
