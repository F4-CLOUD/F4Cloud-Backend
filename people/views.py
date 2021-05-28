from datetime import datetime
from io import BytesIO
import io

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from rest_framework import status
import boto3
from PIL import Image
import requests

from .models import *
from .serializers import *
from files.models import File
from users.models import User
from files.serializers import FileGroupSerializer
from utils.cognito import is_token_valid
from f4cloud.settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, DEFAULT_REGION_NAME


def get_object_faceinfo(**kwargs):
    file = get_object_or_404(FaceInfo, **kwargs)
    return file


def get_object_group(**kwargs):
    file = get_object_or_404(GroupInfo, **kwargs)
    return file


class collections(APIView):
    def post(self, request):
        if request.method == 'POST':
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                data = request.data
                user_id = data['user_id']
                client = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=DEFAULT_REGION_NAME)
                collection_id = User.objects.values(
                    'collection_id').distinct().filter(user_id=user_id)
                collection_id = collection_id[0]['collection_id']
                print('Creating collection:' + collection_id)
                response = client.create_collection(CollectionId=collection_id)
                print('Collection ARN: ' + response['CollectionArn'])
                print('Status code: ' + str(response['StatusCode']))
                print('Done...')
                msg = {'msg': ' Create collection '+str(collection_id)}
                return Response(msg, status=status.HTTP_200_OK)
            except Exception as e:
                msg = {'msg': str(e)}
                print(msg)
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if request.method == "DELETE":
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                data = request.data
                user_id = data['userId']
                client = boto3.client('rekognition')
                collection_id = User.objects.values(
                    'collection_id').distinct().filter(user_id=user_id)
                collection_id = collection_id[0]['collection_id']
                print('Attempting to delete collection ' + collection_id)
                status_code = 0
                response = client.delete_collection(CollectionId=collection_id)
                status_code = response['StatusCode']
                FaceInfo.objects.filter(user_id='user_test').delete()
                GroupInfo.objects.filter(user_id='user_test').delete()
                msg = {'msg': ' Delete collection ' + str(collection_id)}
                return Response(msg, status=status.HTTP_200_OK)
            except Exception as e:
                msg = {'msg': str(e)}
                print(msg)
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class faces(APIView):
    def post(self, request):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            data = request.data
            print(data)
            file_id = data['file_id']
            user_id = data['user_id']
            client = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=DEFAULT_REGION_NAME)

            print(file_id, user_id)

            # get file address using file id
            file_address = File.objects.values(
                's3_url').distinct().filter(file_id=file_id, user_id=user_id)
            file_address = file_address[0]['s3_url']

            # Check if it is an image file
            im = requests.get(file_address)
            im = Image.open(BytesIO(im.content))

            # filename not an image file
            # file_address format : object URL
            proc = file_address[8:]
            bucket = proc[:proc.find('.')]
            file_path = proc[proc.find('/') + 1:]

            print(bucket, file_path)
            if file_path.find('/') != -1:
                file_name = file_path
                while (file_name.find('/') != -1):
                    file_name = file_name[file_name.find('/') + 1:]
            else:
                file_name = file_path

            if file_name.find('/') != -1:
                file_name = file_name[file_name.find('/') + 1:]

            # get collection id using user id
            collection_id = User.objects.values(
                'collection_id').distinct().filter(user_id=user_id)
            collection_id = collection_id[0]['collection_id']

            # set max number of face to add
            add_max_faces = 3
            # add faces to collection
            response = client.index_faces(CollectionId=collection_id,
                                          Image={'S3Object': {
                                              'Bucket': bucket, 'Name': file_path}},
                                          ExternalImageId='FIX',  # For Korean
                                          MaxFaces=add_max_faces,
                                          QualityFilter="AUTO",
                                          DetectionAttributes=['ALL'])
            print('Complete Add Face')
            # process result
            face_records = response['FaceRecords']
            unindex_faces = response['UnindexedFaces']

            if (len(face_records) == 0):
                # case1 : There is no person in this image
                print('No Person in Photo')
                msg = {'msg': 'No Person in Photo'}
            else:
                print('Faces indexed:')
                for faceRecord in face_records:
                    # case2 : There is people in this image

                    print('  Face ID: ' + faceRecord['Face']['FaceId'])
                    print('  Location: {}'.format(
                        faceRecord['Face']['BoundingBox']))

                    # Check if there is already the same person

                    # Set threshold for similarity
                    threshold = 95

                    # Set max result number to find in a collection
                    max_faces = 1
                    client = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=DEFAULT_REGION_NAME)

                    face_id = faceRecord['Face']['FaceId']
                    location = faceRecord['Face']['BoundingBox']
                    response = client.search_faces(CollectionId=collection_id,
                                                   FaceId=face_id,
                                                   FaceMatchThreshold=threshold,
                                                   MaxFaces=max_faces)

                    face_matches = response['FaceMatches']

                    # Even if input face id is in the collection, results do not include input face id
                    group_id = FaceInfo.objects.values(
                        'group_id').distinct().filter(face_id=face_id)
                    if(len(group_id) != 0):
                        # case 1 : There is the same face id
                        group_id = group_id[0]['group_id']
                        print()
                        print('group_id : ', group_id)
                        print()
                        face_serializers = FaceInfoSerializer(data={
                            'user_id': user_id,
                            'face_id': face_id,
                            'group_id': group_id,
                            'file_id': file_id,
                        })
                        if face_serializers.is_valid():
                            face_serializers.save()
                        else:
                            print(' DB에 저장 안됨')
                            print(face_serializers.errors)

                        msg = {'msg': 'Add to group '+str(group_id)}
                    elif (len(face_matches) == 0):
                        # case2-1 : There is no same person in collection
                        print('New Person')
                        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                                 aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=DEFAULT_REGION_NAME)

                        # group info bucket
                        group_bucket = 'f4cloud-facegroup'

                        # set initial name of new group
                        timestamp = datetime.now().strftime('%y%m%d%H%M%S%f')
                        group_name_prefix = user_id
                        new_group_id = group_name_prefix + timestamp

                        print(file_address)
                        img_response = requests.get(file_address)
                        img = Image.open(BytesIO(img_response.content))
                        width, height = img.size
                        left = width * location['Left']
                        top = height * location['Top']
                        crop_loc = (
                            left, top, left + (width * location['Width']), top + (height * location['Height']))
                        crop_img = img.crop(crop_loc)
                        crop_img = crop_img.convert("RGB")
                        # crop_img.show()
                        # save crop image
                        rep_img = io.BytesIO()
                        img_format = "JPEG"
                        crop_img.save(rep_img, img_format)
                        rep_img.seek(0)

                        url_gen = new_group_id + file_id + '.' + img_format

                        s3_prefix = 'https://'+group_bucket+'.s3.amazonaws.com/'
                        s3_client.upload_fileobj(
                            rep_img,
                            group_bucket,
                            url_gen,
                            ExtraArgs={
                                "ContentType": 'image/jpeg'
                            }
                        )
                        rep_faceaddress = s3_prefix + url_gen
                        rep_fileid = file_id
                        rep_faceid = face_id

                        print()
                        print('group_id : ', new_group_id)
                        print()
                        group_serializers = GroupListSerializer(data={
                            'group_id': new_group_id,
                            'user_id': user_id,
                            'rep_faceid': rep_faceid,
                            'rep_faceaddress': rep_faceaddress,
                            'rep_fileid': rep_fileid,
                        })
                        if group_serializers.is_valid():
                            group_serializers.save()
                        else:
                            print(' DB에 저장 안됨')
                            print(group_serializers.errors)

                        face_serializers = FaceInfoSerializer(data={
                            'user_id': user_id,
                            'face_id': face_id,
                            'group_id': new_group_id,
                            'file_id': file_id,
                        })
                        if face_serializers.is_valid():
                            face_serializers.save()
                        else:
                            print(' DB에 저장 안됨')
                            print(face_serializers.errors)

                        msg = {'msg': 'Create new group'}
                    else:
                        # case2-2 : There is same person in collection
                        print('add into existing group')
                        for match in face_matches:
                            print('FaceId:' + match['Face']['FaceId'])
                            print('Similarity: ' +
                                  "{:.2f}".format(match['Similarity']) + "%")
                            match_face_id = match['Face']['FaceId']

                            get_group_id = GroupInfo.objects.values('group_id').distinct().filter(
                                rep_faceid=match_face_id, user_id=user_id)
                            print(get_group_id)
                            group_id = get_group_id[0]['group_id']
                            print()
                            print('group_id : ', group_id)
                            print()
                            face_serializers = FaceInfoSerializer(data={
                                'user_id': user_id,
                                'face_id': face_id,
                                'group_id': group_id,
                                'file_id': file_id,
                            })
                            if face_serializers.is_valid():
                                face_serializers.save()
                            else:
                                print(' DB에 저장 안됨')
                                print(face_serializers.errors)

                        del_faces = list()
                        del_faces.append(face_id)
                        print(del_faces)
                        print('face_id:' + face_id)
                        response = client.delete_faces(CollectionId=collection_id,
                                                       FaceIds=del_faces)
                        print(
                            str(len(response['DeletedFaces'])) + ' faces deleted:')

                        msg = {'msg': 'Add to group ' + str(group_id)}

            '''if (len(unindex_faces) != 0):
                print('Faces not indexed:')
                for unindexedFace in unindex_faces:
                    print(' Location: {}'.format(unindexedFace['FaceDetail']['BoundingBox']))
                    print(' Reasons:')
                    for reason in unindexedFace['Reasons']:
                        print('   ' + reason)'''
            ''' except IOError as e:
            print(e)
            return Response({'msg':'Not Image File'})
        except IndexError as e:
            print(e)
            return Response({'msg':'parameter error'})'''
        except Exception as e:
            msg = {'msg': str(e)}
            print(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        return Response(msg, status=status.HTTP_200_OK)

    def delete(self, request):
        # Permission 확인
        if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            data = request.data
            file_id = data['file_id']
            user_id = data['user_id']
            client = boto3.client('rekognition', aws_access_key_id=AWS_ACCESS_KEY_ID,
                                  aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=DEFAULT_REGION_NAME)
            collection_id = User.objects.values(
                'collection_id').distinct().filter(user_id=user_id)
            collection_id = collection_id[0]['collection_id']
            #print('Creating collection:' + collection_id)
            faces = FaceInfo.objects.values('face_id').distinct().filter(
                user_id=user_id, file_id=file_id)
            #print('faces : ' + str(faces))
            if len(faces) == 0:
                msg = {'msg': 'There is no face id about this file '}
                return Response(msg, status=status.HTTP_200_OK)
            for faceId in faces:
                face_id = faceId['face_id']
                # check if this face id is rep_face id
                group_id = FaceInfo.objects.values('group_id').distinct().filter(
                    user_id=user_id, face_id=face_id)
                group_id = group_id[0]['group_id']
                print(group_id)

                check = GroupInfo.objects.filter(
                    user_id=user_id, group_id=group_id)
                item = FaceInfo.objects.filter(
                    user_id=user_id, file_id=file_id, face_id=face_id)
                item.delete()
                other_mem = FaceInfo.objects.values(
                    'file_id').distinct().filter(group_id=group_id)
                if len(other_mem) == 0:
                    # There is no member
                    del_faces = []
                    del_faces.append(face_id)
                    response = client.delete_faces(CollectionId=collection_id,
                                                   FaceIds=del_faces)
                    item = FaceInfo.objects.filter(
                        user_id=user_id, file_id=file_id, face_id=face_id)
                    item.delete()
                    check.delete()
                    print(
                        str(len(response['DeletedFaces'])) + ' faces deleted:')
                    for faceId in response['DeletedFaces']:
                        print(faceId)
                else:
                    '''new_rep_fileid = new_rep_fileid[0]['file_id']
                    new_rep_fileaddress = FileInfo.objects.values('file_address').distict().filter(file_id=file_id)
                    new_rep_fileaddress= new_rep_fileaddress[0]['file_address']'''
                    del_faces = []
                    del_faces.append(face_id)
                    response = client.delete_faces(CollectionId=collection_id,
                                                   FaceIds=del_faces)
                    item = FaceInfo.objects.filter(
                        user_id=user_id, file_id=file_id, face_id=face_id)
                    item.delete()
                    print(
                        str(len(response['DeletedFaces'])) + ' faces deleted:')
                    for faceId in response['DeletedFaces']:
                        print(faceId)

            return Response({'msg': 'complete'}, status=status.HTTP_200_OK)
        except Exception as e:
            msg = {'msg': str(e)}
            # print(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class groups(APIView):
    def get(self, request):
        if request.method == 'GET':
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                user_id = request.GET['user_id']
                res = GroupInfo.objects.filter(user_id=user_id)
                serializer = GroupListSerializer(res, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                msg = {'msg':  str(e)}
                print(e)
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        if request.method == 'PUT':
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                data = request.data
                group_id = data['group_id']
                user_id = data['user_id']
                display_name = data['display_name']
                item = GroupInfo.objects.filter(
                    user_id=user_id, group_id=group_id)
                item.update(display_name=display_name)
                return Response({'msg': 'complete'}, status=status.HTTP_200_OK)
            except Exception as e:
                msg = {'msg': str(e)}
                print(e)
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class group_detail(APIView):
    def get(self, request):
        if request.method == 'GET':
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            try:
                user_id = request.GET['user_id']
                group_id = request.GET['group_id']
                files = FaceInfo.objects.values('file_id').distinct().filter(
                    group_id=group_id, user_id=user_id)
                print(files)
                res = []
                for file in files:
                    file_id = file['file_id']
                    item = File.objects.filter(
                        file_id=file_id, user_id=user_id)
                    res.append(item[0])
                print(res)
                serializer = FileGroupSerializer(res, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:
                msg = {'msg': str(e)}
                print(e)
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)
