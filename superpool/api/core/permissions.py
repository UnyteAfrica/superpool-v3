from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class IsCustomerSupport(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and request.user.groups.filter(name="CustomerSupport").exists()
        )


class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name="Merchant").exists()


# Admin user can have multiple groups
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name="Admin").exists()


# define permissions types, permission groups, and assign permissions to groups
permissions = [
    # Permissions for Customer Support
    ("manage_merchants", "Can manage merchants"),
    ("view_customer", "Can view customer"),
    # Permissions for Merchant
    ("manage_customers", "Can manage customers"),
    ("manage_policies", "Can manage policies"),
    ("manage_claims", "Can manage claims"),
]

# Create the actual permissions
for codename, name in permissions:
    content_type = ContentType.objects.get_for_model(Group)
    permission = Permission.objects.get_or_create(
        codename=codename, name=name, content_type=content_type
    )

admin_permissions = [
    "view_dashboard",
    "manage_users",
    "manage_merchants",
    "manage_customers",
    "manage_policies",
    "manage_claims",
]
support_permissions = ["view_dashboard", "view_customers", "manage_merchants"]
merchant_permissions = [
    "view_customers",
    "manage_customers",
    "manage_policies",
    "manage_claims",
]

admin_group, created = Group.objects.get_or_create(name="Admin")
support_group, created = Group.objects.get_or_create(name="CustomerSupport")
merchant_group, created = Group.objects.get_or_create(name="Merchant")


# Assign permissions to groups
for permission in admin_permissions:
    admin_group.permissions.add(Permission.objects.get(codename=permission))

for permission in support_permissions:
    support_group.permissions.add(Permission.objects.get(codename=permission))

for permission in merchant_permissions:
    merchant_group.permissions.add(Permission.objects.get(codename=permission))
