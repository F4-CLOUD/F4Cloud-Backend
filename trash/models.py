from django.db import models


class TrashFolder(models.Model):
    folder_id = models.ForeignKey(
        'folders.Folder', on_delete=models.CASCADE, db_column='folder_id')
    trashed_at = models.DateTimeField()
    expired_at = models.DateTimeField()

    class Meta:
        db_table = 'trash_folder'

    def __str__(self):
        return self.name


class TrashFile(models.Model):
    file_id = models.ForeignKey(
        'files.File', on_delete=models.CASCADE, db_column='file_id')
    trashed_at = models.DateTimeField()
    expired_at = models.DateTimeField()

    class Meta:
        db_table = 'trash_file'

    def __str__(self):
        return self.name
