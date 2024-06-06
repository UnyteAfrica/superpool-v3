from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class Operation:
    """
    Class to represent an operation
    """

    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self) -> str:
        return f"<Operation: {self.name}>"
