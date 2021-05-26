# -*- coding: utf-8 -*-
import jwt
import boto3
import botocore.exceptions
from rest_framework import response

from f4cloud.settings import *


class Cognito():
    user_pool_id = DEFAULT_USER_POOL_ID
    app_client_id = DEFAULT_USER_POOL_APP_ID
    identity_pool_id = IDENTITY_POOL_ID
    account_id = ACCOUNTID
    aws_access_key_id = AWS_ACCESS_KEY_ID
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    region = DEFAULT_REGION_NAME
    default_config = {
        'region_name': DEFAULT_REGION_NAME,
        'aws_access_key_id': AWS_ACCESS_KEY_ID,
        'aws_secret_access_key': AWS_SECRET_ACCESS_KEY
    }
    default_login_provider = 'cognito-idp.{0}.amazonaws.com/{1}'.format(
        DEFAULT_REGION_NAME, DEFAULT_USER_POOL_ID
    )

    # 회원가입
    def sign_up(self, username, password, UserAttributes):
        try:
            idp_client = boto3.client('cognito-idp', **self.default_config)
            response = idp_client.sign_up(
                ClientId=self.app_client_id,
                Username=username,
                Password=password,
                UserAttributes=UserAttributes)
            return response
        # 이미 존재하는 Id
        except idp_client.exceptions.UsernameExistsException:
            raise botocore.exceptions.UsernameExistsException

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except idp_client.exceptions.InvalidPasswordException:
            raise botocore.exceptions.InvalidPasswordException

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError:
            raise botocore.exceptions.ParamValidationError

    # 회원가입 확인
    def confirm_sign_up(self, username, confirm_code):
        try:
            idp_client = boto3.client('cognito-idp', **self.default_config)
            response = idp_client.confirm_sign_up(
                ClientId=self.app_client_id,
                Username=username,
                ConfirmationCode=confirm_code
            )
            return response
        # 만료된 코드
        except idp_client.exceptions.ExpiredCodeException:
            raise botocore.exceptions.ExpiredCodeException
        # 올바르지 않은 코드
        except idp_client.exceptions.CodeMismatchException:
            raise botocore.exceptions.CodeMismatchException

    # 회원가입 확인 코드 재전송
    def resend_confirmation_code(self, username):
        idp_client = boto3.client('cognito-idp', **self.default_config)
        response = idp_client.resend_confirmation_code(
            ClientId=self.app_client_id,
            Username=username
        )
        return response

    # 로그인
    def sign_in_admin(self, username, password):
        try:
            # ID Token 불러오기
            idp_client = boto3.client('cognito-idp', **self.DEFAULT_CONFIG)
            response = idp_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.app_client_id,
                AuthFlow='ADMIN_NO_SRP_AUTH',
                AuthParameters={'USERNAME': username, 'PASSWORD': password}
            )

            id_token = response['AuthenticationResult']['IdToken']
            access_token = response['AuthenticationResult']['AccessToken']
            refresh_token = response['AuthenticationResult']['RefreshToken']

            # IdentityId 불러오기
            ci_client = boto3.client('cognito-identity', **self.DEFAULT_CONFIG)
            resp = ci_client.get_id(
                AccountId=self.account_id,
                IdentityPoolId=self.identity_pool_id,
                Logins={self.default_login_provider: id_token}
            )

            # 사용자 정보 Decoding
            user_info = jwt.decode(id_token, verify=False)

            # TODO : 사용자의 Root 폴더 ID, 휴지통 ID 불러오기

            # User Token 생성
            user_token = {
                'User': {
                    'id': user_info['cognito:username'],
                    'sub': user_info['sub'],
                    'name': user_info['name'],
                    'email': user_info['email'],
                    'root_id': 0,
                    'trash_id': 0,
                },
                'exp': user_info['exp'],
                'IdentityId': response['IdentityId'],
                'IdToken': id_token,
                'AccessToken': access_token,
                'RefreshToken': refresh_token,
                'Credentials': {
                    'AccessKeyId': response['Credentials']['AccessKeyId'],
                    'SessionToken': response['Credentials']['SessionToken'],
                    'SecretKey': response['Credentials']['SecretKey']
                }
            }

            return user_token
        except idp_client.exceptions.NotAuthorizedException:
            raise botocore.exceptions.NotAuthorizedException

    # 로그아웃
    def sign_out(self, access_token):
        try:
            idp_client = boto3.client('cognito-idp', **self.DEFAULT_CONFIG)

            response = idp_client.global_sign_out(
                AccessToken=access_token
            )

            return response

        # 로그인 상태가 아닐 시
        except idp_client.exceptions.NotAuthorizedException:
            raise botocore.exceptions.NotAuthorizedException

    # 비밀번호 변경
    def change_password(self, access_token, old_password, new_password):
        try:
            idp_client = boto3.client('cognito-idp', **self.DEFAULT_CONFIG)
            response = idp_client.change_password(
                AccessToken=access_token,
                PreviousPassword=old_password,
                ProposedPassword=new_password,
            )

            return response

        # 현재 비밀번호가 일치하지 않음
        except idp_client.exceptions.NotAuthorizedException:
            raise botocore.exceptions.NotAuthorizedException

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except idp_client.exceptions.InvalidPasswordException:
            raise botocore.exceptions.InvalidPasswordException

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError:
            raise botocore.exceptions.ParamValidationError

        # 횟수 초과
        except idp_client.exceptions.LimitExceededException:
            raise botocore.exceptions.LimitExceededException

        # 유효하지 않은 ACCESSTOKEN 로그인 필요
        except idp_client.exceptions.InvalidParameterException:
            raise botocore.exceptions.InvalidParameterException

    # 비밀번호 잊어버림
    def forgot_password(self, username):
        client = boto3.client('cognito-idp', **self.DEFAULT_CONFIG)
        response = client.forgot_password(
            ClientId=self.DEFAULT_USER_POOL_APP_ID,
            Username=username,
        )

        return response

    # 비밀번호 초기화
    def reset_password(self, username, new_password, confirmation_code):
        try:
            client = boto3.client('cognito-idp', **self.DEFAULT_CONFIG)
            response = client.confirm_forgot_password(
                ClientId=self.DEFAULT_USER_POOL_APP_ID,
                Username=username,
                Password=new_password,
                ConfirmationCode=confirmation_code,
            )

            return response

        # 재시도 필요
        except botocore.exceptions.ParamValidationError:
            raise botocore.exceptions.ParamValidationError
        # 만료된 코드
        except client.exceptions.ExpiredCodeException:
            raise botocore.exceptions.ExpiredCodeException
        # 올바르지 않은 코드
        except client.exceptions.CodeMismatchException:
            raise botocore.exceptions.CodeMismatchException

    # 사용자 탈퇴
    def delete_user(self, access_token):
        try:
            client = boto3.client('cognito-idp', **self.DEFAULT_CONFIG)
            response = client.delete_user(
                AccessToken=access_token
            )

            return response

        # ACCESS_TOKEN 필요 로그인 필요
        except Exception as e:
            raise e
