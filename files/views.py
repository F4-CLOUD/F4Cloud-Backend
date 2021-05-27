import json

from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from .serializers import *
from .models import File
from utils.s3 import *
from utils.cognito import is_token_valid


class FileCreate(APIView):
    # 파일 업로드
    def post(self, request):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 정보 확인
        file_info = json.loads(request.data['file_info'])
        user_info = json.loads(request.data['user'])

        # 파일 불러오기
        file = request.FILES.get('file')

        # S3에 업로드
        print(upload_file(
            user_info['bucket'], file, '{0}_{1}'.format(
                file_info['folder_id'], file_info['name']
            ))
        )

        # S3 Address, Size 처리
        file_info['s3_address'] = 'https://{0}.s3.amazonaws.com/{1}'.format(
            user_info['bucket'], '{0}_{1}'.format(
                file_info['folder_id'], file_info['name']
            )
        )

        # DB에 데이터 저장
        serializers = FileSerializer(data=file_info)
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
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 정보 확인
        file = self.get_object(file_id)
        serializers = FileSerializer(file)

        # 완료 응답
        return Response(serializers.data, content_type="application/json", status=status.HTTP_202_ACCEPTED)

    # 파일 다운로드
    def post(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 정보 확인
        file = self.get_object(file_id)
        serializers = FileSerializer(file)

        # 완료 응답
        return Response(serializers.data['s3_address'], content_type="application/json", status=status.HTTP_202_ACCEPTED)

    # 파일 이름 변경
    def put(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 불러오기
        file = self.get_object(file_id)

        # S3 파일 Key 수정
        rename_file(
            request.data['bucket'], '{0}_{1}'.format(
                file.folder_id, file.name
            ), '{0}_{1}'.format(
                file.folder_id, request.data['new_name']
            )
        )

        # 파일 이름 수정
        serializers = FileNameSerializer(
            file, {
                's3_address': 'https://{0}.s3.amazonaws.com/{1}'.format(
                    request.data['bucket'], '{0}_{1}'.format(
                        file.folder_id, request.data['new_name']
                    )
                ),
                'name': request.data['new_name'],
            }
        )

        if serializers.is_valid():
            serializers.save()
            return Response(serializers.data, content_type="application/json", status=status.HTTP_200_OK)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)

    # 파일 삭제
    def delete(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

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
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 불러오기
        file = self.get_object(file_id)

        # S3 파일 Key 수정
        rename_file(
            request.data['bucket'], '{0}_{1}'.format(
                file.folder_id, file.name
            ), '{0}_{1}'.format(
                request.data['location'], file.name
            )
        )

        # Folder 위치 수정
        serializers = FileMoveSerializer(
            file, {
                's3_address': 'https://{0}.s3.amazonaws.com/{1}'.format(
                    request.data['bucket'], '{0}_{1}'.format(
                        request.data['location'], file.name
                    )
                ),
                'folder_id': request.data['location'],
            }
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
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 정보 확인
        file = self.get_object(file_id)
        serializers = FileSerializer(file)

        # 파일 이름 수정
        file_name = serializers.data['name'].split('.')
        print(file_name)
        if len(file_name) >= 2:
            extension = file_name.pop()
            filename = ''.join(file_name + ["_copy"])
            new_name = '.'.join([filename, extension])
        else:
            new_name = serializers.data['name'] + '_copy'

        new_file = {
            'folder_id': serializers.data['folder_id'],
            'name': new_name,
            'size': serializers.data['size'],
        }

        # S3에 복사본 생성
        copy_file(request.data['bucket'], '{0}_{1}'.format(
            file.folder_id, file.name
        ), '{0}_{1}'.format(
            new_file['folder_id'], new_name
        ))

        s3_address = 'https://{0}.s3.amazonaws.com/{1}'.format(
            request.data['bucket'], '{0}_{1}'.format(
                new_file['folder_id'], new_name
            )
        )
        new_file['s3_address'] = s3_address

        # DB에 데이터 저장
        new_serializers = FileSerializer(data=new_file)
        if new_serializers.is_valid():
            new_serializers.save()

            # 완료 응답
            return Response(new_serializers.data, content_type="application/json", status=status.HTTP_202_ACCEPTED)
        return Response(new_serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)
