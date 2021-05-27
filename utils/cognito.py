# -*- coding: utf-8 -*-
import datetime

import jwt
import boto3
import botocore.exceptions

from f4cloud.settings import *


# Token의 Valid 여부 파악
def is_token_valid(token, user_id):
    # Token이 Expired인지 확인
    if datetime.datetime.utcnow() > datetime.datetime.utcfromtimestamp(token['exp']):
        return False

    # Token의 User ID와 매칭이 되는지 확인
    if user_id != token['User']['id']:
        return False

    return True


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
        except idp_client.exceptions.UsernameExistsException as e:
            raise Exception('User ID already exits', e)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except idp_client.exceptions.InvalidPasswordException as e:
            raise Exception('Invalid Password', e)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError as e:
            raise Exception('Invalid Password', e)

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
        except idp_client.exceptions.ExpiredCodeException as e:
            raise Exception('Expired Code', e)
        # 올바르지 않은 코드
        except idp_client.exceptions.CodeMismatchException as e:
            raise Exception('Wrong Code', e)

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
            idp_client = boto3.client('cognito-idp', **self.default_config)
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
            ci_client = boto3.client('cognito-identity', **self.default_config)
            response = ci_client.get_id(
                AccountId=self.account_id,
                IdentityPoolId=self.identity_pool_id,
                Logins={self.default_login_provider: id_token}
            )

            # Credentials 불러오기
            response = ci_client.get_credentials_for_identity(
                IdentityId=response['IdentityId'],
                Logins={self.default_login_provider: id_token}
            )

            # 사용자 정보 Decoding
            user_info = jwt.decode(id_token, verify=False)
            print(user_info)

            # User Token 생성
            user_token = {
                'User': {
                    'id': user_info['cognito:username'],
                    'sub': user_info['sub'],
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

        # 아이디 혹은 비밀번호가 일치하지 않음
        except idp_client.exceptions.NotAuthorizedException as e:
            raise Exception('Invalid user id or user password', e)

    # 로그아웃
    def sign_out(self, access_token):
        try:
            idp_client = boto3.client('cognito-idp', **self.default_config)

            response = idp_client.global_sign_out(
                AccessToken=access_token
            )

            return response

        # 로그인 상태가 아닐 시
        except idp_client.exceptions.NotAuthorizedException as e:
            raise Exception('Not Sign in', e)

    # 비밀번호 변경
    def change_password(self, access_token, old_password, new_password):
        try:
            idp_client = boto3.client('cognito-idp', **self.default_config)
            response = idp_client.change_password(
                AccessToken=access_token,
                PreviousPassword=old_password,
                ProposedPassword=new_password,
            )

            return response

        # 현재 비밀번호가 일치하지 않음
        except idp_client.exceptions.NotAuthorizedException as e:
            raise Exception('Wrong Password', e)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except idp_client.exceptions.InvalidPasswordException as e:
            raise Exception('Invalid Password', e)

        # 비밀번호는 최소 6자리, 특수문자, 대문자, 소문자, 숫자를 포함해야 함
        except botocore.exceptions.ParamValidationError as e:
            raise Exception('Invalid Password', e)

        # 횟수 초과
        except idp_client.exceptions.LimitExceededException as e:
            raise Exception('Count over', e)

        # 유효하지 않은 ACCESSTOKEN 로그인 필요
        except idp_client.exceptions.InvalidParameterException as e:
            raise Exception('Invalid Token', e)

    # 비밀번호 잊어버림
    def forgot_password(self, username):
        client = boto3.client('cognito-idp', **self.default_config)
        response = client.forgot_password(
            ClientId=self.app_client_id,
            Username=username,
        )

        return response

    # 비밀번호 초기화
    def reset_password(self, username, new_password, confirmation_code):
        try:
            client = boto3.client('cognito-idp', **self.default_config)
            response = client.confirm_forgot_password(
                ClientId=self.app_client_id,
                Username=username,
                Password=new_password,
                ConfirmationCode=confirmation_code,
            )

            return response

        # 재시도 필요
        except botocore.exceptions.ParamValidationError as e:
            raise Exception('Retry', e)
        # 만료된 코드
        except client.exceptions.ExpiredCodeException as e:
            raise Exception('Expired Code', e)
        # 올바르지 않은 코드
        except client.exceptions.CodeMismatchException as e:
            raise Exception('Wrong Code', e)

    # 사용자 탈퇴
    def delete_user(self, access_token):
        try:
            client = boto3.client('cognito-idp', **self.default_config)
            response = client.delete_user(
                AccessToken=access_token
            )

            return response

        # ACCESS_TOKEN 필요 로그인 필요
        except Exception as e:
            raise e
