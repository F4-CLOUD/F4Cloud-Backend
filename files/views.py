import datetime

import boto3
from botocore import regions
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from .serializers import *
from .models import File
from folders.models import Folder
from utils.s3 import *
from utils.cognito import is_token_valid
from trash.serializers import TrashFile, TrashFileSerializer
from f4cloud.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DEFAULT_REGION_NAME


class FileCreate(APIView):
    # 파일 업로드
    def post(self, request):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 불러오기
        file = request.FILES.get('file')

        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # S3에 업로드
        upload_file(s3_client, file, '{0}/{1}{2}'.format(
            request.data['user_id'], request.data['path'], request.data['name']
        ))

        # S3 Address 처리
        s3_url = get_s3_url('{0}/{1}{2}'.format(
            request.data['user_id'], request.data['path'], request.data['name']
        ))

        # ------------------------
        # DB 처리
        # ------------------------
        # DB에 데이터 저장 (size 처리)
        serializers = FileSerializer(data={
            'folder_id': request.data['folder_id'],
            'user_id': request.data['user_id'],
            's3_url': s3_url,
            'path': request.data['path'],
            'name': request.data['name'],
            'size': request.data['size'],
        })
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
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.GET['user_id']):
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

        # 완료 응답
        return Response(file.s3_url, content_type="application/json", status=status.HTTP_202_ACCEPTED)

    # 파일 이름 변경
    def put(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 불러오기
        file = self.get_object(file_id)

        # ------------------------
        # S3 처리
        # ------------------------
        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # S3 파일 Key 수정
        new_path = '{0}/{1}'.format(
            file.user_id.user_id, file.path
        )
        rename_move_file(s3_client, '{0}/{1}{2}'.format(
            file.user_id.user_id, file.path, file.name
        ), '{0}/{1}{2}'.format(
            file.user_id.user_id, file.path, request.data['new_name']
        ))

        # S3 Address 처리
        s3_url = get_s3_url(new_path, request.data['new_name'])

        # ------------------------
        # DB 처리
        # ------------------------
        # 파일 이름 수정
        serializers = FileNameSerializer(
            file, {
                's3_url': s3_url,
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
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.DELETE['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 사용자의 휴지통 정보 가져오기
        trash = request.DELETE['trash']

        # 파일 불러오기
        file = self.get_object(file_id)

        # ------------------------
        # S3 처리
        # ------------------------
        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # S3 Key 이름 변경
        new_path = '{0}/{1}/'.format(
            'trash', file.user_id.user_id
        )
        rename_move_file(s3_client, '{0}/{1}{2}'.format(
            file.user_id.user_id, file.path, file.name
        ), new_path + file.name)

        # S3 Address 처리
        s3_url = get_s3_url(new_path, file.name)

        # ------------------------
        # DB 처리
        # ------------------------
        # Folder 위치 수정
        serializers = FileMoveSerializer(
            file, {
                'folder_id': trash,
                'path': new_path,
                's3_url': s3_url,
            }
        )

        if serializers.is_valid():
            serializers.save()

        # 휴지통 이동 기록 생성
        trash_serializer = TrashFileSerializer(data={
            'file_id': file_id,
            'trashed_at': datetime.datetime.now(),
            'expired_at': datetime.datetime.now() + datetime.timedelta(days=30),
        })
        if trash_serializer.is_valid():
            trash_serializer.save()

            return Response(serializers.data, content_type="application/json", status=status.HTTP_200_OK)
        return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FileMove(APIView):
    # 파일 불러오기
    def get_object(self, file_id):
        file = get_object_or_404(File, file_id=file_id)
        return file

    # 폴더 불러오기
    def get_folder(self, folder_id):
        folder = get_object_or_404(Folder, folder_id=folder_id)
        return folder

    # 파일 이동
    def post(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 파일 불러오기
        file = self.get_object(file_id)

        # 폴더 정보 불러오기
        folder = self.get_folder(request.data['loc'])

        # ------------------------
        # S3 처리
        # ------------------------
        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # S3 Key 이름 변경
        new_path = '{0}{1}/'.format(
            folder.path, folder.name
        )
        rename_move_file(s3_client, '{0}/{1}{2}'.format(
            file.user_id.user_id, file.path, file.name
        ), '{0}/{1}{2}'.format(
            file.user_id.user_id, new_path, file.name
        ))

        # S3 Address 처리
        s3_url = get_s3_url('{0}/{1}'.format(
            file.user_id.user_id, new_path
        ), file.name)

        # ------------------------
        # DB 처리
        # ------------------------
        # Folder 위치 수정
        serializers = FileMoveSerializer(
            file, {
                'folder_id': folder.folder_id,
                'path': new_path,
                's3_url': s3_url,
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
        file_name = file.name.split('.')
        if len(file_name) >= 2:
            extension = file_name.pop()
            filename = ''.join(file_name + ["_copy"])
            new_name = '.'.join([filename, extension])
        else:
            new_name = file.name + '_copy'

        new_file = {
            'folder_id': file.folder_id.folder_id,
            'user_id': file.user_id.user_id,
            'name': new_name,
            'size': file.size,
            'path': file.path
        }

        # ------------------------
        # S3 처리
        # ------------------------
        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # S3 Key 이름 변경
        copy_file(s3_client, '{0}/{1}{2}'.format(
            file.user_id.user_id, file.path, file.name
        ), '{0}/{1}{2}'.format(
            new_file['user_id'], new_file['path'], new_file['name']
        ))

        # S3 Address 처리
        s3_url = get_s3_url('{0}/{1}'.format(
            new_file['user_id'], new_file['path']
        ), new_file['name'])
        new_file['s3_url'] = s3_url

        # DB에 데이터 저장
        new_serializers = FileSerializer(data=new_file)
        if new_serializers.is_valid():
            new_serializers.save()

            # 완료 응답
            return Response(new_serializers.data, content_type="application/json", status=status.HTTP_202_ACCEPTED)
        return Response(new_serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)


class FileHashTag(APIView):
    # 파일 불러오기
    def get_object(self, **kwargs):
        file = get_object_or_404(File, **kwargs)
        return file

    def post(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            file = self.get_object(
                file_id=file_id, user_id=request.data['user_id']
            )
            s3_address = file.s3_url
            client = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=DEFAULT_REGION_NAME)

            # file_address format : object URL
            proc = s3_address[8:]
            bucket = proc[:proc.find('.')]
            file_key = proc[proc.find('/') + 1:]

            # Use Amazon rekognition Object detection
            response = client.detect_labels(
                Image={'S3Object': {'Bucket': bucket, 'Name': file_key}}, MaxLabels=10)
            obj_list = list()
            translate = boto3.client(
                service_name='translate', region_name='us-east-1', use_ssl=True,
                aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
            )

            # Set Max
            max = 2
            threshold = 95.0
            for label in response['Labels']:
                max -= 1
                if(max == -1):
                    break
                if(label['Confidence'] > threshold):
                    print(label['Name'])
                    print("Confidence: " + str(label['Confidence']))
                    result = translate.translate_text(Text=label['Name'],
                                                      SourceLanguageCode="en", TargetLanguageCode="ko")
                    tag = str(result.get('TranslatedText'))
                    tag = tag.replace(' ', '_')
                    obj_list.append(tag)
            if(len(obj_list) == 0):
                return Response({'recommend': ''})
            recommend = '#'
            recommend += ' #'.join(obj_list)
            msg = {'recommend': recommend}

            return Response(msg, status=status.HTTP_200_OK)
        except Exception as e:
            msg = {'msg': str(e)}
            print(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, file_id):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            file = self.get_object(
                file_id=file_id, user_id=request.data['user_id']
            )

            serializers = FileHashTagSerializer(
                file, {
                    'hash_tag': request.data['hash_tag']
                }
            )
            if serializers.is_valid():
                serializers.save()

            return Response(serializers.data, status=status.HTTP_200_OK)

        except Exception as e:
            msg = {'msg': str(e)}
            print(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
