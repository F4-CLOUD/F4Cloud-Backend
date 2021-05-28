from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from files.models import File
from files.serializers import FileSerializer
from people.models import *
from utils.cognito import is_token_valid


class SearchKeyword(APIView):
    def get(self, request, format=None):
        try:
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            keyword = request.GET['keyword']
            userId = request.GET['userId']
            res = File.objects.filter(
                name__contains=keyword, user_id=userId
            )
            serializer = FileSerializer(res, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            msg = {'error': str(e)}
            # print(e)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class SearchHashtag(APIView):
    def get(self, request):
        try:
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            user_id = request.GET['userId']
            keyword = request.GET['keyword']
            res = File.objects.filter(
                hash_tag__contains=keyword, user_id=user_id)

            serializer = FileSerializer(res, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            msg = {'msg': str(e)}
            print(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class SearchGroup(APIView):
    def get(self, request):
        try:
            # Permission 확인
            if not is_token_valid(token=request.headers['ID-Token'], user_id=request.data['user_id']):
                return Response(status=status.HTTP_403_FORBIDDEN)

            res = []
            user_id = request.GET['userId']
            group_name = request.GET['groupName']
            groups = GroupInfo.objects.values('group_id').distinct().filter(
                display_name__contains=group_name, user_id=user_id)
            for group_id in groups:
                group_id = group_id['group_id']
                files = FaceInfo.objects.values('file_id').distinct().filter(
                    group_id=group_id, user_id=user_id)

                for file in files:
                    file_id = file['file_id']
                    item = File.objects.get(file_id=file_id, user_id=user_id)
                    res.append(item)
            serializer = FileSerializer(res, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            msg = {'msg': str(e)}
            print(e)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
