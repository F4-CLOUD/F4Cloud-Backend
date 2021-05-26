from django.db import models


class User(models.Model):
    user_id = models.CharField(primary_key=True, max_length=255)
    collection_id = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
