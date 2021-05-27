from botocore import serialize
from django.db import models


class Folder(models.Model):
    folder_id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=True
    )
    parent_id = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, db_column='parent_id')
    user_id = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, db_column='user_id')
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = 'folders'

    def __str__(self):
        return self.name
