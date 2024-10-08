from typing import Any

from django.db.models import Q, QuerySet
from django_filters import rest_framework as filters

from core.catalog.models import Policy
from core.user.models import Customer


class CustomerFilter(filters.FilterSet):
    """
    Defines set of filters that can be applied onto a customer query lookup
    """

    first_name = filters.CharFilter(lookup_expr="iexact")
    last_name = filters.CharFilter(lookup_expr="iexact")
    email = filters.CharFilter(lookup_expr="icontains")
    has_active_policies = filters.BooleanFilter(method="filter_active_policies")
    has_pending_claims = filters.BooleanFilter(method="filter_pending_claims")
    has_active_claims = filters.BooleanFilter(method="filter_active_claims")

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "email", "has_active_policies"]

    def filter_active_policies(self, qs: QuerySet, name: str, value: Any) -> QuerySet:
        """
        Filters customers by those with active policies
        """
        return qs.filter(policies__status=Policy.ACTIVE).distinct()

    def filter_active_claims(self, qs: QuerySet, name: str, value: Any) -> QuerySet:
        """
        Filter customers by those with active claims, that is:

        anything that is not 'paid', 'denied', or 'pending' and the there they have at least ONE claim
        """
        inactive_statuses = ["paid", "denied", "pending"]
        active_claims_filter = ~Q(claims__status__in=inactive_statuses)
        return qs.exclude(active_claims_filter).distinct()

    def filter_pending_claims(self, qs: QuerySet, name: str, value: Any) -> QuerySet:
        """
        Filter for customers with pending claims
        """
        return qs.filter(claims__status="pending").distinct()
