from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()


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
def create_permissions():
    permissions = [
        ("view_dashboard", "Can view dashboard"),
        ("manage_users", "Can manage users"),
        ("manage_merchants", "Can manage merchants"),
        ("view_customers", "Can view customers"),
        ("manage_customers", "Can manage customers"),
        ("manage_policies", "Can manage policies"),
        ("manage_claims", "Can manage claims"),
        ("manage_tickets", "Can manage support tickets"),
        (
            "create_quote",
            "Can create a quote",
        ),  # allows us to be able to create a quote on the admin dashboard
    ]

    content_type = ContentType.objects.get_for_model(User)
    for codename, description in permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=description,
            content_type=content_type,
        )


def assign_user_to_group(user, group_name: str):
    # create a group if it does not exist and assign the user to the group
    group, created = Group.objects.get_or_create(name=group_name)
    if user:
        user.groups.add(group)
        user.save()


def assign_permissions_to_groups():
    permissions = {
        "Admin": [
            "view_dashboard",
            "manage_users",
            "manage_merchants",
            "view_customers",
            "view_tickets",
            "manage_claims",
            "create_quote",
        ],
        "Merchant": [
            "view_dashboard",
            "manage_customers",
            "create_quote",
            "manage_policies",
            "manage_claims",
            "manage_policies",
        ],
        "CustomerSupport": [
            "view_dashboard",
            "manage_tickets",
            "manage_merchants",
            "manage_customers",
            "manage_claims",
        ],
    }
    # assign the predefined permissions to the groups

    for group_name, perm_codenames in permissions.items():
        group, created = Group.objects.get_or_create(name=group_name)

        #  Assign permissions to groups
        for codename in perm_codenames:
            # check if the permission exists
            permission_qs = Permission.objects.filter(codename=codename)
            if permission_qs.exists():
                permission = permission_qs.first()
                group.permissions.add(Permission.objects.get(codename=permission))
            else:
                print(f"Permission {codename} does not exist")


# Invoke the functions to create permissions and assign them to groups
create_permissions()
assign_permissions_to_groups()
