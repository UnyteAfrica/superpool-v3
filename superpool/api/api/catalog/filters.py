from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter

from core.catalog.models import Quote


class QSearchFilter(SearchFilter):
    search_param = "q"


class QuoteFilter(SearchFilter):
    """
    Filter class for filtering quotes by various criteria such as provider, coverage type,
    and sorting by cheapest or best coverage.
    """

    provider_name = filters.CharFilter(
        label="Provider Name",
        lookup_expr="icontains",
        field_name="product__provider__name",
    )
    coverage_type = filters.CharFilter(
        method="filter_by_coverage_type", label="Coverage Type"
    )
    # sort_by = filters.CharFilter(
    #     method="sort_by_cheapest_or_best_coverage",
    #     label="Sort by cheapest or best coverage limit",
    # )
    # we want to filter by prices greater than min_price and lesser than our max_price
    min_price = filters.NumberFilter(field_name="premium__amount", lookup_expr="gte")
    max_price = filters.NumberFilter(field_name="premium__amount", lookup_expr="lte")

    class Meta:
        model = Quote
        fields = ["provider_name", "coverage_type", "min_price", "max_price"]

    def filter_by_coverage_type(self, queryset, name, value):
        return queryset.filter(
            additional_metadata__coverage_details__coverage_type__icontains=value
        )
