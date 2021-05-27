from botocore.exceptions import ClientError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

from .serializers import *
from .models import User
from utils.cognito import *


# 회원가입 요청
class SignUp(APIView):
    def post(self, request):
        try:
            request.data['user_id']
            request.data['user_password']
            request.data['confirm_user_password']
            request.data['user_email']
            
            # Cognito를 통한 회원가입
            cog = Cognito()
            response = cog.sign_up(
                request.data['user_id'],
                request.data['user_password'],
                [{'Name': 'email', 'Value': request.data['user_email']}, ]
            )

            # 이메일 공백일 시
            if(request.data['user_email'] == ''):
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # 비밀번호 확인 다를 경우
            if(request.data['user_password']!=request.data['confirm_user_password']):
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # Cognito를 통한 회원가입
            cog = Cognito()
            response = cog.sign_up(
                request.data['user_id'],
                request.data['user_password'],
                [{'Name': 'email', 'Value': request.data['user_email']}, ]
            )

            # TODO : DB에 User 정보 저장 (Collection ID)
            serializers = UserSerializer(data={
                'user_id': request.data['user_id'],
                'collection_id': 'col_'+request.data['user_id']
            })
            if serializers.is_valid():
                serializers.save()

            # TODO : DB에 User의 Root 폴더, Trash 폴더 생성

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

            # TODO : 사용자의 Root 폴더 ID, 휴지통 ID 불러오기

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
                request.data['token']['AccessToken']
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
                request.data['token']['AccessToken'],
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
                request.data['token']['AccessToken']
            )

            # DB에서 사용자 삭제 (CASCADE이므로 하위 상관 없음)
            user = self.get_object(request.data['token']['User']['id'])
            user.delete()

            # TODO : 해당 사용자의 S3 버킷 폴더 밀기

            return Response(status=status.HTTP_200_OK)

        # ACCESS_TOKEN 필요 로그인 필요
        except Exception as e:
            return Response(str(e), status=status.HTTP_401_UNAUTHORIZED)