from django.db import models


class TimestampMixin(models.Model):
    """
    Mixin class to add timestamp to models

    Attributes:
    created_at: DateTimeField
    updated_at: DateTimeField
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
