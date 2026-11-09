from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.exceptions import ValidationError


class DynamicPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 50


class DynamicCursorPagination(CursorPagination):
    page_size = 20
    page_size_query_param = "per_page"
    max_page_size = 50
    ordering = '-created_at'  # default
    ordering_fields = ['created_at']


    def get_ordering(self, request, queryset, view):
        param = request.query_params.get('ordering', self.ordering)
        field_name = param.lstrip('-')

        if field_name not in self.ordering_fields:
            raise ValidationError({
                "ordering": f"Invalid ordering. Allowed fields: {self.ordering_fields}. Use '-' for DESC, e.g. '-created_at'"
            })
        return (param,)

    def decode_cursor(self, request):
        # Only for invalid/tampered cursor token
        try:
            return super().decode_cursor(request)
        except Exception:
            raise ValidationError({"cursor": "Invalid or expired cursor token. Remove ?cursor= to start from first page."})


def build_pagination_dict(paginator):
    return {
        "next": paginator.get_next_link(),
        "previous": paginator.get_previous_link(),
        "has_next": paginator.get_next_link() is not None,
        "has_prev": paginator.get_previous_link() is not None
    }