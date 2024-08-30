from django.db import models
from django.utils import timezone


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


class TrashableModelMixin(models.Model):
    """
    Mixin class to add trashable functionality to models.

    Technically, we are not deleting the model instance, we are just marking it as trashed
    which could in turn be restored (let's say, an insurance provider temporarily stops offering a package, they can restore it later on, maybe due to regulations, mandates or downtimes)

    Attributes:

        is_trashed: BooleanField
        trashed_at: DateTimeField
        restored_at: DateTimeField
        trash: Method
    """

    is_trashed: models.BooleanField = models.BooleanField(default=False)
    trashed_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)
    restored_at: models.DateTimeField = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def trash(self) -> None:
        """
        Trash the model instance
        """
        self.is_trashed = True
        self.trashed_at = timezone.now()
        self.save()

    def restore(self) -> None:
        """
        Restore the model instance
        """
        self.is_trashed = False
        self.restored_at = timezone.now()
        self.save()

    def delete(self, *args: dict, **kwargs: dict) -> None:
        """
        Overrides the delete method to trash the model instance instead of deleting it
        """
        self.trash()
