from datetime import datetime

from django.db import models


class Folder(models.Model):
    folder_id = models.BigAutoField(auto_created=True,
                                    primary_key=True, serialize=False, verbose_name='ID', editable=False)
    parent_id = models.ForeignKey(
        'Folder', related_name='parent_folder', on_delete=models.CASCADE, db_column='parent_id', null=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        db_table = 'folders'

    def __str__(self):
        return self.name
