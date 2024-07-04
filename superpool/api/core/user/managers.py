from django.contrib.auth.models import BaseUserManager
from django.db.models import Q, QuerySet


class UserQuerySet(QuerySet):
    def active(self):
        return self.filter(Q(is_active=True) & Q(has_completed_verification=True))

    def inactive(self):
        return self.filter(Q(is_active=False) | Q(has_completed_verification=False))


class UserManager(BaseUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)

        user.has_completed_verification = False
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)
