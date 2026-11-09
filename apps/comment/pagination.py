from core.pagination import DynamicCursorPagination
from rest_framework.exceptions import ValidationError


class CommentCursorPagination(DynamicCursorPagination):
    ordering = "-date_created"
    page_size = 3
    max_page_size = 15

    ORDERING_MAP = {
    'likes_count': 'analytics__likes_count',
    'replies_count': 'analytics__replies_count',
    'date_created': 'date_created'
    }

    ordering_fields = ['date_created', 'likes_count', 'replies_count']

    def get_ordering(self, request, queryset, view):
        ordering_param = request.query_params.get('ordering', self.ordering)
        cursor = request.query_params.get('cursor')

        if ordering_param and cursor:
            raise ValidationError({
                "error":"Cannot change ordering while paginating. Drop cursor to change ordering"
            })
        field_name = ordering_param.lstrip('-')
       
        if field_name not in self.ordering_fields:
            raise ValidationError({
                "ordering": f"Invalid ordering. Allowed fields: {self.ordering_fields}. Use '-' for DESC, e.g. '-date_created'"
            })

        # Map likes_count -> analytics__likes_count for DB
        is_desc = ordering_param.startswith('-')
        db_field = self.ORDERING_MAP[field_name]
        final_ordering = f"-{db_field}" if is_desc else db_field
       
        return (final_ordering,)