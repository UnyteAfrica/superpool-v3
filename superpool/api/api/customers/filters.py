from typing import Any
from django.db.models import QuerySet
from django.db.models import Q
from django_filters import rest_framework as filters
from core.user.models import Customer


class CustomerFilter(filters.Filter):
    """
    Defines set of filters that can be applied onto a customer query lookup
    """

    full_name = filters.CharFilter(lookup_expr="icontains")
    email = filters.CharFilter(lookup_expr="icontains")
    has_active_policies = filters.BooleanFilter(method="filter_active_policies")
    # has_pending_claims = filters.BooleanFilter(method="filter_pending_claims")

    class Meta:
        model = Customer
        fields = ["full_name", "email", "has_active_policies"]

    def filter_active_policies(self, qs: QuerySet, name: str, value: Any) -> QuerySet:
        """
        Filters customers by those with active policies
        """
        return qs.filter(policies__status="active")
