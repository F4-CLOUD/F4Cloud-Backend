from datetime import datetime

from django.db import models


class Folder(models.Model):
    folder_id = models.BigAutoField(
        auto_created=True, primary_key=True, editable=False
    )
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)
    user = models.ForeignKey('Users', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = 'folders'

    def __str__(self):
        return self.name
