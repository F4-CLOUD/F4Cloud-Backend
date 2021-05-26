# -*- coding: utf-8 -*-
import configparser

import boto3

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
        idp_client = boto3.client('cognito-idp', **self.default_config)
        resp = idp_client.sign_up(
            ClientId=self.app_client_id,
            Username=username,
            Password=password,
            UserAttributes=UserAttributes)
        return resp

    def confirm_sign_up(self, username, confirm_code):

        idp_client = boto3.client('cognito-idp')

        resp = idp_client.confirm_sign_up(ClientId=self.app_client_id,

                                          Username=username,

                                          ConfirmationCode=confirm_code)

        return resp

    def sign_in_admin(self, username, password):

        # Get ID Token

        idp_client = boto3.client('cognito-idp')

        resp = idp_client.admin_initiate_auth(UserPoolId=self.user_pool_id,

                                              ClientId=self.app_client_id,

                                              AuthFlow='ADMIN_NO_SRP_AUTH',

                                              AuthParameters={'USERNAME': username, 'PASSWORD': password})

        provider = 'cognito-idp.%s.amazonaws.com/%s' % (
            self.region, self.user_pool_id)

        token = resp['AuthenticationResult']['IdToken']

        # Get IdentityId

        ci_client = boto3.client('cognito-identity')

        resp = ci_client.get_id(AccountId=self.account_id,

                                IdentityPoolId=self.identity_pool_id,

                                Logins={provider: token})

        # Get Credentials

        resp = ci_client.get_credentials_for_identity(IdentityId=resp['IdentityId'],

                                                      Logins={provider: token})

        return resp
