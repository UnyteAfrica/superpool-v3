from django.contrib import admin
from django.db.models.query import QuerySet
from rest_framework.request import Request

from .models import Merchant


@admin.register(Merchant)
class MerchantModelAdmin(admin.ModelAdmin):
    """
    Admin model for Merchant model
    """

    list_display = ("name", "support_email", "is_active", "created_at", "updated_at")
    search_fields = ("name", "short_code")
    list_filter = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Merchant Details",
            {
                "fields": (
                    "name",
                    "short_code",
                    "support_email",
                    "is_active",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def deactivate_merchant(self, request: Request, queryset: QuerySet):
        """
        Deactivate selected merchants
        """
        queryset.update(is_active=False)
