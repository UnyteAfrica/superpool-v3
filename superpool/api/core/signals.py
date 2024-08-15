from django.dispatch import receiver
from django.db.models.signals import post_save
from core.permissions import assign_user_to_group
from core.user.models import Admin, CustomerSupport
from core.merchants.models import Merchant
from django.db import transaction


@receiver(post_save, sender=Admin)
def assign_admin_group(sender, instance, created, **kwargs):
    """
    Assigns the user to the Admin group
    """
    if created:

        def commit():
            assign_user_to_group(instance.user, "Admin")

        transaction.on_commit(commit)


@receiver(post_save, sender=CustomerSupport)
def assign_support_group(sender, instance, created, **kwargs):
    """
    Assigns the user to the Customer Support group
    """
    if created:

        def commit():
            assign_user_to_group(instance.user, "CustomerSupport")

        transaction.on_commit(commit)


@receiver(post_save, sender=Merchant)
def assign_merchant_group(sender, instance, created, **kwargs):
    """
    Assign created user to the Merchant group
    """
    if created:

        def commit():
            assign_user_to_group(instance.user, "Merchant")

        transaction.on_commit(commit)
