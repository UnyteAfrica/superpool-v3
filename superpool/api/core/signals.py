from django.dispatch import receiver
from django.db.models.signals import post_save
from core.permissions import assign_user_to_group
from core.user.models import Admin, CustomerSupport
from core.merchants.models import Merchant


@receiver(post_save, sender=Admin)
def assign_admin_group(sender, instance, created, **kwargs):
    """
    Assigns the user to the Admin group
    """
    if created:
        assign_user_to_group(instance.user, "Admin")
        instance.save()


@receiver(post_save, sender=CustomerSupport)
def assign_support_group(sender, instance, created, **kwargs):
    """
    Assigns the user to the Customer Support group
    """
    if created:
        assign_user_to_group(instance.user, "CustomerSupport")
        instance.save()


@receiver(post_save, sender=Merchant)
def assign_merchant_group(sender, instance, created, **kwargs):
    """
    Assign created user to the Merchant group
    """
    if created:
        assign_user_to_group(instance.user, "Merchant")
        instance.save()
