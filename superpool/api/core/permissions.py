from rest_framework.permissions import BasePermission


class IsCustomerSupport(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.groups.filter(name="Customer Support").exists()
        )


class IsMerchant(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name="Merchant").exists()


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.groups.filter(name="Admin").exists()
