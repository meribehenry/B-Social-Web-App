from rest_framework.pagination import PageNumberPagination


class DynamicPageNumberPagination(PageNumberPagination):
    per_page = 20
    page_size_query_param = "per_page"
    max_page_size = "100"