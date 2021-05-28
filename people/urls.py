from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *

urlpatterns = [
    path('collections/', collections.as_view()),
    path('faces/', faces.as_view()),
    path('face_groups/', groups.as_view()),
    path('group_detail/', group_detail.as_view()),
    path('search/', search_group.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
