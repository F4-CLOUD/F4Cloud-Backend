from django.urls import path

from .views import *


urlpatterns = [
    path('', FileCreate.as_view(), name='file_upload'),
    path('<int:file_id>', FileDetail.as_view(), name='file_detail'),
    path('<int:file_id>/move', FileMove.as_view(), name='file_move'),
    path('<int:file_id>/copy', FileCopy.as_view(), name='file_copy'),
    path('<int:file_id>/hashTag', FileHashTag.as_view(), name='file_hashtag'),
]
