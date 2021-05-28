import sys

import boto3

from f4cloud.settings import DEFAULT_REGION_NAME, S3_BUCKET_ID


# S3 Client 생성
def get_s3_client(access_key_id, secret_access_key, session_token=None):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        aws_session_token=session_token,
        region_name=DEFAULT_REGION_NAME
    )
    return s3_client


# S3 URL 생성
def get_s3_url(path):
    return 'https://{0}.s3.amazonaws.com/{1}'.format(
        S3_BUCKET_ID,
        path
    )


# ----------------------------
# 폴더 관련 모듈
# ----------------------------
# 폴더 생성
def upload_folder(s3_client, folder):
    try:
        response = s3_client.put_object(
            Bucket=S3_BUCKET_ID,
            Key=folder,
            ACL='public-read'
        )
        return response
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Upload Folder Fail', e)


# 폴더 삭제
def delete_folder(s3_client, target):
    try:
        response = s3_client.delete_object(Bucket=S3_BUCKET_ID, Key=target)
        return response
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Delete folder Fail', e)


# 폴더 이름 변경 혹은 이동
def rename_move_folder(s3_client, target, new_key):
    try:
        s3_client.copy_object(Bucket=S3_BUCKET_ID, Key=new_key, CopySource={
            'Bucket': S3_BUCKET_ID, 'Key': target
        }, ACL='public-read')

        # 내부 컨텐츠 이동
        contents = s3_client.list_objects(
            Bucket=S3_BUCKET_ID, Prefix=target, Delimiter="/")
        for content in contents['CommonPrefixes']:
            old_path = content['Prefix']
            new_path = new_key + old_path.replace(contents['Prefix'], '')
            s3_client.copy_object(Bucket=S3_BUCKET_ID, Key=new_path, CopySource={
                'Bucket': S3_BUCKET_ID, 'Key': old_path
            }, ACL='public-read')
            s3_client.delete_object(Bucket=S3_BUCKET_ID, Key=old_path)

        s3_client.delete_object(Bucket=S3_BUCKET_ID, Key=target)
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Rename or Move Folder Fail', e)


# ----------------------------
# 파일 관련 모듈
# ----------------------------
# 파일 업로드
def upload_file(s3_client, file, file_name):
    try:
        response = s3_client.put_object(
            Bucket=S3_BUCKET_ID,
            Key=file_name,
            Body=file,
            ACL='public-read'
        )
        return response
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Upload file Fail', e)


# 파일 삭제
def delete_file(s3_client, file_name):
    try:
        response = s3_client.delete_object(Bucket=S3_BUCKET_ID, Key=file_name)
        return response
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Delete file Fail', e)


# 파일 이름 변경 혹은 이동
def rename_move_file(s3_client, file_name, new_name):
    try:
        s3_client.copy_object(Bucket=S3_BUCKET_ID, Key=new_name, CopySource={
            'Bucket': S3_BUCKET_ID, 'Key': file_name
        }, ACL='public-read')
        s3_client.delete_object(Bucket=S3_BUCKET_ID, Key=file_name)
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Rename Fail', e)


# 파일 복사
def copy_file(s3_client, file_name, new_name):
    try:
        s3_client.copy_object(Bucket=S3_BUCKET_ID, Key=new_name, CopySource={
            'Bucket': S3_BUCKET_ID, 'Key': file_name
        }, ACL='public-read')
    except Exception as e:
        print('Error on line {}'.format(
            sys.exc_info()[-1].tb_lineno), type(e).__name__, e
        )
        raise Exception('Copy Fail', e)
