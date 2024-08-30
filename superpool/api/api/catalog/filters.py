from rest_framework.filters import SearchFilter


class QSearchFilter(SearchFilter):
    search_param = "q"
