from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class Operation:
    """
    Class to represent an operation
    """

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"<Operation: {self.name}>"


class Address(models.Model):
    """
    Class to represent an address
    """

    street = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    def __str__(self) -> str:
        return f"<Address: {self.street}, {self.city}, {self.state}, {self.country}>"
