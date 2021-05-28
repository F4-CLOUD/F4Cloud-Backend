from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import *

urlpatterns = [
    path('keyword/', SearchKeyword.as_view()),
    path('hashtag/', SearchHashtag.as_view()),
    path('people/', SearchGroup.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
