import boto3
import botocore
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from utils import settings
from rest_framework import exceptions
from django.http import HttpResponse
from rest_framework.generics import get_object_or_404

from .serializers import *
from .models import User
from utils.cognito import *

# 회원가입요청


class SignUp(APIView):
    def post(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)

            user = idp_client.sign_up(ClientId=settings.DEFAULT_USER_POOL_APP_ID,
                                      Username=request.data['user_id'],
                                      Password=request.data['user_password'],
                                      UserAttributes=[
                                          {'Name': 'email', 'Value': request.data['user_email']}, ]
                                      )

            settings.USERNAME = request.data['user_id']
            # 이메일 공백일 시
            if(request.data['user_email'] == ''):
                return Response(status=status.HTTP_400_BAD_REQUEST)

        # 이미 존재하는 Id
        except idp_client.exceptions.UsernameExistsException:
            return Response(status=status.HTTP_409_CONFLICT)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except idp_client.exceptions.InvalidPasswordException:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # # db에 저장
        # serializers = UserSerializer(data=request.data)
        # if serializers.is_valid():
        #     serializers.save()

        # serializers.data,

        # 이메일로 verification 전송됨
        return Response(status=status.HTTP_201_CREATED)


# 회원가입 확인
class ConfirmSignUp(APIView):
    def post(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)

            # SignUp하고 난 뒤 username이 유효하면 request에 username 필요 없지만 만료될 시 필요
            username = ''
            if(settings.USERNAME == ''):
                username = request.data['username']
            else:
                username = settings.USERNAME

            # code는 이메일로 받은 verification code
            user = idp_client.confirm_sign_up(ClientId=settings.DEFAULT_USER_POOL_APP_ID,
                                              Username=username,
                                              ConfirmationCode=request.data['code']
                                              )

            return Response(status=status.HTTP_201_CREATED)

        # 만료된 코드
        except idp_client.exceptions.ExpiredCodeException:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 올바르지 않은 코드
        except idp_client.exceptions.CodeMismatchException:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# 회원가입 확인 코드 재발급
class GetEmailVerification(APIView):
    def post(self, request):
        idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)

        # SignUp하고 난 뒤 username이 유효하면 request에 username 필요 없지만 만료될 시 필요
        username = ''
        if(settings.USERNAME == ''):
            username = request.data['username']
        else:
            username = settings.USERNAME

        user = idp_client.resend_confirmation_code(ClientId=settings.DEFAULT_USER_POOL_APP_ID,
                                                   Username=username
                                                   )

        # 지정한 이메일로 verification code 전송 (user['CodeDeliveryDetails']['Destination'])
        return Response(status=status.HTTP_201_CREATED)


# 로그아웃
class SignOut(APIView):
    def get(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)

            user = idp_client.global_sign_out(
                AccessToken=request.data['token'])

            return Response(status=status.HTTP_200_OK)

        # 로그인 상태가 아닐 시
        except idp_client.exceptions.NotAuthorizedException:
            return Response(status=status.HTTP_404_NOT_FOUND)

# 로그인


class AdminInitiateAuth(APIView):
    def post(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)
            ci_client = boto3.client(
                'cognito-identity', **settings.DEFAULT_CONFIG)

            user = idp_client.admin_initiate_auth(UserPoolId=settings.DEFAULT_USER_POOL_ID,
                                                  AuthFlow='ADMIN_NO_SRP_AUTH',
                                                  ClientId=settings.DEFAULT_USER_POOL_APP_ID,
                                                  AuthParameters={'USERNAME': request.data['username'],
                                                                  'PASSWORD': request.data['password']}
                                                  )

            settings.ACCESS_TOKEN = user["AuthenticationResult"]["AccessToken"]
            settings.USERNAME = request.data['username']
            # get identity id
            res = ci_client.get_id(AccountId=settings.ACCOUNTID,
                                   IdentityPoolId=settings.IDENTITYPOOLID,
                                   Logins={
                                       settings.DEFAULT_USER_POOL_LOGIN_PROVIDER: user[
                                           'AuthenticationResult']['IdToken']
                                   }
                                   )
            return Response(user["AuthenticationResult"]["AccessToken"], status=status.HTTP_201_CREATED)
        # 아이디 혹은 비밀번호가 일치하지 않음
        except idp_client.exceptions.NotAuthorizedException:
            return Response(status=status.HTTP_400_BAD_REQUEST)


# 비밀번호 변경
class ChangePassword(APIView):
    def post(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)
            user = idp_client.change_password(PreviousPassword=request.data['OldPassword'],
                                              ProposedPassword=request.data['NewPassword'],
                                              AccessToken=settings.ACCESS_TOKEN
                                              )

            # TODO : db password 변경
            user = get_object_or_404(User, user_id=settings.USERNAME)
            serializers = PasswordSerializer(
                user, {'user_password': request.data['NewPassword'], }
            )
            if serializers.is_valid():
                serializers.save()

            return Response(status=status.HTTP_201_CREATED)

        # 현재 비밀번호가 일치하지 않음
        except idp_client.exceptions.NotAuthorizedException:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except idp_client.exceptions.InvalidPasswordException:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 횟수 초과
        except idp_client.exceptions.LimitExceededException:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 유효하지 않은 ACCESSTOKEN 로그인 필요
        except idp_client.exceptions.InvalidParameterException:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


# 비밀번호 잊어버렸을 때
class ForgotPassword(APIView):
    def post(self, request):
        idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)
        user = idp_client.forgot_password(ClientId=settings.DEFAULT_USER_POOL_APP_ID,
                                          Username=request.data['username']
                                          )

        settings.USERNAME = request.data['username']

        return Response(status=status.HTTP_201_CREATED)


# 비밀번호 잊어버린 거 Confirm
class ConfirmForgotPassword(APIView):
    def post(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)
            user = idp_client.confirm_forgot_password(ClientId=settings.DEFAULT_USER_POOL_APP_ID,
                                                      Username=settings.USERNAME,
                                                      Password=request.data['newpassword'],
                                                      ConfirmationCode=request.data['code']
                                                      )

            # # TODO : db password 변경
            # user = get_object_or_404(User, user_id=settings.USERNAME)
            # serializers = PasswordSerializer(
            #     user, {'user_password': request.data['newpassword'], }
            # )

            if serializers.is_valid():
                serializers.save()

            return Response(status=status.HTTP_201_CREATED)

        # 재시도 필요
        except botocore.exceptions.ParamValidationError:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        # 만료된 코드
        except idp_client.exceptions.ExpiredCodeException:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # 올바르지 않은 코드
        except idp_client.exceptions.CodeMismatchException:
            return Response(status=status.HTTP_400_BAD_REQUEST)


'''
# 사용자 정보 조회
class RetrieveInfo(APIView):
    def get(self,request,*args,**kwargs):
        try:
             idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)
             user=idp_client.get_user(AccessToken=settings.ACCESS_TOKEN)

             return Response(data={'user':user}, status=status.HTTP_201_CREATED)

        except:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
'''

# 사용자 삭제 탈퇴


class DeleteUser(APIView):
    def get(self, request):
        try:
            idp_client = boto3.client('cognito-idp', **settings.DEFAULT_CONFIG)
            user = idp_client.delete_user(AccessToken=settings.ACCESS_TOKEN)

            # TODO : db에서 삭제
            # user = User.objects.filter(user_id=settings.USERNAME)
            # user.delete()

            return Response(status=status.HTTP_200_OK)

        # ACCESS_TOKEN 필요 로그인 필요
        except:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
