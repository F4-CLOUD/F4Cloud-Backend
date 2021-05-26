import botocore.exceptions
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
            # Cognito를 통한 회원가입
            cog = Cognito()
            cog.sign_up(
                request.data['user_id'],
                request.data['user_password'],
                [{'Name': 'email', 'Value': request.data['user_email']}, ]
            )

            # 이메일 공백일 시
            if(request.data['user_email'] == ''):
                return Response(status=status.HTTP_400_BAD_REQUEST)

            # TODO : DB에 User 정보 저장 (Collection ID)
            serializers = UserSerializer(data={
                'user_id': request.data['user_id'],
                'collection_id': ''
            })
            if serializers.is_valid():
                serializers.save()

            # TODO : DB에 User의 Root 폴더, Trash 폴더 생성

            # 이메일로 verification 전송됨
            return Response(status=status.HTTP_201_CREATED)

        # 이미 존재하는 Id
        except botocore.exceptions.UsernameExistsException:
            return Response("ID already exist", status=status.HTTP_409_CONFLICT)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.InvalidPasswordException:
            return Response("Invalid password", status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError:
            return Response("Invalid password", status=status.HTTP_400_BAD_REQUEST)


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

        # 만료된 코드
        except botocore.exceptions.ExpiredCodeException:
            return Response("Expired Code", status=status.HTTP_400_BAD_REQUEST)
        # 올바르지 않은 코드
        except botocore.exceptions.CodeMismatchException:
            return Response("Wrong Code", status=status.HTTP_400_BAD_REQUEST)


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
        # 아이디 혹은 비밀번호가 일치하지 않음
        except botocore.exceptions.NotAuthorizedException:
            return Response("ID or Password mismatch", status=status.HTTP_400_BAD_REQUEST)


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

        # 로그인 상태가 아닐 시
        except botocore.exceptions.NotAuthorizedException:
            return Response("Not Sign in now", status=status.HTTP_404_NOT_FOUND)


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

        # 현재 비밀번호가 일치하지 않음
        except botocore.exceptions.NotAuthorizedException:
            return Response("Current Password mismatch", status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.InvalidPasswordException:
            return Response("Invalid New Password", status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError:
            return Response("Invalid New Password", status=status.HTTP_400_BAD_REQUEST)

        # 횟수 초과
        except botocore.exceptions.LimitExceededException:
            return Response("Count Over", status=status.HTTP_403_FORBIDDEN)

        # 유효하지 않은 ACCESSTOKEN 로그인 필요
        except botocore.exceptions.InvalidParameterException:
            return Response("Invalid Tokken", status=status.HTTP_401_UNAUTHORIZED)


# 비밀번호 잊어버렸을 때
class ForgotPassword(APIView):
    def post(self, request):
        try:
            cog = Cognito()
            response = cog.forgot_password(
                request.data['user_id']
            )

            return Response(response, status=status.HTTP_200_OK)
        except botocore.exceptions as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)


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

        # 재시도 필요
        except botocore.exceptions.ParamValidationError:
            return Response("Retry", status=status.HTTP_401_UNAUTHORIZED)
        # 만료된 코드
        except botocore.exceptions.ExpiredCodeException:
            return Response("Expired Code", status=status.HTTP_400_BAD_REQUEST)
        # 올바르지 않은 코드
        except botocore.exceptions.CodeMismatchException:
            return Response("Wrong Code", status=status.HTTP_400_BAD_REQUEST)


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
            return Response(e, status=status.HTTP_401_UNAUTHORIZED)
