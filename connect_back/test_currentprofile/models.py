from common.current_profile.db.models import CurrentProfileField
from django.db import models


class TestModel(models.Model):
    author = CurrentProfileField(verbose_name='Author', editable=False)
    text = models.CharField(null=False, default='', verbose_name='Some text', max_length=31)

    class Meta:
        verbose_name = 'Test current profile'
