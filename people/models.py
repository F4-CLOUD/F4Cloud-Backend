from django.db import models


class FaceInfo(models.Model):
    id = models.BigAutoField(
        auto_created=True, primary_key=True, serialize=True, verbose_name='ID')
    user_id = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, db_column='user_id')
    file_id = models.CharField(max_length=255)
    file_id = models.ForeignKey(
        'files.File', on_delete=models.CASCADE, db_column='file_id')
    group_id = models.CharField(max_length=255, blank=True, null=True)
    group_id = models.ForeignKey(
        'GroupInfo', on_delete=models.CASCADE, db_column='group_id')
    face_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'face_info'


class GroupInfo(models.Model):
    group_id = models.CharField(primary_key=True, max_length=255)
    user_id = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, db_column='user_id')
    rep_faceid = models.CharField(max_length=255)
    rep_faceaddress = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, blank=True, null=True)
    rep_fileid = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'group_info'
