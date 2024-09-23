from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter


class QSearchFilter(SearchFilter):
    search_param = "q"


class QuoteFilter(SearchFilter):
    """
    Filter class for filtering quotes by various criteria such as provider, coverage type,
    and sorting by cheapest or best coverage.
    """

    provider_name = filters.CharFilter(label="Insurer", lookup_expr="icontains")
    coverage_type = filters.CharFilter(
        method="filter_by_coverage_type", label="Coverage Type"
    )

    sort_by = filters.CharFilter(
        method="sort_by_cheapest_or_best_coverage",
        label="Sort by cheapest or best coverage limit",
    )
