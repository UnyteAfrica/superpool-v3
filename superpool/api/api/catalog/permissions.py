from rest_framework import permissions


class AdminOnlyInsurerFilterPermission(permissions.BasePermission):
    """
    Custom permission to restrict access to 'insurer_name' and 'insurer_id' filters to admin users only.
    """

    def has_permissions(self, request, view) -> bool:
        # set the query params

        query_params = request.query_params
        insurer_name = query_params.get("insurer_name")
        insurer_id = query_params.get("insurer_id")

        if insurer_name and insurer_id:
            # confirm if the user is an admin or a customer support
            return request.user and request.user.is_staff
        # other-wise any other filters? No problem give every one access
        return True
