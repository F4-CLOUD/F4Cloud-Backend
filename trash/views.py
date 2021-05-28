from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from files.models import File
from files.serializers import FileMoveSerializer
from folders.models import Folder
from folders.serializers import FolderMoveSerializer
from utils.s3 import *
from utils.cognito import is_token_valid
from .models import *


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
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 복원할 위치 확인
        location = request.data['loc']
        restore_loc = self.get_object_folder(request.data['loc'])
        new_path = ''
        if restore_loc.parent_id:
            new_path = '{0}{1}/'.format(
                restore_loc.path, restore_loc.name
            )

        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # 휴지통 복원
        # 1. 파일 복원
        files = []
        self.validate_ids(id_list=request.data['files'], type='file')
        for file_id in request.data['files']:
            # 파일 불러오기
            file = self.get_object_file(file_id=file_id)
            files.append(file)

            rename_move_file(s3_client, '{0}{1}'.format(
                file.path, file.name
            ), '{0}/{1}{2}'.format(
                file.user_id.user_id, new_path, file.name
            ))

            # S3 Address 처리
            s3_url = get_s3_url('{0}/{1}{2}'.format(
                file.user_id.user_id, new_path, file.name
            ))

            # DB 처리
            obj = FileMoveSerializer(
                file, {
                    'folder_id': restore_loc.folder_id,
                    'path': new_path,
                    's3_url': s3_url,
                }
            )
            if obj.is_valid():
                obj.save()
            files.append(obj.data)

        # 휴지통 이동 기록 삭제
        TrashFile.objects.filter(file_id__in=request.data['files']).delete()

        # 2. 폴더 복원
        folders = []
        self.validate_ids(id_list=request.data['folders'], type='folder')
        for folder_id in request.data['folders']:
            # 폴더 불러오기
            folder = self.get_object_folder(folder_id=folder_id)

            print('{0}{1}/'.format(
                folder.path, folder.name
            ))

            # S3 Key 이름 변경
            rename_move_folder(s3_client, '{0}{1}/'.format(
                folder.path, folder.name
            ), '{0}/{1}{2}/'.format(
                folder.user_id.user_id, new_path, folder.name
            ))

            # DB 처리
            folder_serializer = FolderMoveSerializer(
                folder,
                {'parent_id': location, 'path': new_path},
            )
            if folder_serializer.is_valid():
                folder_serializer.save()
            folders.append(folder_serializer.data)

        # 휴지통 이동 기록 삭제
        TrashFolder.objects.filter(
            folder_id__in=request.data['folders']).delete()

        return Response({
            "files": files,
            "folders": folder_serializer.data,
        }, content_type="application/json", status=status.HTTP_202_ACCEPTED)

    # 휴지통에서 선택 항목 삭제
    def delete(self, request):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 휴지통 ID 확인
        trash_id = request.data['trash']

        # 삭제 방식 확인
        target = request.data['target']

        # S3 Client 생성
        s3_client = get_s3_client(
            request.headers['Access-Key-Id'],
            request.headers['Secret-Key'],
            request.headers['Session-Token'],
        )

        # 휴지통 전체 삭제
        if target == 'all':
            # 1. 파일 삭제
            # 휴지통에 있는 파일 선택
            files = File.objects.filter(folder_id=trash_id)

            # 파일 삭제
            if files:
                files.delete()

            # 휴지통 이동 기록 삭제
            TrashFile.objects.all().delete()

            # 2. 폴더 삭제
            # 휴지통에 있는 폴더 선택
            folders = Folder.objects.filter(parent_id=trash_id)

            # 폴더 삭제
            if folders:
                folders.delete()

            # 휴지통 이동 기록 삭제
            TrashFolder.objects.all().delete()

            # S3 휴지통 밀어버리기!
            clear_folder(
                s3_client, 'trash/{0}/'.format(request.data['user_id'])
            )

            return Response("OK", content_type="application/json", status=status.HTTP_200_OK)

        # 휴지통에서 선택 항목 삭제
        elif target == 'select':

            # 1. 파일 삭제
            for file_id in request.data['files']:
                file = self.get_object_file(file_id=file_id)

                delete_folder_file(
                    s3_client, 'trash/{0}/{1}'.format(
                        request.data['user_id'], file.name
                    )
                )

                file.delete(s3_client)
            # 휴지통 이동 기록 삭제
            TrashFile.objects.filter(
                file_id__in=request.data['files']).delete()

            # 2. 폴더 삭제
            for folder_id in request.data['folders']:
                folder = self.get_object_folder(folder_id=folder_id)

                delete_folder_file(
                    s3_client, 'trash/{0}/{1}/'.format(
                        request.data['user_id'], folder.name
                    )
                )

                folder.delete()
            # 휴지통 이동 기록 삭제
            TrashFolder.objects.filter(
                folder_id__in=request.data['folders']).delete()

            return Response("OK", content_type="application/json", status=status.HTTP_200_OK)
