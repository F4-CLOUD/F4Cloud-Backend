from django.urls import path

from .views import *


urlpatterns = [
    path('', Trash.as_view(), name='trash'),
]
