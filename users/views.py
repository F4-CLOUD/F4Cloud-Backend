from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

from f4cloud.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from .serializers import *
from .models import User
from utils.cognito import *
from folders.models import Folder
from folders.serializers import FolderSerializer
from utils.s3 import get_s3_client, upload_folder, delete_folder


# 회원가입 요청
class SignUp(APIView):
    def post(self, request):
        try:
            request.data['user_id']
            request.data['user_password']
            request.data['confirm_user_password']
            request.data['user_email']

            # 이메일 공백일 시
            if(request.data['user_email'] == ''):
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # 비밀번호 확인 다를 경우
            if(request.data['user_password'] != request.data['confirm_user_password']):
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # Cognito를 통한 회원가입
            cog = Cognito()
            cog.sign_up(
                request.data['user_id'],
                request.data['user_password'],
                [{'Name': 'email', 'Value': request.data['user_email']}, ]
            )

            # DB에 User 정보 저장 (Collection ID)
            serializers = UserSerializer(data={
                'user_id': request.data['user_id'],
                'collection_id': 'col_'+request.data['user_id']
            })
            if serializers.is_valid():
                serializers.save()

            # DB에 User의 Root 폴더, Trash 폴더 생성
            serializers = FolderSerializer(data=[
                {
                    'user': request.data['user_id'],
                    'name': request.data['user_id'],
                    'path': '',
                },
                {
                    'user': request.data['user_id'],
                    'name': request.data['user_id'],
                    'path': 'trash/',
                }
            ], many=True)
            if not serializers.is_valid():
                return Response(serializers.errors, content_type="application/json", status=status.HTTP_400_BAD_REQUEST)
            serializers.save()

            # S3에 User의 Root 폴더, Trash 폴더 생성
            # S3 Client 생성
            s3_client = get_s3_client(
                AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
            )

            # S3에 Root 폴더에 해당하는 Key 생성
            upload_folder(s3_client, "/".join([
                request.data['user_id'], ''
            ]))

            # S3에 Trash 폴더에 해당하는 Key 생성
            upload_folder(s3_client, "/".join([
                'trash', request.data['user_id'], ''
            ]))

            # 이메일로 verification 전송됨
            return Response(status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 회원가입 확인
class ConfirmSignUp(APIView):
    # 회원가입 확인 코드 재발급
    def get(self, request):
        cog = Cognito()

        response = cog.resend_confirmation_code(
            request.data['user_id'],
        )

        return Response(response, status=status.HTTP_200_OK)

    # 회원가입 확인 코드 확인
    def post(self, request):
        try:
            # Cognito를 통해 회원가입 확인
            cog = Cognito()
            # code는 이메일로 받은 verification code
            response = cog.confirm_sign_up(
                request.data['user_id'],
                request.data['code'],
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 로그인
class SignIn(APIView):
    def post(self, request):
        try:
            # Cognito를 이용하여 사용자 로그인
            cog = Cognito()

            user_token = cog.sign_in_admin(
                request.data['user_id'],
                request.data['user_password']
            )

            # 사용자의 Root 폴더 ID, 휴지통 ID 불러오기
            root = Folder.objects.get(
                user_id=request.data['user_id'], path='', parent_id=None)
            trash = Folder.objects.get(
                user_id=request.data['user_id'], path='trash/', parent_id=None)
            user_token['User']['root_id'] = root.folder_id
            user_token['User']['trash_id'] = trash.folder_id

            return Response(user_token, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 로그아웃
class SignOut(APIView):
    def get(self, request):
        try:
            # Cognito를 통해 로그아웃
            cog = Cognito()
            response = cog.sign_out(
                request.headers['Authorization']
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 비밀번호 변경
class ChangePassword(APIView):
    def post(self, request):
        try:
            cog = Cognito()
            response = cog.change_password(
                request.headers['Authorization'],
                request.data['old_password'],
                request.data['new_password'],
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 비밀번호 잊어버렸을 때
class ForgotPassword(APIView):
    def post(self, request):
        try:
            cog = Cognito()
            response = cog.forgot_password(
                request.data['user_id']
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 비밀번호 잊어버린 거 Confirm
class ConfirmForgotPassword(APIView):
    def post(self, request):
        try:
            cog = Cognito()
            response = cog.reset_password(
                request.data['user_id'],
                request.data['new_password'],
                request.data['code'],
            )

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 사용자 삭제 탈퇴
class DeleteUser(APIView):
    def get_object(self, user_id):
        user = get_object_or_404(User, user_id=user_id)
        return user

    def get(self, request):
        try:
            cog = Cognito()
            cog.delete_user(
                request.headers['Authorization']
            )

            # DB에서 사용자 삭제 (CASCADE이므로 하위 상관 없음)
            user = self.get_object(request.data['user_id'])
            user.delete()

            # 해당 사용자의 S3 버킷 폴더 밀기
            s3_client = get_s3_client(
                request.headers['Access-Key-Id'],
                request.headers['Secret-Key'],
                request.headers['Session-Token'],
            )
            delete_folder(s3_client, '/'.join([request.data['user_id'], '']))
            delete_folder(
                s3_client, '/'.join(['trash', request.data['user_id'], ''])
            )

            return Response(status=status.HTTP_200_OK)

        # ACCESS_TOKEN 필요 로그인 필요
        except Exception as e:
            return Response(str(e), status=status.HTTP_401_UNAUTHORIZED)
