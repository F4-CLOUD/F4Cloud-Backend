from django.db import models

from folders.models import Folder


class File(models.Model):
    file_id = models.BigAutoField(auto_created=True,
                                  primary_key=True, serialize=True, verbose_name='ID')
    folder_id = models.ForeignKey(
        'folders.Folder', related_name='file_location', on_delete=models.CASCADE, db_column='folder_id')
    s3_url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    size = models.IntegerField()

    class Meta:
        db_table = 'files'

    def __str__(self):
        return self.name
