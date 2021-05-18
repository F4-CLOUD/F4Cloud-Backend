from django.urls import path

from .views import *


urlpatterns = [
    path('', FolderCreate.as_view(), name='folder_create'),
    path('<int:folder_id>', FolderDetail.as_view(), name='folder_detail'),
    path('<int:folder_id>/list', FolderElements.as_view(), name='folder_elements'),
    path('<int:folder_id>/move', FolderMove.as_view(), name='folder_move'),
]
